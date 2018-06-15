#!/usr/bin/python

import csv
from fdfgen import forge_fdf
import subprocess
import requests
import tempfile
import os
import platform

LEVEL_ONE_SPELLS = os.path.join(
    os.path.dirname(__file__),
    "Item Lists",
    "LevelOneSpells.csv")

OVERSIZED_ITEMS = os.path.join(
    os.path.dirname(__file__),
    "Item Lists",
    "Oversized.txt")

TINY_ITEMS = os.path.join(
    os.path.dirname(__file__),
    "Item Lists",
    "TinyItems.txt")

WEAPONS = os.path.join(
    os.path.dirname(__file__),
    "Item Lists",
    "Weapons.txt")

WEAPON_STATS = os.path.join(
    os.path.dirname(__file__),
    "Item Lists",
    "WeaponStats.csv")

CLERIC_SPELLS = [
    'Bless', 'Command', 'Cure Light Wounds', 'Detect Evil',
    'Invisibility to Undead', 'Protection from Evil',
    'Purify Food & Drink', 'Remove Fear', 'Sanctuary', 'Turn Undead']

SPELL_FIELDS = [
    'Spell', 'Duration', 'Range', 'Save',
    'Reversible', 'Effect', 'Flavor', 'Page']

WEAPON_FIELDS = ['Weapon', 'Damage', 'Short', 'Medium', 'Long', 'Ammo']

CHARACTER_GEN_URL = "http://character.totalpartykill.ca/lotfp/json"


def add_PDF_field_names(equiplist, type='NonEnc'):
    """Takes a list of items and their type and returns a dictionary with the items
     as values and the type followed by a sequential number (type0, type1, etc.) as
     keys. These are generally used to fill fields in a blank PDF, with keys
     corresponding to field names.
     """
    equipdict = {}
    for index, item in enumerate(equiplist):
        prefix = ''.join((type, str(index)))
        equipdict[prefix] = equiplist[index]
    return equipdict


def get_pdftk_path():
    if platform.system() == "Linux":
        path_to_pdftk = "pdftk"
    else:
        path_to_pdftk = os.path.join(
            os.path.dirname(__file__),
            "PDFtk",
            "bin",
            "pdftk.exe")

    return path_to_pdftk


def subprocess_args(include_stdout=True):
    """
    Create a set of arguments which make a ``subprocess.Popen`` (and
    variants) call work with or without Pyinstaller, ``--noconsole`` or
    not, on Windows and Linux. Typical use::

      subprocess.call(['program_to_run', 'arg_1'], **subprocess_args())

    When calling ``check_output``::

      subprocess.check_output(['program_to_run', 'arg_1'],
                              **subprocess_args(False))
    The following is true only on Windows.
    """
    if hasattr(subprocess, 'STARTUPINFO'):
        # On Windows, subprocess calls will pop up a command window by default
        # when run from Pyinstaller with the ``--noconsole`` option. Avoid this
        # distraction.
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # Windows doesn't search the path by default. Pass it an environment so
        # it will.
        env = os.environ
    else:
        si = None
        env = None
        # ``subprocess.check_output`` doesn't allow specifying ``stdout``::
        #
        #   Traceback (most recent call last):
        #     File "test_subprocess.py", line 58, in <module>
        #       **subprocess_args(stdout=None))
        #     File "C:\Python27\lib\subprocess.py", line 567, in check_output
        #       raise ValueError('stdout argument not allowed, it will be overridden.')
        #   ValueError: stdout argument not allowed, it will be overridden.
        #
        # So, add it only if it's needed.
    if include_stdout:
        ret = {'stdout:': subprocess.PIPE}
    else:
        ret = {}

        # On Windows, running this from the binary produced by Pyinstaller
        # with the ``--noconsole`` option requires redirecting everything
        # (stdin, stdout, stderr) to avoid an OSError exception
        # "[Error 6] the handle is invalid."
    ret.update({'stdin': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'startupinfo': si,
                'env': env})
    return ret


