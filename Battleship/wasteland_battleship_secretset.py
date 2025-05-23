import sys, random, string, csv
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import QCoreApplication

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

    def randomize_ships(self, team, ship_indices=None):
        # ship_indices: list of indices in SHIP_SHAPES to randomize, or None for all
        if team == "Alpha":
            self.ships_alpha = []
        else:
            self.ships_omega = []
        placed = set()
        indices = ship_indices if ship_indices is not None else list(range(len(SHIP_SHAPES)))
        for idx in indices:
            shape = SHIP_SHAPES[idx][1]
            for attempt in range(100):
                orientation = random.choice([0, 1])
                if orientation == 0:
                    max_x = GRID_SIZE - max(dx for dx, dy in shape)
                    max_y = GRID_SIZE - max(dy for dx, dy in shape)
                else:
                    max_x = GRID_SIZE - max(dy for dx, dy in shape)
                    max_y = GRID_SIZE - max(dx for dx, dy in shape)
                origin = (random.randint(0, max_x - 1), random.randint(0, max_y - 1))
                if self.can_place_ship(team, shape, origin, orientation):
                    self.add_ship(team, shape, origin, orientation)
                    break
        # After randomizing, update placed_coords
        if team == "Alpha":
            self.placed_coords_alpha = self.get_ship_coords("Alpha")
        else:
            self.placed_coords_omega = self.get_ship_coords("Omega")

class DisplayWindow(QtWidgets.QWidget):
    def __init__(self, game_state):
        super().__init__()
        self.setWindowTitle("Wasteland Grid Display")
        self.game_state = game_state
        # Remove setMinimumSize for full responsiveness
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.show()

    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        width = self.width()
        height = self.height()
        grid_width = width - 60
        grid_height = (height - 120) // 2
        cell_size_x = grid_width / GRID_SIZE
        cell_size_y = grid_height / GRID_SIZE
        cell_size = min(cell_size_x, cell_size_y)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        # Draw Alpha grid
        offset_y_alpha = 30
        # Draw column letters centered
        for x in range(GRID_SIZE):
            rect = QtCore.QRectF(40 + x * cell_size, offset_y_alpha - 24, cell_size, 20)
            painter.drawText(rect, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter, string.ascii_uppercase[x])
        # Draw row numbers (fixed)
        for y in range(GRID_SIZE):
            rect = QtCore.QRectF(0, offset_y_alpha + y * cell_size, 38, cell_size)
            painter.drawText(rect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight, str(y + 1))
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                color = self.game_state.grid_alpha[(x, y)]
                display_color = ALPHA_COLOR if color == EMPTY_COLOR else color
                rect = QtCore.QRectF(40 + x * cell_size, offset_y_alpha + y * cell_size, cell_size, cell_size)
                painter.fillRect(rect, QtGui.QColor(display_color))
                painter.drawRect(rect)
        # Draw Omega grid
        offset_y_omega = grid_height + 70
        font.setPointSize(14)
        painter.setFont(font)
        for x in range(GRID_SIZE):
            rect = QtCore.QRectF(40 + x * cell_size, offset_y_omega - 24, cell_size, 20)
            painter.drawText(rect, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter, string.ascii_uppercase[x])
        for y in range(GRID_SIZE):
            rect = QtCore.QRectF(0, offset_y_omega + y * cell_size, 38, cell_size)
            painter.drawText(rect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight, str(y + 1))
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                color = self.game_state.grid_omega[(x, y)]
                display_color = OMEGA_COLOR if color == EMPTY_COLOR else color
                rect = QtCore.QRectF(40 + x * cell_size, offset_y_omega + y * cell_size, cell_size, cell_size)
                painter.fillRect(rect, QtGui.QColor(display_color))
                painter.drawRect(rect)
        # Draw log line exactly between the two grids
        if self.game_state.shots_log:
            player, team, coord, result = self.game_state.shots_log[-1]
            coord_str = f"{string.ascii_uppercase[coord[0]]}{coord[1]+1}"
            log_line = f"{player} ({team}) fired at {coord_str}: {result}"
            # Calculate the space between the bottom of Alpha and top of Omega grid
            bottom_alpha = offset_y_alpha + cell_size * GRID_SIZE
            top_omega = offset_y_omega - 24  # top of Omega grid's column labels
            available_space = top_omega - bottom_alpha
            if available_space > 10:
                font.setPointSize(min(18, max(10, int(available_space * 0.5))))
                painter.setFont(font)
                painter.setPen(QtGui.QColor("black"))
                y_log = bottom_alpha + (available_space / 2) - 10
                painter.drawText(QtCore.QRectF(0, y_log, width, available_space), QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter, log_line)
        # Show HIT or MISS text only in the center of the Omega grid
        if self.game_state.shots_log:
            _, _, _, result = self.game_state.shots_log[-1]
            if result == "HIT" or result == "MISS":
                font.setPointSize(48)
                painter.setFont(font)
                painter.setPen(QtGui.QColor("red" if result == "HIT" else "blue"))
                # Center in Omega grid
                omega_grid_rect = QtCore.QRectF(40, offset_y_omega, cell_size * GRID_SIZE, cell_size * GRID_SIZE)
                painter.drawText(omega_grid_rect, QtCore.Qt.AlignCenter, result)
        painter.setPen(QtGui.QColor("black"))

