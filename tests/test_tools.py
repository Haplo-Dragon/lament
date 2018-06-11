import pytest
from lament_mod import tools


@pytest.mark.parametrize("equip_list, equip_type", [
    (['stuff', 'things', 'more_stuff'], "NonEnc"),
    (['foo', 'bar', 'foobar'], "Normal"),
    (['Shield', 'Giant pole', 'ROUS'], "Oversized")])
def test_generate_dict(equip_list, equip_type):
    equip_dict = tools.add_PDF_field_names(equip_list, equip_type)
    assert isinstance(equip_dict, dict)
    for item in equip_dict.items():
        assert equip_type in item[0]


@pytest.mark.parametrize("modifiers", [
    {'STR': '0', 'DEX': '0', 'CON': '0', 'INT': '0', 'WIS': '0', 'CHA': '0'},
    {'STR': '-1', 'DEX': '-2', 'CON': '-1', 'INT': '-2', 'WIS': '0', 'CHA': '-1'},
    {'STR': '+1', 'DEX': '+2', 'CON': '+1', 'INT': '+2', 'WIS': '+1', 'CHA': '0'},
    {'STR': '-2', 'DEX': '+3', 'CON': '0', 'INT': '0', 'WIS': '+1', 'CHA': '-1'},
    {'STR': '+1', 'DEX': '+1', 'CON': '+1', 'INT': '+1', 'WIS': '+1', 'CHA': '+1'}])
def test_clear_mod_zeroes(modifiers):
    zeroes_cleared = tools.clear_mod_zeroes(modifiers)
    assert '0' not in zeroes_cleared.values()


@pytest.mark.parametrize("pcClass, expected", [
    ('Magic-User', 'Summon'),
    ('Cleric', 'Bless'),
    ('Elf', 'Read Magic')])
def test_add_class_based_spells(pcClass, expected):
    spell_list = tools.add_class_based_spells([], pcClass)
    assert expected in spell_list
