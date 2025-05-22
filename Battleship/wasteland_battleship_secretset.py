import sys, random, string, csv
from PyQt5 import QtWidgets, QtGui, QtCore

GRID_SIZE = 8
CELL_SIZE = 50
HIT_COLOR = "red"
MISS_COLOR = "blue"
EMPTY_COLOR = "white"
ALPHA_COLOR = "lightgray"
OMEGA_COLOR = "lightblue"
SHIP_COLORS = ["green", "orange", "purple", "yellow", "pink"]

# Define ship shapes: (name, list of (x, y) offsets)
SHIP_SHAPES = [
    ("Carrier (5)", [(0, i) for i in range(5)]),
    ("Battleship (4)", [(0, i) for i in range(4)]),
    ("Cruiser (3)", [(0, i) for i in range(3)]),
    ("Submarine (3)", [(0, i) for i in range(3)]),
    ("Destroyer (2)", [(0, i) for i in range(2)]),
    ("L-Shape", [(0,0),(1,0),(2,0),(2,1)]),
]

class GameState:
    def __init__(self):
        self.reset()
        self.alpha_wins = 0
        self.omega_wins = 0

    def reset(self):
        self.grid_alpha = {(x, y): EMPTY_COLOR for x in range(GRID_SIZE) for y in range(GRID_SIZE)}
        self.grid_omega = {(x, y): EMPTY_COLOR for x in range(GRID_SIZE) for y in range(GRID_SIZE)}
        self.hits_alpha = set()
        self.hits_omega = set()
        self.ships_alpha = []  # List of (shape, origin, orientation)
        self.ships_omega = []
        self.shots_log = []
        self.placed_coords_alpha = set()
        self.placed_coords_omega = set()

    def get_ship_coords(self, team):
        # Returns set of all ship cells for the team
        ships = self.ships_alpha if team == "Alpha" else self.ships_omega
        coords = set()
        for shape, origin, orientation in ships:
            for dx, dy in shape:
                if orientation == 0:
                    x, y = origin[0] + dx, origin[1] + dy
                else:
                    x, y = origin[0] + dy, origin[1] - dx
                coords.add((x, y))
        return coords

    def can_place_ship(self, team, shape, origin, orientation):
        coords = set()
        for dx, dy in shape:
            if orientation == 0:
                x, y = origin[0] + dx, origin[1] + dy
            else:
                x, y = origin[0] + dy, origin[1] - dx
            if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
                return False
            coords.add((x, y))
        placed = self.get_ship_coords(team)
        if coords & placed:
            return False
        return True

    def add_ship(self, team, shape, origin, orientation):
        if self.can_place_ship(team, shape, origin, orientation):
            if team == "Alpha":
                self.ships_alpha.append((shape, origin, orientation))
            else:
                self.ships_omega.append((shape, origin, orientation))
            return True
        return False

    def remove_ship_at(self, team, coord):
        ships = self.ships_alpha if team == "Alpha" else self.ships_omega
        for i, (shape, origin, orientation) in enumerate(ships):
            for dx, dy in shape:
                if orientation == 0:
                    x, y = origin[0] + dx, origin[1] + dy
                else:
                    x, y = origin[0] + dy, origin[1] - dx
                if (x, y) == coord:
                    del ships[i]
                    return True
        return False

    def process_shot(self, team, coord, player):
        x, y = coord
        target_grid = self.grid_omega if team == "Alpha" else self.grid_alpha
        target_team = "Omega" if team == "Alpha" else "Alpha"
        target_ships = self.get_ship_coords(target_team)
        hit_set = self.hits_alpha if team == "Alpha" else self.hits_omega

        if coord in hit_set:
            return None  # already fired

        result = "MISS"
        if coord in target_ships:
            target_grid[coord] = HIT_COLOR
            result = "HIT"
        else:
            target_grid[coord] = MISS_COLOR

        hit_set.add(coord)
        self.shots_log.append((player, team, coord, result))
        return result

    def undo_shot(self):
        if not self.shots_log:
            return
        player, team, coord, result = self.shots_log.pop()
        hit_set = self.hits_alpha if team == "Alpha" else self.hits_omega
        grid = self.grid_omega if team == "Alpha" else self.grid_alpha
        if coord in hit_set:
            hit_set.remove(coord)
        grid[coord] = EMPTY_COLOR

    def get_hit_buyers(self):
        return [(player, team, coord) for (player, team, coord, result) in self.shots_log if result == "HIT"]

    def get_stats(self):
        player_stats = {}
        team_stats = {"Alpha": {"shots": 0, "hits": 0, "misses": 0}, "Omega": {"shots": 0, "hits": 0, "misses": 0}}
        for player, team, coord, result in self.shots_log:
            if player not in player_stats:
                player_stats[player] = {"shots": 0, "hits": 0, "misses": 0}
            player_stats[player]["shots"] += 1
            team_stats[team]["shots"] += 1
            if result == "HIT":
                player_stats[player]["hits"] += 1
                team_stats[team]["hits"] += 1
            else:
                player_stats[player]["misses"] += 1
                team_stats[team]["misses"] += 1
        return player_stats, team_stats

