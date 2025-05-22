import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from Battleship.wasteland_battleship_secretset import GameState, SHIP_SHAPES
import pytest

def test_ship_placement():
    state = GameState()
    shape = [(0, i) for i in range(5)]  # Carrier
    assert state.can_place_ship('Alpha', shape, (0,0), 0)
    assert state.add_ship('Alpha', shape, (0,0), 0)
    assert not state.can_place_ship('Alpha', shape, (0,0), 0)

def test_shot_processing():
    state = GameState()
    shape = [(0, i) for i in range(2)]  # Destroyer
    state.add_ship('Alpha', shape, (0,0), 0)
    result = state.process_shot('Omega', (0,0), 'Player1')
    assert result in ('HIT', 'MISS')

def test_reset():
    state = GameState()
    state.add_ship('Alpha', [(0,0)], (0,0), 0)
    state.process_shot('Omega', (0,0), 'Player1')
    state.reset()
    assert state.ships_alpha == []
    assert state.ships_omega == []
    assert state.shots_log == []

def test_get_ship_coords():
    state = GameState()
    shape = [(0, i) for i in range(3)]
    state.add_ship('Alpha', shape, (1,1), 0)
    coords = state.get_ship_coords('Alpha')
    assert (1,1) in coords and (1,2) in coords and (1,3) in coords

def test_remove_ship_at():
    state = GameState()
    shape = [(0, i) for i in range(2)]
    state.add_ship('Alpha', shape, (2,2), 0)
    assert state.remove_ship_at('Alpha', (2,2))
    assert not state.remove_ship_at('Alpha', (2,2))  # Already removed

def test_undo_shot():
    state = GameState()
    state.add_ship('Alpha', [(0,0)], (0,0), 0)
    state.process_shot('Omega', (0,0), 'Player1')
    state.undo_shot()
    assert state.shots_log == []
    # Undo with no shots should not error
    state.undo_shot()

def test_get_hit_buyers():
    state = GameState()
    state.add_ship('Alpha', [(0,0)], (0,0), 0)
    state.process_shot('Omega', (0,0), 'Player1')
    hits = state.get_hit_buyers()
    assert isinstance(hits, list)
    if hits:
        assert hits[0][0] == 'Player1'

def test_get_stats():
    state = GameState()
    state.add_ship('Alpha', [(0,0)], (0,0), 0)
    state.process_shot('Omega', (0,0), 'Player1')
    player_stats, team_stats = state.get_stats()
    assert 'Player1' in player_stats
    assert 'Alpha' in team_stats and 'Omega' in team_stats

def test_randomize_ships():
    state = GameState()
    state.randomize_ships('Alpha')
    assert len(state.ships_alpha) == len(SHIP_SHAPES)
    state.randomize_ships('Omega')
    assert len(state.ships_omega) == len(SHIP_SHAPES) 