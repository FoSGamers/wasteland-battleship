import sys
import random
import string
from PyQt5 import QtWidgets, QtGui, QtCore

GRID_SIZE = 8
CELL_SIZE = 50
HIT_COLOR = "red"
MISS_COLOR = "blue"
EMPTY_COLOR = "white"
ALPHA_COLOR = "lightgray"
OMEGA_COLOR = "lightblue"


class GameState:
    def __init__(self):
        self.grid_alpha = {(x, y): EMPTY_COLOR for x in range(GRID_SIZE) for y in range(GRID_SIZE)}
        self.grid_omega = {(x, y): EMPTY_COLOR for x in range(GRID_SIZE) for y in range(GRID_SIZE)}
        self.hits_alpha = set()
        self.hits_omega = set()
        self.ships_alpha = self.place_random_ships()
        self.ships_omega = self.place_random_ships()

    def place_random_ships(self):
        ships = set()
        while len(ships) < 5:
            ships.add((random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)))
        return ships

    def process_shot(self, team, coord):
        x, y = coord
        if team == "Alpha":
            if coord in self.hits_alpha:
                return
            if coord in self.ships_omega:
                self.grid_omega[coord] = HIT_COLOR
            else:
                self.grid_omega[coord] = MISS_COLOR
            self.hits_alpha.add(coord)
        else:
            if coord in self.hits_omega:
                return
            if coord in self.ships_alpha:
                self.grid_alpha[coord] = HIT_COLOR
            else:
                self.grid_alpha[coord] = MISS_COLOR
            self.hits_omega.add(coord)


class DisplayWindow(QtWidgets.QWidget):
    def __init__(self, game_state):
        super().__init__()
        self.game_state = game_state
        self.setWindowTitle("Wasteland Battleship Display")
        self.setFixedSize(GRID_SIZE * CELL_SIZE * 2 + 100, GRID_SIZE * CELL_SIZE + 60)
        self.show()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        for grid, color_base, offset_x in [
            (self.game_state.grid_alpha, ALPHA_COLOR, 20),
            (self.game_state.grid_omega, OMEGA_COLOR, GRID_SIZE * CELL_SIZE + 60),
        ]:
            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    color = grid[(x, y)]
                    display_color = color_base if color == EMPTY_COLOR else color
                    rect = QtCore.QRect(offset_x + x * CELL_SIZE, 20 + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    painter.fillRect(rect, QtGui.QColor(display_color))
                    painter.drawRect(rect)


class ControlWindow(QtWidgets.QWidget):
    def __init__(self, game_state, display_window):
        super().__init__()
        self.game_state = game_state
        self.display_window = display_window
        self.setWindowTitle("Wasteland Battleship GM Control")
        self.setFixedSize(400, 200)

        self.coord_input = QtWidgets.QLineEdit(self)
        self.coord_input.setPlaceholderText("Enter coordinate (e.g., B4)")
        self.coord_input.setGeometry(20, 20, 150, 30)

        self.team_selector = QtWidgets.QComboBox(self)
        self.team_selector.addItems(["Alpha", "Omega"])
        self.team_selector.setGeometry(200, 20, 100, 30)

        self.fire_button = QtWidgets.QPushButton("FIRE!", self)
        self.fire_button.setGeometry(150, 70, 100, 40)
        self.fire_button.clicked.connect(self.fire)

        self.info_box = QtWidgets.QTextEdit(self)
        self.info_box.setReadOnly(True)
        self.info_box.setGeometry(20, 120, 360, 60)
        self.show()

    def fire(self):
        coord_text = self.coord_input.text().strip().upper()
        team = self.team_selector.currentText()

        try:
            col = string.ascii_uppercase.index(coord_text[0])
            row = int(coord_text[1:]) - 1
            if not (0 <= col < GRID_SIZE and 0 <= row < GRID_SIZE):
                raise ValueError
        except:
            self.info_box.setText("Invalid coordinate. Try A1 to H8.")
            return

        coord = (col, row)
        self.game_state.process_shot(team, coord)
        self.display_window.update()

        ship_hit = (
            coord in self.game_state.ships_omega if team == "Alpha"
            else coord in self.game_state.ships_alpha
        )
        result = "HIT!" if ship_hit else "MISS."
        self.info_box.setText(f"{team} fires at {coord_text} → {result}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    sys.exit(app.exec_()) 