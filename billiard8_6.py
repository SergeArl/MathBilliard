import sys
import math
import time
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QApplication,
    QLabel, QFormLayout # , QMainWindow
)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QPointF, QTimer
# for plots + time 
import numpy as np

from GraphMenu import ParamViewer, HistogramViewer, PlotViewer, RightMenu
from BorderMolecules import Border, Molecule, Object, SpatialGrid
from balls import Ball
from dumbbells import Dumbbell


# Constants
TRACE_FREQUENCY = 6
GRAPH_FREQUENCY = 100
BORDER_WIDTH = 50
TRACE_LENGTH = 2500


class Envelope(QWidget):
    def __init__(self, points, molecules: list[Molecule], sort_vertex=False, trace_length=TRACE_LENGTH, stack_size=100, arrow_scale=1/2):
        super().__init__()
        self.setWindowTitle("Billiard 8.5  https://t.me/SergeArl")

        self.arrow_scale = arrow_scale
        
        if len(points) > 0:
            self.setGeometry(int(min([p[0] for p in points])) - BORDER_WIDTH, int(min([p[1] for p in points])) - BORDER_WIDTH,
                             int(max([p[0] for p in points])) + BORDER_WIDTH, int(max([p[1] for p in points])) + BORDER_WIDTH )
            points = [QPointF(*p) for p in points]
            if sort_vertex:
                cx, cy = self.width() / 2, self.height() / 2  # Center of the window
                points = sorted(points, key=lambda p: math.atan2(p.y() - cy, p.x() - cx))
            self.borders = [Border(points[i], points[(i + 1) % len(points)], stack_size=stack_size) for i in range(len(points))]
        else:
            self.borders = []
            
        self.molecules = molecules    
        # ==== cell size calculation ========
        # ("grid...")
        self.grid = SpatialGrid(self.width(), self.height(), self.cell_size())

        # ==== moving parameters =========
        self.is_running = False  # State toggle on click
        
        self.trace_count = 0
        self.trace_length = trace_length
        self.dt = 0.05  # default value of dt, specify in start_moving(dt)
        self.g = 0.
        self.skip_draw_count = 0
        self.skip_draw = 1
        self.timer = QTimer()
        # =========== for buttons and graphics =========
        # print("menu...")
        self.right_menu = RightMenu(self)
        
        self.param_viewer = None
        self.histogram_viewer = None
        # self.graph_counter = 0
        self.plot_viewer = None       # PlotViewer(100, "test", lambda: math.sin(1), (0, 500), (-2,2))
        self.file_number = 0
        
        # =========== temporary for timing =============
        self.time_moving = 0.
        self.time_grid = 0.
        # self.time_check = 0.
        self.time_reflect = 0.
        self.time_drawing = 0.
        # ==============================================
        self.show()

    def cell_size(self):
        if len(self.molecules) > 0:
            bounds = [molecule.get_bounds() for molecule in self.molecules]
            average_x = 2 * sum([bnd[2] - bnd[0] for bnd in bounds]) / len(self.molecules)
            average_y = 2 * sum([bnd[3] - bnd[1] for bnd in bounds]) / len(self.molecules)
            return max([(self.width() * self.height() / len(self.molecules)) ** (1/2), 2 * average_x, 2 * average_y])
        else:
            return min([self.width(), self.height()])

    def start_moving(self, dt: float, g=0., skip_draw = 1):
        self.g = g
        self.dt = dt
        self.skip_draw = skip_draw
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(int(dt*1000))  # ms

    def update_simulation(self):
        if not self.is_running:
            return
        self.trace_count = (self.trace_count + 1) % TRACE_FREQUENCY
        add_trace = True if self.trace_count == 0 else False

        # 1st timer
        # print("first timer")
        time_moving_start = time.perf_counter()
        for molecule in self.molecules:
            molecule.move(self.dt, add_trace, self.g, self.trace_length)
        self.time_moving += time.perf_counter() - time_moving_start

        # construct of grid
        # print("start grid")
        time_check_grid = time.perf_counter()
        self.grid.clear()
        for obj in self.molecules + self.borders:
            self.grid.add_object(obj)
        collisions = self.grid.get_possible_collisions()
        touch_objects = []
        # print("start grid_check len = ", len(collisions))
        for pair in collisions:
            if pair[0].touch(pair[1]):
                    touch_objects.append(pair)
        self.time_grid += time.perf_counter() - time_check_grid
        
        time_reflect_start = time.perf_counter()
        [pair[0].reflect(pair[1]) for pair in touch_objects]
        self.time_reflect += time.perf_counter() - time_reflect_start
        # print("borders next")
        for brd in self.borders:
            brd.next_time(self.dt)
        # print("drawing...")
        # update parameters and graphics    
        self.update_presentation()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw borders
        time_drawing_start = time.perf_counter()
        for border in self.borders:
            border.draw(painter)

        # Draw molecules and possibly velocity arrows
        # print("draw molecules")
        for molecule in self.molecules:
            molecule.draw(painter)
            if not self.is_running:
                molecule.draw_velocity(painter, self.arrow_scale)
        self.time_drawing += time.perf_counter() - time_drawing_start

    def mousePressEvent(self, event):
        self.is_running = not self.is_running
        self.update()

    def set_geometry(self):
        bnd = [bord.get_bounds() for bord in self.borders]
        if len(bnd) == 0:
            bnd = [(0, 0, 0, 0)]       
        self.setGeometry(int(min([b[0] for b in bnd])) - BORDER_WIDTH, int(min([b[1] for b in bnd])),
                         int(max([b[2] for b in bnd])) + BORDER_WIDTH + self.right_menu.width(),
                         int(max([b[3] for b in bnd])) + BORDER_WIDTH)

    def add_param_button(self, label: str, param_funcs: list[tuple[str, callable]]):
        def on_click():
            if self.param_viewer is None:
                self.param_viewer = ParamViewer(parent=self, param_funcs=param_funcs)
            self.param_viewer.show()
            self.param_viewer.raise_()
        self.right_menu.add_button(label, on_click)
        self.set_geometry()

    def add_histogram_button(self, label: str, histogram_func: callable, skip=GRAPH_FREQUENCY):
        def on_click():
            if self.histogram_viewer is None:
                self.histogram_viewer = HistogramViewer(self, label, histogram_func, skip)
            self.histogram_viewer.raise_it()
        self.right_menu.add_button(label, on_click)
        self.set_geometry()
        
    def add_plot_button(self, label: str, plot_funcs: list[tuple[str, callable]], t_interval=(0,100), func_interval=(-100, 10**4), step=20):
        num_points = int((t_interval[1] - t_interval[0]) / step / self.dt)
        def on_click():
            if self.plot_viewer is None:
                # (self, win: QWidget, num_points: int, label: str, function: callable, t_interval: tuple, func_interval: tuple, step=1)
                self.plot_viewer = PlotViewer(self, num_points, label, plot_funcs, t_interval, func_interval, step)
            self.plot_viewer.raise_it()
        self.right_menu.add_button(label, on_click)
        self.set_geometry()
        
    def update_presentation(self):
        # print("start update")
        self.skip_draw_count += 1
        if self.skip_draw_count >= self.skip_draw:
            self.skip_draw_count = 0
            self.update()
            # parameters and graph output        
            if self.param_viewer:
                self.param_viewer.update_parameters()
                
        if self.plot_viewer:
            self.plot_viewer.update(self.dt)
        if self.histogram_viewer:
            self.histogram_viewer.update_distribution()
        
    def add_save_button(self, file_name: str, file_number=0):
        self.file_number = file_number
        def save_to_file():
            self.is_running = False
            # print("file number:", self.file_number)
            with open(file_name + str(self.file_number) + ".txt", 'w') as file:
                for bord in self.borders:
                    red, green, blue, a = QColor(bord.color).getRgb()
                    file.write(f"Border {red} {green} {blue} {a} {int(bord.teflon)} {bord.p1.x()} {bord.p1.y()} {bord.p2.x()} {bord.p2.y()} {bord.stack_size}\n")
                for mol in self.molecules:
                    kind = type(mol).__name__
                    red, green, blue, a = QColor(mol.color).getRgb()
                    base = f"{red} {green} {blue} {a} {int(mol.teflon)} {mol.x} {mol.y} {mol.v_x} {mol.v_y} {int(mol.trace)}"
                    
                    if kind == "Ball":
                        file.write(f"Ball {base} {mol.m} {mol.r}\n")
                    elif kind == "Dummbell":
                        file.write(f"Dummbell {base} {m.d}\n")
                    else:
                        file.write(f"Molecule {base}\n")
            self.file_number += 1
            sender = self.sender()  # Get the button that sent the signal
            self.update()
            if sender:
                sender.setText("Save " + file_name + str(self.file_number))  # Change the button's label
                
        # print(file_name + str(self.file_number) + ".txt")
        self.right_menu.add_button("Save" + file_name + str(self.file_number), save_to_file)
        self.set_geometry()

    def load_from_file(self, file_name: str):
        self.is_running = False
        self.borders.clear()
        self.molecules.clear()
        with open(file_name + ".txt", 'r') as file:
            for line in file:
                kind, red, green, blue, a, teflon, *other = line.strip().split()
                clr = QColor(int(red), int(green), int(blue), int(a))
                
                if kind == "Border":
                    x1, y1, x2, y2, stack_size = other
                    self.borders.append(Border(QPointF(int(float(x1)), int(float(y1))), QPointF(int(float(x2)), int(float(y2))), \
                                                   clr, teflon=bool(int(teflon)), stack_size=int(stack_size)))
                elif kind == "Ball":
                    x, y, v_x, v_y, trace, m, r = other
                    self.molecules.append(Ball(float(m), float(r), float(x), float(y),
                                                       float(v_x), float(v_y), clr, bool(int(teflon)), bool(int(trace))))
                elif kind == "Dummbell":
                    pass
                    
        self.set_geometry()
        self.grid = SpatialGrid(self.width(), self.height(), self.cell_size())
        self.update()
        
    # def add_load_button(self, file_name: str):
        
    #     self.right_menu.add_button("Load" + file_name, lambda: self.load_from_file(file_name))
    #     self.set_geometry()
        

if __name__ == '__main__':
            
    app = QApplication(sys.argv)
    pts = [(50, 50), (1700, 50), (1700, 1100), (50, 1100)]

    mlcls = [
         Ball(30, 60, 400, 450, 60, -15, color=Qt.green, trace=True),
         Ball(70, 80, 550, 450, -45, 5, color=Qt.blue, trace=True),
         Ball(70, 80, 750, 450, 30, 4, color=Qt.blue, trace=True),
         Ball(m=30, r=60, x=900, y=450, v_x=-40, v_y=-20, color=Qt.green, trace=True)
    ]
    
    window = Envelope(pts, mlcls)
    
    window.add_param_button(
            label="Parameters",
            param_funcs=[
                ("move time", lambda w: f'{w.time_moving:5.3}'),
                ("grid time", lambda w: f'{w.time_grid:.5}'),
                # ("check time", lambda w: f'{w.time_check:.5}'),
                ("reflect time", lambda w: f'{w.time_reflect:5.3}'),
                ("draw time", lambda w: f'{w.time_drawing:5.4}')
            ]
        )

    window.add_save_button("FourBalls")
    
    window.start_moving(dt=0.03, g=10, skip_draw=2)
    sys.exit(app.exec_())