def fetch_character(pc_class=None):
    """Fetch character data JSON from the remote generator."""
    with requests.session() as r:
        details = {'class': ""}
        if pc_class:
            while details['class'] != pc_class:
                try:
                    r = requests.get(CHARACTER_GEN_URL, timeout=10)
                    details = r.json()
                except ConnectionError as e:
                    print("There was a connection error: %s" % e)
                except TimeoutError as e:
                    print("The connection timed out: %s" % e)
        else:
            try:
                r = requests.get(CHARACTER_GEN_URL, timeout=10)
                details = r.json()
            except ConnectionError as e:
                print("There was a connection error: %s" % e)
            except TimeoutError as e:
                print("The connection timed out: %s" % e)

        return details


def format_equipment_list(details, calculate_encumbrance=True):
    """
    Split the huge, unsorted equipment list provided by the remote
    generator into logical bits, sort, prefix, and return it.

    Duplicates the weapons and their statistics (once to fill the weapons table
    and again for the items carried list). Splits the non-encumbering, oversized,
    and normal items into their own containers, removing them from the original equipment
    list. Splits the money from the original equipment list. Generates an
    encumbrance value with the split equipment. Combines all of the separated
    and sorted equipment dictionaries into one.

    :param details: The details of the character - easily obtained from the
    JSON remote generator.
    :return: The combined and sorted equipment, weapons with stats,
    and encumbrance, prefixed with the proper PDF field names.
    """
    # Get a list of equipment (including money and weapons)
    equipment = details['equipment']

    # Split the money, non-encumbering, and oversized items from the
    # equipment list
    weapons = get_weapons_and_stats(equipment)
    equipment, nonenc_equipment = split_tiny(equipment)
    equipment, over_equipment = split_over(equipment)
    equipment, money = split_money(equipment)

    # Generate dictionary version of the normal equipment list
    normal_equipment = add_PDF_field_names(equipment, 'Normal')

    if calculate_encumbrance:
        encumbrance = {'Encumbrance': get_encumbrance(
            normal_equipment,
            over_equipment,
            details['class'])}
    else:
        encumbrance = {'Encumbrance': ""}

    # Create a combined equipment list
    comb_equipment = {}
    comb_equipment = {
        **comb_equipment,
        **nonenc_equipment,
        **over_equipment,
        **normal_equipment,
        **money,
        **weapons,
        **encumbrance
    }

    return comb_equipment


def split_over(target, filename=None):
    """Split oversized items from the equipment list and return both lists."""
    over = []
    if filename is None:
        filename = OVERSIZED_ITEMS

    with open(filename, 'r') as o:
        oversized = o.read().splitlines()

    for item in target:
        if item in oversized:
            over.append(item)
            target.remove(item)

    over = add_PDF_field_names(over, 'Over')

    return (target, over)


def split_tiny(target, filename=None):
    """Split non-encumbering items from the equipment list and return both lists."""
    non_enc = []
    if filename is None:
        filename = TINY_ITEMS

    with open(filename, 'r') as t:
        tiny = t.read().splitlines()

    for item in tiny:
        if item in target:
            non_enc.append(item)
            target.remove(item)

    non_enc = add_PDF_field_names(non_enc, 'NonEnc')

    return (target, non_enc)


def split_money(target):
    """Split money from the equipment list and return both lists."""
    money = {}
    for item in target:
        cp_index = item.find(' Cp')
        sp_index = item.find(' sp')
        if (cp_index is not -1) and (sp_index is not -1):
            money['cp'] = item[item.find(' Cp') - 2:]
            money['sp'] = item[:item.find(' sp') + 3]
        elif cp_index is not -1:
            money['cp'] = item[cp_index - 1]
            target.remove(item)

    return (target, money)


def get_encumbrance(normal_items, oversized_items, pc_class):
    """Set encumbrance from normal (that is, encumbering) items carried.

    Encumbrance is calculated from number of items carried, in multiples of 5.
    0-5 items is 0 encumbrance, 6-10 is 1 encumbrance, 11-16 is 2 encumbrance,
    etc. This is why we're taking the whole number result of a division
    by 5.1 — it goes up by one after each multiple of 5.
    """
    encumbrance = int(len(normal_items) / 5.1)

    # Check for chain or plate armor that would add extra encumbrance
    if 'Chain Armor' in normal_items.values():
        encumbrance += 1
    if 'Plate Armor' in normal_items.values():
        encumbrance += 2

    # Check for oversized items (shields, polearms, etc.).
    # Each oversized item adds an encumbrance point.
    encumbrance += len(oversized_items)

    # Dwarves can carry more, so their first point of encumbrance
    # doesn't count.
    if pc_class == 'Dwarf':
        encumbrance -= 1

    # Make sure encumbrance isn't negative. Wouldn't want characters
    # floating away into the sky.
    if encumbrance < 0:
        encumbrance = 0

    return encumbrance


