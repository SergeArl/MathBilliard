from PyQt5.QtGui import QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter
from BorderMolecules import Border, Molecule, Object
from balls import Ball
import math


class Dumbbell(Molecule):
    def set_balls_v(self):
        print("dumbb. set v")
        dx = (self.balls[1].x - self.balls[0].x)
        dy = (self.balls[1].y - self.balls[0].y)
        
        dp = self.mu * ((self.balls[1].v_x - self.balls[0].v_x) * dx + (self.balls[1].v_y - self.balls[0].v_y) * dy) / (self.d * self.d )
        self.balls[1].v_x -= dp * dx / self.balls[1].m
        self.balls[1].v_y -= dp * dy / self.balls[1].m
        self.balls[0].v_x += dp * dx / self.balls[0].m
        self.balls[0].v_y += dp * dy / self.balls[0].m

        self.v_x = (self.balls[0].m * self.balls[0].v_x + self.balls[1].m * self.balls[1].v_x) / (self.balls[0].m + self.balls[1].m)
        self.v_y = (self.balls[0].m * self.balls[0].v_y + self.balls[1].m * self.balls[1].v_y) / (self.balls[0].m + self.balls[1].m)

        self.Lz = self.mu * ( dy * (self.balls[1].v_x - self.balls[0].v_x) - dx * (self.balls[1].v_y - self.balls[0].v_y) )
        print("dp, Lz:", dp, self.Lz)


    def set_sin_cos(self, dt: float):
        dphi = dt * self.Lz / self.I
        print("dphi", dphi)
        self.dcos = math.cos(dphi)
        self.dsin = math.sin(dphi)
        self.moving = True

    def __init__(self, ball0: Ball, ball1: Ball, color_arrow=Qt.gray, teflon=True, trace=False):
        self.balls = [ball0, ball1]
        self.mu = ball0.m * ball1.m / (ball0.m + ball1.m)
        dx, dy = ball0.x - ball1.x, ball0.y - ball1.y
        d2 = dx * dx + dy * dy
        self.d = d2 ** (1/2)
        self.I = self.mu * d2
        cm_x, cm_y = (ball0.m * ball0.x + ball1.m * ball1.x) / (ball0.m + ball1.m), (ball0.m * ball0.y + ball1.m * ball1.y) / (ball0.m + ball1.m)
        #print("dumbbell base class...") 
        super().__init__(cm_x, cm_y, trace=trace)
        self.dcos = 1.
        self.dsin = 0.
        self.Lz = 0.
        self.set_balls_v()
        self.moving = True
        self.color_arrow = color_arrow

    def move(self, dt: float, add_trace=False, g=0., trace_length=50):
        # print("Dmbbll move", self.x, "moving", self.moving) 
        if not self.moving:
            self.set_sin_cos(dt)
        
        super().move(dt, add_trace, g, trace_length)
        
        c1 =  self.mu / self.balls[0].m
        c2 =  self.mu / self.balls[1].m
        
        dx = self.balls[1].x - self.balls[0].x
        dy = self.balls[1].y - self.balls[0].y
        # dphi = dt * self.Lz / self.I
        #print("  Lz = ", self.Lz, "  m1 = ", self.balls[0].m, "  m2 = ", self.balls[1].m,  "  d = ", self.d, "   c1 = ", c1, "  c2 = ", c2, "  phi1 = ", dphi1, "   phi2 = ", dphi2)
        self.balls[0].x = self.x - c1 * (dx * self.dcos + dy * self.dsin)
        self.balls[0].y = self.y - c1 * (-dx * self.dsin + dy * self.dcos)
        self.balls[1].x = self.x + c2 * (dx * self.dcos + dy * self.dsin)
        self.balls[1].y = self.y + c2 * (-dx * self.dsin + dy * self.dcos)

        dx = (self.balls[1].x - self.balls[0].x)
        dy = (self.balls[1].y - self.balls[0].y)
        self.balls[0].v_x = self.v_x - c1 * dy * self.Lz / self.I
        self.balls[0].v_y = self.v_y + c1 * dx * self.Lz / self.I
        self.balls[1].v_x = self.v_x + c2 * dy * self.Lz / self.I
        self.balls[1].v_y = self.v_y - c2 * dx * self.Lz / self.I
        # print("end move")

    def touch(self, other: Object) -> bool:
        #print("ball0 res", self.balls[0].touch(other))
        #print("ball1 res", self.balls[1].touch(other))
        ret = self.balls[0].touch(other) or self.balls[1].touch(other)
        if ret:
            print("Dumbbell touch", ret)
            self.moving = False
        return ret

    def reflect(self, other: Object):
        print("Dumbbell reflect")
        self.set_balls_v()
        self.moving = True

    def get_bounds(self) -> tuple:
        bnd0 = self.balls[0].get_bounds()
        bnd1 = self.balls[1].get_bounds()
        return (min([bnd0[0], bnd1[0]]), min([bnd0[1], bnd1[1]]), max([bnd0[2], bnd1[2]]), max([bnd0[3], bnd1[3]]))

    def M(self) -> float:
        return self.balls[0].m + self.balls[1].m

    def W_r(self) -> float:
        return self.Lz * self.Lz / self.I / 2 

    def W(self) -> float:
        return self.W_x() + self.W_y() + self.W_r()

    def draw(self, painter: QPainter):
        # print("Dumbell draw start")
        super().draw(painter)
        self.balls[0].draw(painter)
        self.balls[1].draw(painter)

    def draw_velocity(self, painter: QPainter, scale=0.5):
        print("v_draw start")
        super().draw_velocity(painter, scale)
        self.balls[0].draw_velocity(painter, scale)
        self.balls[1].draw_velocity(painter, scale)
        

    
    

            
