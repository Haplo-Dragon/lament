#!/usr/bin/python

import csv
from fdfgen import forge_fdf
import subprocess
import requests
import tempfile
import os


def combine_dicts(dict1, dict2):
    combined = dict1.copy()
    combined.update(dict2)
    return combined


def generate_dict(equiplist, type='NonEnc'):
    equipdict = {}
    for i in range(len(equiplist)):
        prefix = type + str(i)
        equipdict[prefix] = equiplist[i]
    return equipdict


def get_pdftk_path():
    path_to_pdftk = os.path.join(os.getcwd(), "PDFtk", "bin", "pdftk.exe")
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
    with requests.session() as r:
        details = {'class': ""}
        i = 1
        if pc_class:
            while details['class'] != pc_class:
                try:
                    # print("This is try #", i)
                    r = requests.get("http://character.totalpartykill.ca/lotfp/json", timeout=5)
                    details = r.json()
                    i += 1
                except ConnectionError as e:
                    print("There was a connection error: %s" % e)
                except TimeoutError as e:
                    print("The connection timed out: %s" % e)

        else:
            try:
                r = requests.get("http://character.totalpartykill.ca/lotfp/json", timeout=5)
                details = r.json()
            except ConnectionError as e:
                print("There was a connection error: %s" % e)
            except TimeoutError as e:
                print("The connection timed out: %s" % e)
        return details


def format_equipment_list(details, calculate_encumbrance=True):
    """
    Splits the huge, unsorted equipment list provided by the remote generator into logical bits.
        Duplicates the weapons and their statistics to fill the weapons table on the character sheet.
        Splits the non-encumbering, oversized, and normal items into their own containers, removing them from
        the original equipment list.
        Splits the money from the original equipment list.
    Generates an encumbrance value with the split equipment.
    Combines all of the separated and sorted equipment dictionaries into one.
    :param details: The details of the character - easily obtained from the JSON remote generator.
    :return: The combined and sorted equipment, weapons with stats, encumbrance.
    """
    # Get a list of equipment (including money and weapons)
    equipment = details['equipment']

    # Split the money, non-encumbering, and oversized items from the equipment list
    weapons = get_weapons_and_stats(equipment)
    equipment, nonenc_equipment = split_tiny(equipment)
    equipment, over_equipment = split_over(equipment)
    equipment, money = split_money(equipment)

    # Generate dictionary version of the normal equipment list
    normal_equipment = generate_dict(equipment, 'Normal')

    if calculate_encumbrance:
        encumbrance = {'Encumbrance': get_encumbrance(normal_equipment, details['class'])}
    else:
        encumbrance = {'Encumbrance': ""}

    # Create a combined equipment list
    comb_equipment = combine_dicts(nonenc_equipment, over_equipment)
    comb_equipment = combine_dicts(comb_equipment, normal_equipment)
    comb_equipment = combine_dicts(comb_equipment, money)
    comb_equipment = combine_dicts(comb_equipment, weapons)
    comb_equipment = combine_dicts(comb_equipment, encumbrance)

    return comb_equipment


def split_over(target, filename=None):
    over = []
    if filename is None:
        with open('Item Lists\Oversized.txt', 'r') as o:
            oversized = o.read().splitlines()
    else:
        with open(filename, 'r') as o:
            oversized = o.read().splitlines()
    for item in target:
        if item in oversized:
            over.append(item)
            target.remove(item)

    over = generate_dict(over, 'Over')

    return (target, over)


def split_tiny(target, filename=None):
    non_enc = []
    if filename is None:
        with open('Item Lists\TinyItems.txt', 'r') as t:
            tiny = t.read().splitlines()
    else:
        with open(filename, 'r') as t:
            tiny = t.read().splitlines()
    for item in tiny:
        if item in target:
            non_enc.append(item)
            target.remove(item)

    non_enc = generate_dict(non_enc, 'NonEnc')

    return (target, non_enc)


def split_money(target):
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


