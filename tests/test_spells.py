import pytest
import math
import spells


@pytest.mark.parametrize("pcClass, expected", [
    ('Magic-User', 'Summon'),
    ('Cleric', 'Bless'),
    ('Elf', 'Read Magic')])
def test_create_spell_list(pcClass, expected):
    """Is the Level 1 spell list being filled with the appropriate spells?"""
    spell_list = spells.create_spell_list([], pcClass, level=1)
    assert expected in spell_list
    assert "Magic Missle" not in spell_list


@pytest.mark.parametrize("level", list(range(2, 21)))
def test_list_number_of_random_spells_by_level(level):
    """Are the number of random spells Magic-Users must add calculated correctly?"""
    highest_spell_level = min(math.ceil(level / 2), 9)

    number_of_spells_by_level = [0 for i in range(highest_spell_level)]
    number_of_spells_by_level = spells.list_number_of_random_spells_by_level(
        number_of_spells_by_level,
        level)

    # Always ONE level 1 spell
    assert number_of_spells_by_level[0] == 1
    # Always TWO of every spell level except the last (highest)
    for item in number_of_spells_by_level[1:-1]:
        assert item == 2

    # Even levels (other than 2) below 19 have TWO spells of the highest level,
    # odd levels have ONE.
    if 2 < level < 19:
        if level % 2 == 0:
            assert number_of_spells_by_level[-1] == 2
        else:
            assert number_of_spells_by_level[-1] == 1

    # Levels 19 and 20 are special cases - they each add ONE to the highest spell level.
    elif level > 19:
        assert number_of_spells_by_level[-1] == 2 + (level - 18)
