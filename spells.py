#!/usr/bin/python

import math
import os
import subprocess
import tempfile
from fdfgen import forge_fdf
import tools

CLERIC_SPELLS = [
    'Bless', 'Command', 'Cure Light Wounds', 'Detect Evil',
    'Invisibility to Undead', 'Protection from Evil',
    'Purify Food & Drink', 'Remove Fear', 'Sanctuary', 'Turn Undead']

MU_SPELL_SLOTS = [1, 2,2,2, 3,3,3, 4,4,4, 5,5,5, 6,6,6, 7,7,7, 8]
CLERIC_SPELL_SLOTS = [1, 2, 3,3,3,3, 4,4,4,4, 5,5,5,5, 6,6,6,6, 7, 8]

MU_SPELL_NOTES = "You must add random spells as follows:\n\n"
CLERIC_SPELL_NOTES = "You have access to all Cleric spells of level {} or lower."

FILLABLE_SPELL_SHEET = os.path.join(
    os.path.dirname(__file__),
    'LotFPSpellSheetFillable.pdf')

SPELL_FIELDS = [
    'Spell', 'Duration', 'Range', 'Save',
    'Reversible', 'Effect', 'Flavor', 'Page']


def add_class_based_spells(spell_list, pc_class, level):
    """Add class-specific spells to the spell list."""
    if pc_class == 'Magic-User':
        spell_list.append('Summon')
    if pc_class == 'Cleric':
        spell_list = CLERIC_SPELLS if level < 2 else []
    if pc_class == 'Elf':
        spell_list = ['Read Magic']
    return spell_list


def create_spell_list(original_spell_list, pcClass, level):
    """Create a full list of spells, including class-specific spells."""
    spell_list = add_class_based_spells(original_spell_list, pcClass, level)

    # Correct for spelling error in Magic Missile
    if 'Magic Missle' in spell_list:
        spell_list.remove('Magic Missle')
        spell_list.append('Magic Missile')
    return spell_list


def get_spell_slots(pcClass, level):
    """Return a list containing the available spell slots for each spell level."""
    spell_slots = []

    if pcClass.casefold() == "Magic-User".casefold():
        highest_spell_level = min(math.ceil(level / 2), 9)
        # MU_SPELL_SLOTS[level - 1] gives first level spell slots for the given character
        # level. The spell slots for subsequent spell levels move two steps down the
        # list each time. So we move two steps down the list for each spell level we
        # need beyond the first by subtracting 2 * i from the index.
        for i in range(highest_spell_level):
            spell_slots.append(MU_SPELL_SLOTS[(level - 1) - (2 * i)])

    if pcClass.casefold() == "Cleric".casefold():
        # Cleric spell slots are a little strange: they have access to level 1 spells
        # if they're 3rd level or lower. Otherwise, they use the same progression as
        # magic-users (except that Clerics' highest spell level is 7, not 9).
        highest_spell_level = 1 if level <= 3 else min(math.ceil(level / 2), 7)

        # Here's the really painful bit. Cleric spell slots ALMOST follow the nice easy
        # Magic-User pattern of moving two steps down each time you go up a spell level.
        # Almost.
        # They actually move 3 steps down the first time (from spell level 1 to spell
        # level 2), and then a nice even 2 steps down for every spell level after that.
        # Special cases, UGH.
        for i in range(highest_spell_level):
            if i <= 1:
                spell_slots.append(CLERIC_SPELL_SLOTS[(level - 1) - (3 * i)])
            else:
                spell_slots.append(CLERIC_SPELL_SLOTS[(level - 1) - (2 * i)])

        # Sigh. Level 20 is a special case that doesn't follow any handy pattern that I
        # could find.
        if level == 20:
            spell_slots = [8, 7, 7, 6, 5, 5, 4]

    return spell_slots