class DisplayWindow(QtWidgets.QWidget):
    def __init__(self, game_state):
        super().__init__()
        self.setWindowTitle("Wasteland Grid Display")
        self.game_state = game_state
        self.setMinimumSize(GRID_SIZE * CELL_SIZE * 2 + 100, GRID_SIZE * CELL_SIZE + 40)
        self.show()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        width = self.width()
        height = self.height()
        grid_width = (width - 100) // 2
        grid_height = height - 40
        cell_size_x = grid_width // GRID_SIZE
        cell_size_y = grid_height // GRID_SIZE
        cell_size = min(cell_size_x, cell_size_y)
        for idx, (grid, color_base, offset_x) in enumerate([
            (self.game_state.grid_alpha, ALPHA_COLOR, 20),
            (self.game_state.grid_omega, OMEGA_COLOR, grid_width + 60),
        ]):
            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    color = grid[(x, y)]
                    display_color = color_base if color == EMPTY_COLOR else color
                    rect = QtCore.QRect(offset_x + x * cell_size, 20 + y * cell_size, cell_size, cell_size)
                    painter.fillRect(rect, QtGui.QColor(display_color))
                    painter.drawRect(rect)

class ShipPlacementGrid(QtWidgets.QWidget):
    def __init__(self, game_state, team, update_callback, get_selected_ship, get_orientation):
        super().__init__()
        self.game_state = game_state
        self.team = team
        self.update_callback = update_callback
        self.get_selected_ship = get_selected_ship
        self.get_orientation = get_orientation
        self.setMinimumSize(GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE)
        self.setToolTip(f"Drag-and-drop to place/remove ships for {team}")

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        width = self.width()
        height = self.height()
        cell_size_x = width // GRID_SIZE
        cell_size_y = height // GRID_SIZE
        cell_size = min(cell_size_x, cell_size_y)
        color_base = ALPHA_COLOR if self.team == "Alpha" else OMEGA_COLOR
        ships = self.game_state.ships_alpha if self.team == "Alpha" else self.game_state.ships_omega
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                rect = QtCore.QRect(x * cell_size, y * cell_size, cell_size, cell_size)
                painter.fillRect(rect, QtGui.QColor(color_base))
                painter.drawRect(rect)
        for idx, (shape, origin, orientation) in enumerate(ships):
            color = SHIP_COLORS[idx % len(SHIP_COLORS)]
            for dx, dy in shape:
                if orientation == 0:
                    x, y = origin[0] + dx, origin[1] + dy
                else:
                    x, y = origin[0] + dy, origin[1] - dx
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    rect = QtCore.QRect(x * cell_size, y * cell_size, cell_size, cell_size)
                    painter.fillRect(rect, QtGui.QColor(color))
                    painter.drawRect(rect)

    def mousePressEvent(self, event):
        width = self.width()
        height = self.height()
        cell_size_x = width // GRID_SIZE
        cell_size_y = height // GRID_SIZE
        cell_size = min(cell_size_x, cell_size_y)
        x = event.x() // cell_size
        y = event.y() // cell_size
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            coord = (x, y)
            if self.game_state.remove_ship_at(self.team, coord):
                self.update()
                self.update_callback()
                return
            shape = self.get_selected_ship()
            orientation = self.get_orientation()
            if shape and self.game_state.can_place_ship(self.team, shape, coord, orientation):
                self.game_state.add_ship(self.team, shape, coord, orientation)
                self.update()
                self.update_callback()

