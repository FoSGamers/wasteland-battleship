import pytest
from Battleship.wasteland_battleship_secretset import GameState

def test_ship_placement():
    state = GameState()
    # Place a ship for Alpha
    shape = [(0, i) for i in range(5)]  # Carrier
    assert state.can_place_ship('Alpha', shape, (0,0), 0)
    assert state.add_ship('Alpha', shape, (0,0), 0)
    # Should not be able to overlap
    assert not state.can_place_ship('Alpha', shape, (0,0), 0)

def test_shot_processing():
    state = GameState()
    shape = [(0, i) for i in range(2)]  # Destroyer
    state.add_ship('Alpha', shape, (0,0), 0)
    result = state.process_shot('Omega', (0,0), 'Player1')
    assert result == 'HIT' or result == 'MISS' 