import pytest
import json


def test_lament_index(client):
    """Does the main page of Lament render properly?"""
    response = client.get('/character')
    assert response.status_code == 200
    list_of_classes = [
        'Fighter',
        'Cleric',
        'Magic-User',
        'Specialist',
        'Dwarf',
        'Elf',
        'Halfling']
    for character_class in list_of_classes:
        assert character_class.encode() in response.data
    assert b'level' in response.data


# Parametrizing allows us to test multiple bad inputs in one test without
# lots of extra code.
@pytest.mark.parametrize("bad_input, expected_message", [
    ("foo", b'Put some NUMBERS in there'),
    ("lurvs", b'I love you'),
    ("-3", b'like NEGATIVE'),
    ("0", b'There you go!')])
def test_bad_data_entered_in_random_field(client, bad_input, expected_message):
    """Do we get the expected error messages when we put garbage in the How
    Many box?"""
    response = client.post(
        '/lament',
        data={'randos': bad_input, 'desired_level': 1},
        follow_redirects=True)
    assert response.status_code == 200
    assert expected_message in response.data


def test_generating_over_20_characters(client, mocker):
    """Does the app generate only one character when asked for >20?"""
    mock_fetch = mocker.patch('lament.tools.fetch_character')
    with open('tests/mocked_fetch_character.json', 'r') as f:
        mock_fetch.return_value = json.load(f)
    response = client.post(
        '/lament',
        data={'randos': 25, 'desired_level': 1},
        follow_redirects=True)
    assert response.status_code == 200
    # Ensure we're sending a PDF
    assert response.mimetype == "application/pdf"

    # This is the easiest way I found to test whether the returned PDF
    # is for one character only. I'm checking if the filename was correctly
    # set to indicate a one character PDF file.
    header_content = response.headers.get('Content-Disposition')
    assert "filename=" in header_content
    assert "1Characters" in header_content


# # TODO: Mock this network call, too.
# @pytest.mark.parametrize("chosen_class", [
#     "Cleric",
#     "Fighter",
#     "Magic-User",
#     "Dwarf",
#     "Elf",
#     "Halfling"])
# def test_generating_specific_class(client, chosen_class):
#     """Does the app generate a PDF with the requested character class?"""
#     response = client.post(
#         '/lament',
#         data={'desired_class': chosen_class},
#         follow_redirects=True)
#     assert response.status_code == 200
#     assert response.mimetype == "application/pdf"
#     header_content = response.headers.get('Content-Disposition')
#     assert "filename=" in header_content
#     assert chosen_class in header_content