class StatsPanel(QtWidgets.QWidget):
    def __init__(self, game_state):
        super().__init__()
        self.game_state = game_state
        self.setWindowTitle("Advanced Stats")
        self.setGeometry(100, 100, 400, 400)
        self.text = QtWidgets.QTextEdit(self)
        self.text.setGeometry(10, 10, 380, 380)
        self.text.setReadOnly(True)
        self.update_stats()
        self.show()

    def update_stats(self):
        player_stats, team_stats = self.game_state.get_stats()
        lines = ["TEAM STATS:"]
        for team, stats in team_stats.items():
            acc = (stats["hits"] / stats["shots"] * 100) if stats["shots"] else 0
            lines.append(f"{team}: Shots={stats['shots']} Hits={stats['hits']} Misses={stats['misses']} Acc={acc:.1f}%")
        lines.append("")
        lines.append("PLAYER STATS:")
        for player, stats in player_stats.items():
            acc = (stats["hits"] / stats["shots"] * 100) if stats["shots"] else 0
            lines.append(f"{player}: Shots={stats['shots']} Hits={stats['hits']} Misses={stats['misses']} Acc={acc:.1f}%")
        self.text.setText("\n".join(lines))

class LeaderboardPanel(QtWidgets.QWidget):
    def __init__(self, game_state):
        super().__init__()
        self.game_state = game_state
        self.setWindowTitle("Leaderboard")
        self.setGeometry(150, 150, 400, 400)
        self.text = QtWidgets.QTextEdit(self)
        self.text.setGeometry(10, 10, 380, 380)
        self.text.setReadOnly(True)
        self.update_leaderboard()
        self.show()

    def update_leaderboard(self):
        player_stats, _ = self.game_state.get_stats()
        leaderboard = sorted(player_stats.items(), key=lambda x: (-x[1]["hits"], -x[1]["shots"]))
        lines = ["LEADERBOARD (by hits, then shots):"]
        for player, stats in leaderboard:
            acc = (stats["hits"] / stats["shots"] * 100) if stats["shots"] else 0
            lines.append(f"{player}: Hits={stats['hits']} Shots={stats['shots']} Acc={acc:.1f}%")
        self.text.setText("\n".join(lines))