def get_weapons_and_stats(original_equipment_list, filename=None):
    """Split weapons from equipment list, add stats, and return them."""
    weapondict = {}
    weapon_details = get_item_details(original_equipment_list, 'Weapon', filename=None)
    weapon_details = get_ammo(original_equipment_list, weapon_details)

    i = 0
    for item in weapon_details:
        for name in WEAPON_FIELDS:
            prefix = name + str(i)
            item[prefix] = item[name]
            del item[name]
        i += 1

    for item in weapon_details:
        weapondict = {**weapondict, **item}

    return weapondict


def get_ammo(original_equipment_list, weapon_details):
    """Find ammo in equipment list and associate it with the correct weapon."""
    for weapon in weapon_details:
        if weapon['Ammo'] == 'Yes':
            for item in original_equipment_list:
                arrows_index = item.find('Arrows')
                if arrows_index is not -1:
                    weapon['Ammo'] = item[arrows_index - 3:]
        else:
            weapon['Ammo'] = ""
    return weapon_details


def clear_mod_zeroes(modsdict):
    """Clear zeroes from dictionary of attributes and modifiers."""
    for item in modsdict.keys():
        if modsdict[item] == '0':
            modsdict[item] = ""
    return modsdict


def add_class_based_spells(spell_list, pc_class):
    """Add class-specific spells to the spell list."""
    if pc_class == 'Magic-User':
        spell_list.append('Summon')
    if pc_class == 'Cleric':
        spell_list = CLERIC_SPELLS
    if pc_class == 'Elf':
        spell_list = ['Read Magic']
    return spell_list


def get_item_details(original_item_list, item_type, filename=None):
    """Create a list of dictionaries containing item names, details, and flavor
    text for original_item_list, drawn from the file specified or from the default
    files defined in LEVEL_ONE_SPELLS and WEAPON_STATS.
    """
    item_types = {'Spell': LEVEL_ONE_SPELLS, 'Weapon': WEAPON_STATS}
    item_details = []
    if filename is None:
        filename = item_types[item_type]

    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row[item_type] in original_item_list:
                item_details.append(row)

    return item_details


def create_spell_list(original_spell_list, pcClass):
    """Create a full list of spells, including class-specific spells."""
    spell_list = add_class_based_spells(original_spell_list, pcClass)

    # Correct for spelling error in Magic Missile
    if 'Magic Missle' in spell_list:
        spell_list.remove('Magic Missle')
        spell_list.append('Magic Missile')
    return spell_list


def create_spellsheet_pdf(details, name, filename=None, directory=None):
    """Get spell list for character, fill spell sheet PDF with spell information."""
    spell_list = create_spell_list(details['spell'], details['class'])
    spell_details = get_item_details(spell_list, 'Spell', filename=None)

    i = 0
    for item in spell_details:
        for name in SPELL_FIELDS:
            prefix = name + str(i)
            item[prefix] = item[name]
            del item[name]
        i += 1

    spell_list = add_PDF_field_names(spell_list, 'Spell')
    for item in spell_details:
        spell_list = {**spell_list, **item}

    if directory is None:
        directory = tempfile.TemporaryDirectory(dir=os.getcwd()).name

    spell_name = name + '_Spells.pdf'
    spell_fdf_name = name + '_Spells.fdf'

    fdf_spell_data = forge_fdf("", spell_list, [], [], [])
    with open(os.path.join(directory, spell_fdf_name), 'wb') as f:
        f.write(fdf_spell_data)

    path_to_pdftk = get_pdftk_path()

    args = [path_to_pdftk,
            os.path.join(os.path.dirname(__file__), 'LotFPSpellSheetFillable.pdf'),
            'fill_form',
            spell_fdf_name,
            'output',
            spell_name,
            'flatten']

    # Fill the spell form with PDFtk, store them in the tempfiles directory.
    subprocess.run(args, cwd=directory, **subprocess_args(False))