class ShipPlacementGrid(QtWidgets.QWidget):
    def __init__(self, game_state, team, update_callback, get_selected_ship, get_orientation, control_window=None, hide_ships=True):
        super().__init__()
        self.game_state = game_state
        self.team = team
        self.update_callback = update_callback
        self.get_selected_ship = get_selected_ship
        self.get_orientation = get_orientation
        self.control_window = control_window
        self.hide_ships = hide_ships
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setToolTip(f"Drag-and-drop to place/remove ships for {team}")

    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        width = self.width()
        height = self.height()
        cell_size_x = width / GRID_SIZE
        cell_size_y = height / GRID_SIZE
        cell_size = min(cell_size_x, cell_size_y)
        color_base = ALPHA_COLOR if self.team == "Alpha" else OMEGA_COLOR
        ships = self.game_state.ships_alpha if self.team == "Alpha" else self.game_state.ships_omega
        # GM vs Players mode: show ships only on GM's grid, hide on opponent's
        show_ships = True
        if self.control_window and getattr(self.control_window, 'gm_vs_players_mode', False):
            gm_team = self.control_window.gm_team_box.currentText()
            if self.team == gm_team:
                show_ships = True
            else:
                show_ships = False
        if show_ships:
            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    rect = QtCore.QRectF(x * cell_size, y * cell_size, cell_size, cell_size)
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
                        rect = QtCore.QRectF(x * cell_size, y * cell_size, cell_size, cell_size)
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
        self.orientation = 0  # 0: horizontal
        self.gm_vs_players_mode = False
        self.initUI()
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.setMaximumSize(screen.width(), screen.height())

    def initUI(self):
        # --- Status bar (define first so it's available for layout) ---
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.showMessage("Ready")
        # --- Menu bar (define next so it's available for layout) ---
        menu_bar = QtWidgets.QMenuBar()
        game_menu = menu_bar.addMenu("Game")
        new_action = QtGui.QAction("New Game", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.reset_game)
        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(QCoreApplication.quit)
        game_menu.addAction(new_action)
        game_menu.addAction(exit_action)
        help_menu = menu_bar.addMenu("Help")
        about_action = QtGui.QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # --- Shot Controls Group ---
        shot_group = QtWidgets.QGroupBox("Shot Controls")
        shot_layout = QtWidgets.QHBoxLayout()
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Player Name")
        self.name_input.setToolTip("Enter the player's name")
        self.coord_input = QtWidgets.QLineEdit()
        self.coord_input.setPlaceholderText("Enter Coordinate (e.g., B4)")
        self.coord_input.setToolTip("Enter the grid coordinate to fire at, e.g., B4")
        self.team_box = QtWidgets.QComboBox()
        self.team_box.addItems(["Alpha", "Omega"])
        self.team_box.setToolTip("Select the team to fire for")
        self.fire_btn = QtWidgets.QPushButton("FIRE!")
        self.fire_btn.setToolTip("Fire at the selected coordinate")
        self.fire_btn.clicked.connect(self.fire_shot)
        self.undo_btn = QtWidgets.QPushButton("Undo")
        self.undo_btn.setToolTip("Undo the last shot")
        self.undo_btn.clicked.connect(self.undo_shot)
        self.reset_btn = QtWidgets.QPushButton("Reset Game")
        self.reset_btn.setToolTip("Reset the game state")
        self.reset_btn.clicked.connect(self.reset_game)
        shot_layout.addWidget(self.name_input)
        shot_layout.addWidget(self.coord_input)
        shot_layout.addWidget(self.team_box)
        shot_layout.addWidget(self.fire_btn)
        shot_layout.addWidget(self.undo_btn)
        shot_layout.addWidget(self.reset_btn)
        shot_group.setLayout(shot_layout)

        # --- Ship Placement Group ---
        ship_group = QtWidgets.QGroupBox("Ship Placement")
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
        ship_group.setLayout(ship_layout)

        # --- Randomization Group ---
        rand_group = QtWidgets.QGroupBox("Randomization")
        rand_layout = QtWidgets.QHBoxLayout()
        self.randomize_all_btn = QtWidgets.QPushButton("Randomize All Ships (Both)")
        self.randomize_all_btn.clicked.connect(self.randomize_all_ships)
        self.randomize_alpha_btn = QtWidgets.QPushButton("Randomize Alpha")
        self.randomize_alpha_btn.clicked.connect(lambda: self.randomize_team("Alpha"))
        self.randomize_omega_btn = QtWidgets.QPushButton("Randomize Omega")
        self.randomize_omega_btn.clicked.connect(lambda: self.randomize_team("Omega"))
        self.randomize_selected_btn = QtWidgets.QPushButton("Randomize Selected Ship")
        self.randomize_selected_btn.clicked.connect(self.randomize_selected_ship)
        rand_layout.addWidget(self.randomize_all_btn)
        rand_layout.addWidget(self.randomize_alpha_btn)
        rand_layout.addWidget(self.randomize_omega_btn)
        rand_layout.addWidget(self.randomize_selected_btn)
        rand_group.setLayout(rand_layout)

        # --- Game/Stats Group ---
        game_group = QtWidgets.QGroupBox("Game / Stats")
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
        game_group.setLayout(game_layout)

        # --- GM vs Players Toggle and GM Team Selection ---
        self.gm_vs_players_btn = QtWidgets.QPushButton("GM vs Players Mode: OFF")
        self.gm_vs_players_btn.setCheckable(True)
        self.gm_vs_players_btn.setToolTip("Toggle GM vs Players mode. When ON, ships are hidden from GM.")
        self.gm_vs_players_btn.toggled.connect(self.toggle_gm_vs_players_mode)
        # GM Team selection dropdown
        self.gm_team_box = QtWidgets.QComboBox()
        self.gm_team_box.addItems(["Alpha", "Omega"])
        self.gm_team_box.setToolTip("Select which team the GM is playing as")
        self.gm_team_box.currentIndexChanged.connect(self.update_gm_team)
        gm_toggle_layout = QtWidgets.QHBoxLayout()
        gm_toggle_layout.addStretch(1)
        gm_toggle_layout.addWidget(self.gm_vs_players_btn)
        gm_toggle_layout.addWidget(QtWidgets.QLabel("GM Team:"))
        gm_toggle_layout.addWidget(self.gm_team_box)
        gm_toggle_layout.addStretch(1)
        gm_toggle_widget = QtWidgets.QWidget()
        gm_toggle_widget.setLayout(gm_toggle_layout)

        # --- Controls Area: Professional Layout ---
        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QVBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)

        # Row 0: Menu bar
        controls_layout.addWidget(menu_bar)

        # Row 1: Shot Controls (in QGroupBox)
        shot_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        controls_layout.addWidget(shot_group)

        # Row 2: Ship Placement (in QGroupBox)
        ship_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        controls_layout.addWidget(ship_group)

        # Row 3: Randomization (in QGroupBox)
        rand_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        controls_layout.addWidget(rand_group)

        # Row 4: Game/Stats (in QGroupBox)
        game_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        controls_layout.addWidget(game_group)

        # Row 5: GM vs Players toggle (in QGroupBox)
        gm_toggle_box = QtWidgets.QGroupBox("GM Mode")
        gm_toggle_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        gm_toggle_layout_outer = QtWidgets.QVBoxLayout()
        gm_toggle_layout_outer.addWidget(gm_toggle_widget)
        gm_toggle_box.setLayout(gm_toggle_layout_outer)
        controls_layout.addWidget(gm_toggle_box)

        # Row 6: Spacer
        controls_layout.addStretch(1)

        # Row 7: Status bar
        controls_layout.addWidget(self.status_bar)

        controls_widget.setLayout(controls_layout)
        controls_widget.setMinimumHeight(200)

        # Set consistent button width for all QPushButton in controls area
        min_btn_width = 120
        for group in [shot_group, ship_group, rand_group, game_group]:
            for btn in group.findChildren(QtWidgets.QPushButton):
                btn.setMinimumWidth(min_btn_width)

        # --- Log Box ---
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(100)
        self.log_box.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # --- Left Panel Splitter (vertical) ---
        left_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        left_splitter.addWidget(controls_widget)
        left_splitter.addWidget(self.log_box)
        left_splitter.setSizes([350, 150])
        left_splitter.setHandleWidth(10)
        left_splitter.setCollapsible(0, False)
        left_splitter.setCollapsible(1, False)
        left_panel = QtWidgets.QWidget()
        left_panel_layout = QtWidgets.QVBoxLayout()
        left_panel_layout.setContentsMargins(8, 8, 8, 8)
        left_panel_layout.setSpacing(0)
        left_panel_layout.addWidget(left_splitter)
        left_panel.setLayout(left_panel_layout)
        left_panel.setMinimumWidth(340)

        # --- Right Layout: dynamic grid display ---
        self.right_layout = QtWidgets.QVBoxLayout()
        self.grid_label = QtWidgets.QLabel()
        self.right_layout.addWidget(self.grid_label)
        # Containers for grid widgets
        self.grid_container = QtWidgets.QWidget()
        self.grid_container_layout = QtWidgets.QVBoxLayout()
        self.grid_container.setLayout(self.grid_container_layout)
        self.right_layout.addWidget(self.grid_container, stretch=1)
        self.right_panel = QtWidgets.QWidget()
        self.right_panel.setLayout(self.right_layout)
        self.right_panel.setMinimumWidth(340)

        # --- Main Layout: QSplitter for left/right ---
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([max(340, int(self.width() * 0.32)), max(700, int(self.width() * 0.7))])
        splitter.setHandleWidth(10)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        self.show()

        self.team_box.currentIndexChanged.connect(self.update_gm_vs_players_grid_hiding)
        self.alpha_grid = None
        self.omega_grid = None
        self.gm_grid = None
        self.opp_grid = None
        self.update_right_panel()  # Set initial grid(s)

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
        if self.gm_vs_players_mode:
            if self.gm_grid:
                self.gm_grid.hide_ships = False
                self.gm_grid.update()
            if hasattr(self, 'opp_grid') and self.opp_grid:
                self.opp_grid.hide_ships = True
                self.opp_grid.update()
        else:
            if self.alpha_grid:
                self.alpha_grid.hide_ships = False
                self.alpha_grid.update()
            if self.omega_grid:
                self.omega_grid.hide_ships = False
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

    def randomize_all_ships(self):
        self.game_state.randomize_ships("Alpha")
        self.game_state.randomize_ships("Omega")
        self.update_grids()
        self.log_box.append("All ships randomized for both teams.")

    def randomize_team(self, team):
        self.game_state.randomize_ships(team)
        self.update_grids()
        self.log_box.append(f"All ships randomized for {team}.")

    def randomize_selected_ship(self):
        team = self.ship_team.currentText()
        idx = self.ship_select.currentIndex()
        # Remove the selected ship from the team first
        ships = self.game_state.ships_alpha if team == "Alpha" else self.game_state.ships_omega
        if idx < len(ships):
            del ships[idx]
        self.game_state.randomize_ships(team, [idx])
        self.update_grids()
        self.log_box.append(f"Randomized {self.ship_select.currentText()} for {team}.")

    def show_about(self):
        QtWidgets.QMessageBox.about(self, "About", "Wasteland Battleship\nModernized PyQt5 Edition\n\nUpgraded UI/UX and resizable windows.")

    def toggle_gm_vs_players_mode(self, checked):
        self.gm_vs_players_mode = checked
        if checked:
            self.gm_vs_players_btn.setText("GM vs Players Mode: ON")
        else:
            self.gm_vs_players_btn.setText("GM vs Players Mode: OFF")
        self.update_right_panel()

    def update_right_panel(self):
        # Remove all widgets from grid_container
        for i in reversed(range(self.grid_container_layout.count())):
            widget = self.grid_container_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        # Remove reference grids
        self.alpha_grid = None
        self.omega_grid = None
        self.gm_grid = None
        self.opp_grid = None
        if self.gm_vs_players_mode:
            gm_team = self.gm_team_box.currentText()
            opp_team = "Omega" if gm_team == "Alpha" else "Alpha"
            self.grid_label.setText(f"{gm_team} (GM) and {opp_team} (Players) Ship Grids")
            # GM's team grid (ships visible)
            self.gm_grid = ShipPlacementGrid(self.game_state, gm_team, self.update_grids, self.get_selected_ship, self.get_orientation, self, hide_ships=False)
            self.gm_grid.setMinimumSize(300, 300)
            # Opponent's grid (ships hidden/blank)
            self.opp_grid = ShipPlacementGrid(self.game_state, opp_team, self.update_grids, self.get_selected_ship, self.get_orientation, self, hide_ships=True)
            self.opp_grid.setMinimumSize(300, 300)
            self.grid_container_layout.addWidget(QtWidgets.QLabel(f"{gm_team} Ship Grid (GM)"))
            self.grid_container_layout.addWidget(self.gm_grid)
            self.grid_container_layout.addWidget(QtWidgets.QLabel(f"{opp_team} Ship Grid (Players, Hidden)"))
            self.grid_container_layout.addWidget(self.opp_grid)
            self.update_gm_vs_players_grid_hiding()
        else:
            # Show both grids stacked, all ships visible
            self.grid_label.setText("Alpha and Omega Ship Grids")
            self.alpha_grid = ShipPlacementGrid(self.game_state, "Alpha", self.update_grids, self.get_selected_ship, self.get_orientation, self, hide_ships=False)
            self.omega_grid = ShipPlacementGrid(self.game_state, "Omega", self.update_grids, self.get_selected_ship, self.get_orientation, self, hide_ships=False)
            self.alpha_grid.setMinimumSize(300, 300)
            self.omega_grid.setMinimumSize(300, 300)
            self.grid_container_layout.addWidget(QtWidgets.QLabel("Alpha Ship Grid"))
            self.grid_container_layout.addWidget(self.alpha_grid)
            self.grid_container_layout.addWidget(QtWidgets.QLabel("Omega Ship Grid"))
            self.grid_container_layout.addWidget(self.omega_grid)
            self.update_grids()

    def update_gm_vs_players_grid_hiding(self):
        if self.gm_vs_players_mode:
            if not hasattr(self, 'gm_grid') or self.gm_grid is None or not hasattr(self, 'opp_grid') or self.opp_grid is None:
                return
            self.gm_grid.hide_ships = False
            self.gm_grid.update()
            self.opp_grid.hide_ships = True
            self.opp_grid.update()
        else:
            # Both grids visible, always show ships
            if self.alpha_grid:
                self.alpha_grid.hide_ships = False
                self.alpha_grid.update()
            if self.omega_grid:
                self.omega_grid.hide_ships = False
                self.omega_grid.update()

    def update_gm_team(self):
        # Called when GM team dropdown changes
        self.update_right_panel()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    state = GameState()
    display = DisplayWindow(state)
    control = ControlWindow(state, display)
    sys.exit(app.exec_()) 