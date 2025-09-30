import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from balls import Ball
from dumbbells import Dumbbell
from billiard8_6 import Envelope

GRAVITY = 10
def reverse_v(win: Envelope):
    for molecule in win.molecules:
        molecule.v_x *= -1
        molecule.v_y *= -1
    win.update()


app = QApplication(sys.argv)
    
window = Envelope([], [])
window.load_from_file("TwoBallons2_")

window.add_param_button(
        label="Parameters",
        param_funcs=[
            ("move time", lambda window: f'{window.time_moving:5.3}'),
            ("grid time", lambda window: f'{window.time_grid:.5}'),
            ("reflect time", lambda window: f'{window.time_reflect:5.3}'),
            ("draw time", lambda window: f'{window.time_drawing:5.4}')
        ]
    )
window.add_save_button("TwoBallons", file_number=4)
window.add_plot_button("Pressure", 
                       [
                           ("top left", lambda w: w.borders[0].get_pressure()),
                           ("bottom left", lambda w: w.borders[10].get_pressure()),
                           ("top right", lambda w: w.borders[4].get_pressure()),
                           ("bottom right", lambda w: w.borders[6].get_pressure())
                       ], func_interval=(0,150), t_interval=(0,200))
window.right_menu.add_button("Reverse", lambda: reverse_v(window))
window.add_histogram_button(label = "Energy", histogram_func=lambda mol: mol.W()
                            # - mol.M() * mol.y * GRAVITY
                            , skip=20)

window.start_moving(dt=0.02, g=10, skip_draw=2)
sys.exit(app.exec_())
