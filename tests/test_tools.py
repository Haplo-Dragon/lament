import pytest
import tools


@pytest.mark.parametrize("equip_list, equip_type", [
    (['stuff', 'things', 'more_stuff'], "NonEnc"),
    (['foo', 'bar', 'foobar'], "Normal"),
    (['Shield', 'Giant pole', 'ROUS'], "Oversized")])
def test_add_PDF_field_names(equip_list, equip_type):
    equip_dict = tools.add_PDF_field_names(equip_list, equip_type)
    assert isinstance(equip_dict, dict)
    for prefix in equip_dict.keys():
        assert equip_type in prefix


@pytest.mark.parametrize("filename, prefix, does_not_belong, splitter", [
    (tools.OVERSIZED_ITEMS, "Over", "Tiny Kitten", tools.split_over),
    (tools.TINY_ITEMS, "NonEnc", "Full-size Tiger", tools.split_tiny)])
def test_split_over_and_tiny(filename, prefix, does_not_belong, splitter):
    """Are we splitting oversized/tiny items from a list and returning a prefixed dict?"""
    with open(filename, 'r') as file:
        to_be_split = file.read().splitlines()
    to_be_split.append(does_not_belong)
    to_be_split, split_items = splitter(to_be_split)
    assert isinstance(split_items, dict)
    for key, value in split_items.items():
        assert prefix in key
        assert value not in to_be_split
    assert does_not_belong in to_be_split


@pytest.mark.parametrize("money", ["1 sp 11 Cp", "1 Cp"])
def test_split_money(money):
    """Are we splitting money from a list and returning two lists?"""
    equipment = ["Hitchhiker's Guide to the Galaxy", "Towel"]
    equipment.append(money)
    equipment, money = tools.split_money(equipment)
    for item in equipment:
        assert ' Cp' not in item
        assert ' sp' not in item
    for item in money:
        assert item.find(' Cp') or item.find(' sp')


def test_get_encumbrance(normal_equipment, oversized_equipment):
    """Is encumbrance calculated correctly for normal and oversized items?"""
    encumbrance = tools.get_encumbrance(
        normal_equipment,
        oversized_equipment,
        pc_class="Dwarf")
    assert encumbrance >= 0
    assert encumbrance == 5


@pytest.mark.parametrize("modifiers", [
    {'STR': '0', 'DEX': '0', 'CON': '0', 'INT': '0', 'WIS': '0', 'CHA': '0'},
    {'STR': '-1', 'DEX': '-2', 'CON': '-1', 'INT': '-2', 'WIS': '0', 'CHA': '-1'},
    {'STR': '+1', 'DEX': '+2', 'CON': '+1', 'INT': '+2', 'WIS': '+1', 'CHA': '0'},
    {'STR': '-2', 'DEX': '+3', 'CON': '0', 'INT': '0', 'WIS': '+1', 'CHA': '-1'},
    {'STR': '+1', 'DEX': '+1', 'CON': '+1', 'INT': '+1', 'WIS': '+1', 'CHA': '+1'}])
def test_clear_mod_zeroes(modifiers):
    zeroes_cleared = tools.clear_mod_zeroes(modifiers)
    assert '0' not in zeroes_cleared.values()
