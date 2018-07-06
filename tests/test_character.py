import pytest
import json
import character


@pytest.mark.parametrize("character_class, expected_alignment", [
    ("Halfling", None),
    ("Cleric", "Lawful"),
    ("Magic-User", "Chaotic"),
    ("Elf", "Chaotic")])
def test_align(halfling, character_class, expected_alignment):
    """Is alignment assigned correctly based on class?"""
    halfling.pcClass = character_class
    alignment = halfling.align()
    assert alignment == expected_alignment


@pytest.mark.parametrize("level", list(range(1, 21)))
def test_skill_points(level, halfling, mocker):
    """Are the correct number of skill points assigned to Specialists?"""
    mock_fetch = mocker.patch('lament.tools.fetch_character')
    with open('tests/mocked_fetch_specialist.json', 'r') as f:
        mock_fetch.return_value = json.load(f)
    specialist = character.LotFPCharacter(desired_level=level)

    assert specialist.skill_points == 2 * (level - 1)
    assert halfling.skill_points is None