def list_number_of_random_spells_by_level(spells_to_be_added, level):
    """Return a list with the number of random spells to be added for each spell level.

    incredibly_long_and_unwieldy_overly_verbose_function_name_plus_some_spells_and_shit()
    rejected in favor of current VERY REASONABLE function name.
    """
    current_highest_spell_level = min(math.ceil(level / 2), 9)

    if level <= 2:
        spells_to_be_added[0] += 1
        return spells_to_be_added
    # current_highest_spell_level MINUS 1 because the list is zero-indexed, so list[0]
    # is spell level 1, list[1] is spell level 2, etc.
    spells_to_be_added[current_highest_spell_level - 1] += 1
    return list_number_of_random_spells_by_level(spells_to_be_added, level - 1)


def get_magic_notes(pcClass, level, highest_spell_level):
    """Generate notes about spell levels and random spells that must be chosen.

    Clerics have access to all spells of their level or lower, while Magic-Users
    get a new random spell of any level they can cast each time they level up.
    So a Magic-User above level 1 must add random spells, but can choose which
    level those random spells come from.
    I think Elves are SUPPOSED to have the same spell slot progression as Magic-Users,
    but in the book as written their progression is VERY SLIGHTLY different. I'm leaving
    Elves' spell slots out of Lament until I can contact Raggi or someone to figure out
    if they're a mistake or not.
    """
    notes = ""

    if pcClass.casefold() == "Cleric".casefold():
        notes = CLERIC_SPELL_NOTES.format(highest_spell_level)

    if pcClass.casefold() == "Magic-User".casefold() and level > 1:
        spells_to_be_added = [0 for i in range(highest_spell_level)]
        spells_to_be_added = list_number_of_random_spells_by_level(
            spells_to_be_added,
            level)
        notes = MU_SPELL_NOTES

        for i in range(highest_spell_level):
            # This unwieldy bastard is the easiest way to generate a list of levels
            # to choose random spells from. We're adding "Level [NUMBER] or lower:",
            # then a set of numbered braces (like this: {0}) which we can fill on
            # the next line with the number of spells to be randomly assigned for
            # that spell level or lower.
            # The reason for the huge mess of braces is because we need literal braces
            # surrounding a number, and the way to escape braces to get literal braces
            # is to double them. So, to get actual braces we have {{ }}. And then, inside,
            # to insert the number into them we have {}. If we didn't do this, we'd only
            # get the number, and not the braces around it.
            notes += "Level {} or lower:{{{}}}\n".format(i + 1, i)
        # Now we fill those empty braces with the number of spells to be randomly
        # assigned for each spell level.
        notes = notes.format(*spells_to_be_added)

    return notes


def create_spellsheet_pdf(details, PC_name, filename=None, directory=None):
    """Get spell list for character, fill spell sheet PDF with spell information."""
    spell_list = create_spell_list(details['spell'], details['class'], details['level'])
    spell_details = tools.get_item_details(spell_list, 'Spell', filename=None)
    spell_slots = get_spell_slots(details['class'], details['level'])

    i = 0
    for item in spell_details:
        for name in SPELL_FIELDS:
            prefix = name + str(i)
            item[prefix] = item[name]
            del item[name]
        i += 1

    spell_list = tools.add_PDF_field_names(spell_list, 'Spell')
    for item in spell_details:
        spell_list = {**spell_list, **item}

    spell_list['MagicNotes'] = get_magic_notes(
        details['class'],
        details['level'],
        len(spell_slots))

    spell_slots = tools.add_PDF_field_names(spell_slots, details['class'])
    spell_list = {**spell_list, **spell_slots}

    if directory is None:
        directory = tempfile.TemporaryDirectory(dir=os.getcwd()).name

    spell_name = PC_name + '_Spells.pdf'
    spell_fdf_name = PC_name + '_Spells.fdf'

    fdf_spell_data = forge_fdf("", spell_list, [], [], [])
    with open(os.path.join(directory, spell_fdf_name), 'wb') as f:
        f.write(fdf_spell_data)

    path_to_pdftk = tools.get_pdftk_path()

    args = [path_to_pdftk,
            FILLABLE_SPELL_SHEET,
            'fill_form',
            spell_fdf_name,
            'output',
            spell_name,
            'flatten']

    # Fill the spell form with PDFtk, store them in the tempfiles directory.
    subprocess.run(args, cwd=directory, **tools.subprocess_args(False))