def get_encumbrance(normal_item_dict, pc_class):
    # Set encumbrance from normal (that is, encumbering) items carried
    encumbrance = int(len(normal_item_dict) / 5.1)

    # Check for chain or plate armor that would add extra encumbrance
    if 'Chain Armor' in normal_item_dict.values():
        encumbrance += 1
    if 'Plate Armor' in normal_item_dict.values():
        encumbrance += 2

    # Dwarves can carry more, so their first point of encumbrance doesn't count.
    if pc_class == 'Dwarf':
        encumbrance -= 1

    return encumbrance


def get_weapons_and_stats(target, filename=None):
    weapondict = {}
    listofdicts = []

    if filename is None:
        with open('Item Lists\WeaponStats.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Weapon'] in target:
                    listofdicts.append(row)

    else:
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Weapon'] in target:
                    listofdicts.append(row)

    # Find ammo in equipment list and associate it with the correct weapon.
    for weapon in listofdicts:
        if weapon['Ammo'] == 'Yes':
            for item in target:
                arrows_index = item.find('Arrows')
                if arrows_index is not -1:
                    weapon['Ammo'] = item[arrows_index - 3:]
        else:
            weapon['Ammo'] = ""

    fields = ['Weapon', 'Damage', 'Short', 'Medium', 'Long', 'Ammo']
    i = 0
    for item in listofdicts:
        for name in fields:
            prefix = name + str(i)
            item[prefix] = item[name]
            del item[name]
        i += 1

    for item in listofdicts:
        weapondict = combine_dicts(weapondict, item)

    return weapondict


def clear_mod_zeroes(modsdict):
    for item in modsdict.keys():
        if modsdict[item] == '0':
            modsdict[item] = ""
    return modsdict


def create_spellsheet_pdf(details, name, filename=None, directory=None):
    cleric_spells = ['Bless', 'Command', 'Cure Light Wounds', 'Detect Evil', 'Invisibility to Undead',
                     'Protection from Evil', 'Purify Food & Drink', 'Remove Fear', 'Sanctuary', 'Turn Undead']
    spell_list = details['spell']
    if details['class'] == 'Magic-User':
        spell_list.append('Summon')
    if details['class'] == 'Cleric':
        spell_list = cleric_spells
    if details['class'] == 'Elf':
        spell_list = ['Read Magic']

    spell_name = name + ' Spells.pdf'
    spell_fdf_name = name + ' Spells.fdf'
    # Correct for spelling error in Magic Missile
    if 'Magic Missle' in spell_list:
        spell_list.remove('Magic Missle')
        spell_list.append('Magic Missile')

    listofdicts = []

    if filename is None:
        with open('Item Lists\LevelOneSpells.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Spell'] in spell_list:
                    listofdicts.append(row)

    else:
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Spell'] in spell_list:
                    listofdicts.append(row)

    fields = ['Spell', 'Duration', 'Range', 'Save', 'Reversible', 'Effect', 'Flavor', 'Page']
    i = 0
    for item in listofdicts:
        for name in fields:
            prefix = name + str(i)
            item[prefix] = item[name]
            del item[name]
        i += 1

    spell_list = generate_dict(spell_list, 'Spell')
    for item in listofdicts:
        spell_list = combine_dicts(spell_list, item)

    if directory is None:
        directory = tempfile.TemporaryDirectory(dir=os.getcwd()).name

    fdf_spell_data = forge_fdf("", spell_list, [], [], [])
    with open(directory + '\\' + spell_fdf_name, 'wb') as f:
        f.write(fdf_spell_data)

    path_to_pdftk = get_pdftk_path()

    args = [path_to_pdftk,
            '..\LotFPSpellSheetFillable.pdf',
            'fill_form',
            spell_fdf_name,
            'output',
            spell_name,
            'flatten']

    # Fill the spell form with PDFtk, store them in the tempfiles directory.
    subprocess.run(args, cwd=directory, **subprocess_args(False))
