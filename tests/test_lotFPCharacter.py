import pytest


@pytest.fixture(scope='module')
def PC():
    import character
    PC = character.LotFPCharacter()
    return PC


class TestLotFPCharacter():
    def test_creation(self, PC):
        assert PC is not None

    def test_saves(self, PC):
        for key, val in PC.saves.items():
            assert key in ['poison', 'wands', 'stone', 'breath', 'magic']
            assert val > 0
            assert val <= 18