class ControlWindow(QtWidgets.QWidget):
    def __init__(self, game_state, display_window):
        super().__init__()
        self.setWindowTitle("Wasteland GM Control Panel")
        self.game_state = game_state
        self.display_window = display_window
        self.stats_panel = None
        self.leaderboard_panel = None
        self.selected_ship_idx = 0
        self.orientation = 0  # 0: horizontal, 1: vertical/rotated
        self.initUI()

    def initUI(self):
        # --- Top: Shot Controls ---
        shot_layout = QtWidgets.QHBoxLayout()
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Player Name")
        self.coord_input = QtWidgets.QLineEdit()
        self.coord_input.setPlaceholderText("Enter Coordinate (e.g., B4)")
        self.team_box = QtWidgets.QComboBox()
        self.team_box.addItems(["Alpha", "Omega"])
        self.fire_btn = QtWidgets.QPushButton("FIRE!")
        self.fire_btn.clicked.connect(self.fire_shot)
        self.undo_btn = QtWidgets.QPushButton("Undo")
        self.undo_btn.clicked.connect(self.undo_shot)
        self.reset_btn = QtWidgets.QPushButton("Reset Game")
        self.reset_btn.clicked.connect(self.reset_game)
        shot_layout.addWidget(self.name_input)
        shot_layout.addWidget(self.coord_input)
        shot_layout.addWidget(self.team_box)
        shot_layout.addWidget(self.fire_btn)
        shot_layout.addWidget(self.undo_btn)
        shot_layout.addWidget(self.reset_btn)

        # --- Ship Placement Controls ---
        ship_layout = QtWidgets.QHBoxLayout()
        self.ship_select = QtWidgets.QComboBox()
        for name, _ in SHIP_SHAPES:
            self.ship_select.addItem(name)
        self.ship_select.currentIndexChanged.connect(self.set_ship_idx)
        self.rotate_btn = QtWidgets.QPushButton("Rotate Ship")
        self.rotate_btn.clicked.connect(self.rotate_ship)
        self.ship_team = QtWidgets.QComboBox()
        self.ship_team.addItems(["Alpha", "Omega"])
        self.place_btn = QtWidgets.QPushButton("Place Ship (Text)")
        self.place_btn.clicked.connect(self.place_ship_text)
        self.ship_entry = QtWidgets.QLineEdit()
        self.ship_entry.setPlaceholderText("Set ship origin: A1")
        ship_layout.addWidget(self.ship_select)
        ship_layout.addWidget(self.rotate_btn)
        ship_layout.addWidget(self.ship_team)
        ship_layout.addWidget(self.place_btn)
        ship_layout.addWidget(self.ship_entry)

        # --- Game/Stats Controls ---
        game_layout = QtWidgets.QHBoxLayout()
        self.save_log_btn = QtWidgets.QPushButton("Save Log")
        self.save_log_btn.clicked.connect(self.save_log)
        self.export_hit_btn = QtWidgets.QPushButton("Export HIT Buyers")
        self.export_hit_btn.clicked.connect(self.export_hit_buyers)
        self.alpha_win_btn = QtWidgets.QPushButton("Alpha Wins")
        self.alpha_win_btn.clicked.connect(self.alpha_win)
        self.omega_win_btn = QtWidgets.QPushButton("Omega Wins")
        self.omega_win_btn.clicked.connect(self.omega_win)
        self.win_label = QtWidgets.QLabel()
        self.update_win_label()
        self.stats_btn = QtWidgets.QPushButton("Show Advanced Stats")
        self.stats_btn.clicked.connect(self.toggle_stats)
        self.leaderboard_btn = QtWidgets.QPushButton("Show Leaderboard")
        self.leaderboard_btn.clicked.connect(self.toggle_leaderboard)
        game_layout.addWidget(self.save_log_btn)
        game_layout.addWidget(self.export_hit_btn)
        game_layout.addWidget(self.alpha_win_btn)
        game_layout.addWidget(self.omega_win_btn)
        game_layout.addWidget(self.win_label)
        game_layout.addWidget(self.stats_btn)
        game_layout.addWidget(self.leaderboard_btn)

        # --- Log ---
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(200)

        # --- Ship Grids ---
        grid_layout = QtWidgets.QVBoxLayout()
        self.alpha_label = QtWidgets.QLabel("Alpha Ship Grid")
        self.alpha_grid = ShipPlacementGrid(self.game_state, "Alpha", self.update_grids, self.get_selected_ship, self.get_orientation)
        self.omega_label = QtWidgets.QLabel("Omega Ship Grid")
        self.omega_grid = ShipPlacementGrid(self.game_state, "Omega", self.update_grids, self.get_selected_ship, self.get_orientation)
        grid_layout.addWidget(self.alpha_label)
        grid_layout.addWidget(self.alpha_grid)
        grid_layout.addWidget(self.omega_label)
        grid_layout.addWidget(self.omega_grid)
        grid_layout.setStretch(1, 1)
        grid_layout.setStretch(3, 1)

        # --- Main Layout ---
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addLayout(shot_layout)
        left_layout.addLayout(ship_layout)
        left_layout.addLayout(game_layout)
        left_layout.addWidget(self.log_box, stretch=1)

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.addLayout(left_layout, stretch=2)
        main_layout.addLayout(grid_layout, stretch=1)
        self.setLayout(main_layout)
        self.show()

    def set_ship_idx(self, idx):
        self.selected_ship_idx = idx

    def rotate_ship(self):
        self.orientation = (self.orientation + 1) % 2
        self.update_grids()

    def get_selected_ship(self):
        return SHIP_SHAPES[self.selected_ship_idx][1]

    def get_orientation(self):
        return self.orientation

    def update_grids(self):
        self.alpha_grid.update()
        self.omega_grid.update()

    def update_win_label(self):
        self.win_label.setText(f"A: {self.game_state.alpha_wins} | O: {self.game_state.omega_wins}")

    def coord_from_text(self, text):
        try:
            col = string.ascii_uppercase.index(text[0])
            row = int(text[1:]) - 1
            if not (0 <= col < GRID_SIZE and 0 <= row < GRID_SIZE):
                raise ValueError
            return (col, row)
        except:
            return None

    def place_ship_text(self):
        origin_text = self.ship_entry.text().strip().upper()
        team = self.ship_team.currentText()
        shape = self.get_selected_ship()
        orientation = self.get_orientation()
        origin = self.coord_from_text(origin_text)
        if not origin:
            self.log_box.append("Invalid origin coordinate format.")
            return
        if self.game_state.can_place_ship(team, shape, origin, orientation):
            self.game_state.add_ship(team, shape, origin, orientation)
            self.update_grids()
            self.log_box.append(f"{team} ship placed at {origin_text} ({self.ship_select.currentText()})")
        else:
            self.log_box.append("Invalid ship placement (overlap or out of bounds).")

    def fire_shot(self):
        player = self.name_input.text().strip()
        coord_text = self.coord_input.text().strip().upper()
        team = self.team_box.currentText()

        if not player or not coord_text:
            self.log_box.append("Enter both name and coordinate!")
            return

        coord = self.coord_from_text(coord_text)
        if not coord:
            self.log_box.append("Invalid coordinate format.")
            return

        result = self.game_state.process_shot(team, coord, player)
        if result:
            self.display_window.update()
            self.log_box.append(f"{player} ({team}) fired at {coord_text}: {result}")
            if result == "HIT":
                QtWidgets.QMessageBox.information(self, "HIT!", f"{player} scored a HIT!\nAssign a Wasteland reward manually.")
            if self.stats_panel:
                self.stats_panel.update_stats()
            if self.leaderboard_panel:
                self.leaderboard_panel.update_leaderboard()
        else:
            self.log_box.append("Coordinate already targeted.")

    def undo_shot(self):
        self.game_state.undo_shot()
        self.display_window.update()
        self.log_box.append("Last shot undone.")
        if self.stats_panel:
            self.stats_panel.update_stats()
        if self.leaderboard_panel:
            self.leaderboard_panel.update_leaderboard()

    def reset_game(self):
        self.game_state.reset()
        self.display_window.update()
        self.log_box.clear()
        self.log_box.append("Game reset. Place ships to begin.")
        self.update_grids()
        if self.stats_panel:
            self.stats_panel.update_stats()
        if self.leaderboard_panel:
            self.leaderboard_panel.update_leaderboard()

    def save_log(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Log", "battleship_log.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Player", "Team", "Coordinate", "Result"])
                for player, team, coord, result in self.game_state.shots_log:
                    coord_str = f"{string.ascii_uppercase[coord[0]]}{coord[1]+1}"
                    writer.writerow([player, team, coord_str, result])
            self.log_box.append(f"Log saved to {path}")

    def export_hit_buyers(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export HIT Buyers", "hit_buyers.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Player", "Team", "Coordinate"])
                for player, team, coord in self.game_state.get_hit_buyers():
                    coord_str = f"{string.ascii_uppercase[coord[0]]}{coord[1]+1}"
                    writer.writerow([player, team, coord_str])
            self.log_box.append(f"HIT buyers exported to {path}")

    def alpha_win(self):
        self.game_state.alpha_wins += 1
        self.update_win_label()
        self.log_box.append("Alpha team wins! Game over.")
        if self.stats_panel:
            self.stats_panel.update_stats()
        if self.leaderboard_panel:
            self.leaderboard_panel.update_leaderboard()

    def omega_win(self):
        self.game_state.omega_wins += 1
        self.update_win_label()
        self.log_box.append("Omega team wins! Game over.")
        if self.stats_panel:
            self.stats_panel.update_stats()
        if self.leaderboard_panel:
            self.leaderboard_panel.update_leaderboard()

    def toggle_stats(self):
        if self.stats_panel and self.stats_panel.isVisible():
            self.stats_panel.close()
            self.stats_panel = None
        else:
            self.stats_panel = StatsPanel(self.game_state)
            self.stats_panel.show()

    def toggle_leaderboard(self):
        if self.leaderboard_panel and self.leaderboard_panel.isVisible():
            self.leaderboard_panel.close()
            self.leaderboard_panel = None
        else:
            self.leaderboard_panel = LeaderboardPanel(self.game_state)
            self.leaderboard_panel.show()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    sys.exit(app.exec_()) 