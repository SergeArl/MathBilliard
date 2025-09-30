from PyQt5.QtGui import QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QPointF
import math

ARROW_ANGLE = math.pi / 6


def draw_arrow(painter: QPainter, start: tuple, end: tuple, color=Qt.red, dangle=ARROW_ANGLE):
    # Draw  vector

    end_x, end_y = end[0], end[1]
    start_x, start_y = start[0], start[1]
    
    painter.setPen(QPen(color, 2))
    painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))

    # Draw arrowhead
    angle = math.atan2(end_y - start_y, end_x - start_x)
    arrow_size = 10     # size of arrow head
    dx = arrow_size * math.cos(angle + dangle)
    dy = arrow_size * math.sin(angle + dangle)
    painter.drawLine(QPointF(end_x, end_y), QPointF(end_x - dx, end_y - dy))

    dx = arrow_size * math.cos(angle - dangle)
    dy = arrow_size * math.sin(angle - dangle)
    painter.drawLine(QPointF(end_x, end_y), QPointF(end_x - dx, end_y - dy))


class Object:
    def __init__(self, color=Qt.gray, teflon=True):
        self.color = color
        self.teflon = teflon
        self.neighbours = []

    def touch(self, other):
        raise NotImplementedError

    def reflect(self, other):
        raise NotImplementedError

    def draw(self, painter):
        raise NotImplementedError

    def get_bounds(self) -> tuple:
        raise NotImplementedError


class Border(Object):
    def __init__(self, p1: QPointF, p2: QPointF, color=Qt.black, teflon=True, stack_size=100):
        super().__init__(color, teflon)
        self.p1, self.p2 = p1, p2
        self.center = QPointF((p2.x() + p1.x())/2, (p2.y() + p1.y())/2)
        # Compute normal vector
        dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
        self.length = (dx**2 + dy**2)**0.5
        self.normal = QPointF(-dy / self.length, dx / self.length)  # Perpendicular unit vector
        # pressure stack
        self.current_momentum = 0.
        self.pressure = [0]
        self.stack_size = stack_size

    def get_bounds(self) -> tuple:
        min_x, max_x = sorted([self.p1.x(), self.p2.x()])
        min_y, max_y = sorted([self.p1.y(), self.p2.y()])
        return (min_x, min_y, max_x, max_y)

    def add_pressure(self, p_x: float, p_y: float):
        self.current_momentum -= p_x * self.normal.x() + p_y * self.normal.y()

    def next_time(self, dt: float):
        # print("add press", self.current_momentum, dt, self.length) 
        self.pressure.append(self.current_momentum / dt / self.length)
        if len(self.pressure) > self.stack_size:  # limit history length
                self.pressure.pop(0)
        self.current_momentum = 0.
        # self.neighbours.clear()
        
    def get_pressure(self):
        return sum(self.pressure) / len(self.pressure) 

    def draw(self, painter):
        painter.setPen(QPen(self.color, 2))
        painter.drawLine(self.p1, self.p2)
        # === draw normal vector
        # middle = ((self.p1.x() + self.p2.x())/2, (self.p1.y() + self.p2.y())/2)
        # draw_arrow(painter, middle, (middle[0] + 40*self.normal.x(), middle[1] + 40*self.normal.y()))

    def touch(self, other) -> bool:
        # print(type(other))
        if isinstance(other, Border):
            return False
        else:
            return other.touch(self)

    def reflect(self, other) -> bool:
        # print(type(other))
        if isinstance(other, Border):
            return 
        else:
            other.reflect(self)


class Molecule(Object):
    def __init__(self, x: float, y: float, v_x=0., v_y=0., color=Qt.cyan, teflon=True, trace=False):
        super().__init__(color, teflon)
        self.x, self.y = x, y
        self.v_x, self.v_y = v_x, v_y
        self.trace = trace
        self.path = []  # store previous positions

    def move(self, dt: float, add_trace=False, g=0., trace_length=0):
        self.x += self.v_x * dt
        self.y += self.v_y * dt + g * dt*dt/2
        self.v_y += g * dt
        if self.trace and add_trace:
            self.path.append(QPointF(self.x, self.y))
            if len(self.path) > trace_length:  # limit history length
                self.path.pop(0)
        # self.neighbours.clear()

    def draw_velocity(self, painter: QPainter, scale=0.5):
        # print("draw velosity", type(self).__name__)
        end_x = self.x + self.v_x * scale
        end_y = self.y + self.v_y * scale
        draw_arrow(painter, (self.x, self.y), (end_x, end_y))

    def M(self) -> float:
        raise NotImplementedError

    def P_x(self) -> float:
        return self.M() * self.v_x

    def P_y(self) -> float:
        return self.M() * self.v_y
    
    def W_x(self) -> float:
        return self.M() * self.v_x * self.v_x / 2

    def W_y(self) -> float:
        return self.M() * self.v_y * self.v_y / 2

    def W_r(self) -> float:
        print("W_r in Molecule", type(self).__name__)
        raise NotImplementedError

    def W(self) -> float:
        return self.W_x() + self.W_y() + self.W_r()

    """ # is defined in Object mow 
    def touch(self, other):
        raise NotImplementedError

    def reflect(self, other):
        raise NotImplementedError
    """

    def draw(self, painter: QPainter):
        if self.trace:
            painter.setPen(QPen(self.color, 2))
            for segment in [list(pair) for pair in zip(self.path[::2], self.path[1::2])]:
                painter.drawLine(*segment)
        

""" === Spatial Grid === """
class SpatialGrid:
    def __init__(self, width, height, cell_size):
        self.cell_size = int(cell_size)
        # print("cell: ", cell_size)
        self.cols = int(int(width + cell_size - 1) // cell_size)
        self.rows = int(int(height + cell_size - 1) // cell_size)
        # print("rows, cols: ", self.rows, self.cols)
        self.grid = [[set() for _ in range(self.cols)] for _ in range(self.rows)]   # set

    def clear(self):
        for row in self.grid:
            for cell in row:
                cell.clear()

    def add_object(self, obj: Object):
        bounds = obj.get_bounds()
        # print(bounds)
        min_col = int(bounds[0]) // self.cell_size
        max_col = int(bounds[2]) // self.cell_size
        min_row = int(bounds[1]) // self.cell_size
        max_row = int(bounds[3]) // self.cell_size
        # print("from ", self.rows, self.cols, "rows: ", min_row, " ", max_row, " cols: ", min_col, " ", max_col)
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                if 0 <= row < self.rows and 0 <= col < self.cols:
                    # print("in ", self.grid[row][col])
                    self.grid[row][col].add(obj)                                    # set
        # print("inserted good")

    def get_possible_collisions(self):
        checked = set()
        collisions = []
        for row in self.grid:
            for cell0 in row:                                                        # set  30/80
                cell = list(cell0)
                for i in range(len(cell)):
                    for j in range(i + 1, len(cell)):
                        a, b = cell[i], cell[j]
                        if (id(a), id(b)) not in checked and (id(b), id(a)) not in checked:
                            checked.add((id(a), id(b)))
                            collisions.append((a, b))
        return collisions
