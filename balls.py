from BorderMolecules import Border, Molecule
from PyQt5.QtGui import QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter


class Ball(Molecule):
    def __init__(self, m: float, r: float, x: float, y: float, v_x=0., v_y=0., color=Qt.blue, teflon=True, trace=False):
        super().__init__(x, y, v_x, v_y, color, teflon, trace)
        self.m = m
        self.r = r
        
    def get_bounds(self) -> tuple:
        # print("ball bound in")
        return (self.x - self.r, self.y - self.r, self.x + self.r, self.y + self.r)

    def M(self) -> float:
        return self.m

    """ moved in Molecula """
    # def P_x(self) -> float:
    #    return self.m * self.v_x

    # def P_y(self) -> float:
    #    return self.m * self.v_y

    # def W_x(self) -> float:
    #     return self.m/2 * self.v_x * self.v_x

    # def W_y(self) -> float:
    #     return self.m/2 * self.v_y * self.v_y

    def W_r(self) -> float:
        return 0

#    def W():                   # defined in Molecule
#        return W_x() + W_y() + W_r() 

    def draw(self, painter: QPainter):
        # print("Ball painter, x = ", self.x)
        super().draw(painter)

        # Ball appearance
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.black))
        painter.drawEllipse(QPointF(self.x, self.y), self.r, self.r)
        
        # Highlighted effect
        painter.setPen(QPen(self.color))
        painter.setBrush(QBrush(Qt.white))
        painter.drawEllipse(QPointF(self.x - self.r / 3, self.y - self.r / 3), self.r / 4, self.r / 4)
        
    def reflect_ball(self, other: 'Ball'):
        # solution of equations (V_x and V_y are new velocities):
        # safe of the momentum p_x: a.m a.v_x + b.m b.v_x = a.m a.V_x + b.m b.V_x
        # safe of the momentum p_y: a.m a.v_y + b.m b.v_y = a.m a.V_y + b.m b.V_y
        # safe of the energy: a.m/2 a.v_y**2 + b.m/2 b.v_y**2 = a.m/2 a.V_y**2 + b.m/2 b.V_y**2
        # safe of the rotation momentum: a.m (a.v_x dy - a.v_y dx) - b.m (b.v_x dy - b.v_y dx) =
        #                              = a.m (a.V_x dy - a.V_y dx) - b.m (b.V_x dy - b.V_y dx)
        dx2 = (self.x - other.x) * (self.x - other.x)
        dxy = (self.x - other.x) * (self.y - other.y)
        dy2 = (self.y - other.y) * (self.y - other.y)
        dist = (dx2 + dy2) * (self.m + other.m)

        if dist != 0:
            dvx = dx2 * (other.v_x - self.v_x) + dxy * (other.v_y - self.v_y)
            dvy = dxy * (other.v_x - self.v_x) + dy2 * (other.v_y - self.v_y)

            self.v_x += 2 * other.m * dvx / dist
            self.v_y += 2 * other.m * dvy / dist
            other.v_x -= 2 * self.m * dvx / dist
            other.v_y -= 2 * self.m * dvy / dist
        else:
            sum_m = self.m + other.m
            dvx = other.v_x - self.v_x
            dvy = other.v_y - self.v_y

            self.v_x += 2 * other.m * dvx / sum_m
            self.v_y += 2 * other.m * dvy / sum_m
            other.v_x -= 2 * self.m * dvx / sum_m
            other.v_y -= 2 * self.m * dvy / sum_m

    def reflect_border(self, other: Border):
        n = other.normal
        dot = self.v_x * n.x() + self.v_y * n.y()
        self.v_x -= 2 * dot * n.x()
        self.v_y -= 2 * dot * n.y()
        other.add_pressure(2 * self.m * dot * n.x(), 2 * self.m * dot * n.y())

    def touch(self, other) -> bool:
        # print("ball touch", self.x)
        # print("type", type(other).__name__)
        if isinstance(other, Ball):
            dx, dy = self.x - other.x, self.y - other.y
            sum_r = self.r + other.r
            if dx * dx + dy * dy <= sum_r * sum_r:
                if (self.teflon or other.teflon) and \
                        (other.v_x - self.v_x) * (other.x - self.x) + (other.v_y - self.v_y) * (other.y - self.y) > 0:
                    return False
                # === print("reflect", dx * dx + dy * dy, " < ", sum_r * sum_r)
                return True
            else:
                return False
        elif isinstance(other, Border):
            # Compute distance from ball center to border using the normal vector
            dx, dy = self.x - other.center.x(), self.y - other.center.y()
            distance = abs(dx * other.normal.x() + dy * other.normal.y())  # Projection onto normal
            distance_long = abs(dx * other.normal.y() - dy * other.normal.x())
            if distance <= self.r and distance_long <= other.length/2 + self.r:
                if (self.teflon or other.teflon) and self.v_x * other.normal.x() + self.v_y * other.normal.y() > 0:
                    return False
                return True
            else:
                return False
        else:
            print("ball touch other", type(other).__name__)
            return other.touch(self)

    def reflect(self, other):
        if isinstance(other, Ball):
            self.reflect_ball(other)
        elif isinstance(other, Border):
            self.reflect_border(other)
        else:
            return other.reflect(self)

