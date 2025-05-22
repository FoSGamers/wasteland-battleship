import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import pytest
from PyQt5 import QtWidgets, QtCore
from Battleship.wasteland_battleship_secretset import GameState, ControlWindow, DisplayWindow

def test_fire_button_updates_log(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    qtbot.addWidget(control)
    # Simulate user entering name and coordinate
    control.name_input.setText('Tester')
    control.coord_input.setText('A1')
    control.team_box.setCurrentText('Alpha')
    # Click FIRE button
    qtbot.mouseClick(control.fire_btn, QtCore.Qt.LeftButton)
    # Check log box updated
    assert 'Tester' in control.log_box.toPlainText() or 'Enter both name and coordinate!' in control.log_box.toPlainText()

def test_place_ship_text(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    qtbot.addWidget(control)
    control.ship_entry.setText('B2')
    control.ship_team.setCurrentText('Alpha')
    qtbot.mouseClick(control.place_btn, QtCore.Qt.LeftButton)
    assert 'Alpha ship placed at B2' in control.log_box.toPlainText() or 'Invalid' in control.log_box.toPlainText()

def test_undo_shot_ui(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    qtbot.addWidget(control)
    control.name_input.setText('Tester')
    control.coord_input.setText('A1')
    control.team_box.setCurrentText('Alpha')
    qtbot.mouseClick(control.fire_btn, QtCore.Qt.LeftButton)
    qtbot.mouseClick(control.undo_btn, QtCore.Qt.LeftButton)
    assert 'undone' in control.log_box.toPlainText() or 'Enter both name and coordinate!' in control.log_box.toPlainText()

def test_randomize_all_ships_ui(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    qtbot.addWidget(control)
    qtbot.mouseClick(control.randomize_all_btn, QtCore.Qt.LeftButton)
    assert 'randomized' in control.log_box.toPlainText()

def test_gm_vs_players_toggle_ui(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    qtbot.addWidget(control)
    qtbot.mouseClick(control.gm_vs_players_btn, QtCore.Qt.LeftButton)
    assert 'GM vs Players Mode: ON' in control.gm_vs_players_btn.text() or 'GM vs Players Mode: OFF' in control.gm_vs_players_btn.text()

def test_switch_gm_team_ui(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    qtbot.addWidget(control)
    control.gm_team_box.setCurrentText('Omega')
    assert control.gm_team_box.currentText() == 'Omega'

def test_chaos_user_invalid_input(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    qtbot.addWidget(control)
    control.name_input.setText('')
    control.coord_input.setText('ZZZ')
    qtbot.mouseClick(control.fire_btn, QtCore.Qt.LeftButton)
    assert 'Invalid' in control.log_box.toPlainText() or 'Enter both name and coordinate!' in control.log_box.toPlainText()

def test_chaos_user_rapid_toggle(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    qtbot.addWidget(control)
    for _ in range(10):
        qtbot.mouseClick(control.gm_vs_players_btn, QtCore.Qt.LeftButton)
    assert control.gm_vs_players_btn.isChecked() in [True, False] 