""" Output of parameters """
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QLabel, QFormLayout
)
from PyQt5.QtCore import Qt
import numpy as np
import matplotlib.pyplot as plt


class HistogramViewer:
    def __init__(self, win: QWidget, label: str, histogram_func: callable, skip=1, limits = (None, None)):
        self.skip = skip
        self.skip_counter = 0
        self.fig, self.ax = plt.subplots()
        self.title = "Histogram of " + label
        self.win = win
        self.histogram_func = histogram_func
        self.limits = limits

        def handle_close(event):
            self.win.histogram_viewer = None
            
        self.fig.canvas.manager.set_window_title(self.title)
        self.fig.canvas.mpl_connect("close_event", handle_close)
        plt.show()
        # self.fig.canvas.draw()
        plt.ion()
        self.update_distribution()

    def update_distribution(self):
        if self.skip_counter == 0:
            print("start update Hist")
            self.ax.cla()
            v_values = [self.histogram_func(mol) for mol in self.win.molecules]
            if np.isnan(v_values).any():
                print("ERROR: v_values contains NaN!")
                print(v_values)
                raise ValueError("v_values contains NaN.")

            if np.isinf(v_values).any():
                print("ERROR: v_values contains inf or -inf!")
                print(v_values)
                raise ValueError("v_values contains inf or -inf.")
            self.ax.hist(v_values, bins='auto', density=True, color='skyblue', edgecolor='black')
            print("...done")
            self.ax.set_xlim(*self.limits)                              # ==== for future =======
            self.ax.set_title(self.title)
            # plt.show(block=False)
            
            self.fig.canvas.draw_idle()          # .draw_idle
        self.skip_counter += 1
        if self.skip_counter >= self.skip:
            self.skip_counter = 0
        

    def raise_it(self):
        self.fig.canvas.manager.window.raise_()
        
class PlotViewer:
    def __init__(self, win: QWidget, num_points: int, label: str, functions: list[tuple[str,callable]], t_interval: tuple, func_interval: tuple, step=20):
        self.win = win
        self.current_point = 0
        self.num_points = num_points
        self.functions = functions
        
        self.t = np.linspace(*t_interval, num_points)  # Fixed X-axis
        self.func_values = [np.full(num_points, np.nan) for _ in range(len(functions))]  # Empty Y-values (initialize with NaN)

        # for accumulation of values 
        self.step = step
        self.count_step = 0
        self.c_func_values = [0]*len(functions)

        # Create figure and plot
        self.fig, self.ax = plt.subplots()
        self.fig.canvas.manager.set_window_title(label)
        self.lines = [self.ax.plot(self.t, func_val, label=func[0])[0] for func, func_val in zip(self.functions, self.func_values)]
        self.ax.set_xlim(*t_interval)
        self.ax.set_ylim(*func_interval)
        self.ax.legend()

        def handle_close(event):
            self.win.plot_viewer = None
        self.fig.canvas.mpl_connect("close_event", handle_close)
        
        plt.ion()
        plt.show()

    def update(self, dt: float):
        # print("start plot update")
        for i, func in enumerate(self.functions):
            self.c_func_values[i] += func[1](self.win)  
             
        self.count_step += 1
        if self.count_step >= self.step:
            print("plot values:", self.c_func_values)
            self.count_step = 0
            for i, c_value in enumerate(self.c_func_values):  
                self.func_values[i][self.current_point] = c_value / self.step
                self.c_func_values[i] = 0
                
            for line, func_value in zip(self.lines, self.func_values):
                line.set_ydata(func_value)  # Update the plot
                
            self.current_point += 1
            if self.current_point >= self.num_points:
                self.t = self.t[1:]  # remove the first point
                self.t = np.append(self.t, self.t[-1] + dt * self.step)  # append new point at end
                for i in range(len(self.func_values)):
                    self.func_values[i] = self.func_values[i][1:]
                    self.func_values[i] = np.append(self.func_values[i], np.nan)
                self.current_point -= 1
            # plt.draw()  # Refresh the figure
            self.fig.canvas.draw_idle()         # .draw_idle

    def raise_it(self):
        self.fig.canvas.manager.window.raise_()


class ParamViewer(QWidget):
    def __init__(self, parent, param_funcs):
        super().__init__()
        self.setWindowTitle("Parameters")
        self.param_funcs = param_funcs
        self.obj = parent
        self.layout = QFormLayout()
        self.setLayout(self.layout)
        self.labels = {}

        for display_name, func in self.param_funcs:
            label = QLabel("")
            self.layout.addRow(display_name + ":", label)
            self.labels[display_name] = label

        self.update_parameters()

    def update_parameters(self):
        for name, func in self.param_funcs:
            try:
                val = func(self.obj)
            except Exception as e:
                val = f"Error: {e}"
            self.labels[name].setText(str(val))

class RightMenu:
    def __init__(self, win: QWidget):
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(1)
        win.setLayout(self.main_layout)
        self.button_width = 0

    def add_button(self, label: str, on_click: callable):
        btn = QPushButton(label)
        btn.setFixedSize(btn.sizeHint())  # Minimal size
        self.main_layout.addWidget(btn)
        self.button_width = max(self.button_width, btn.sizeHint().width())
        btn.clicked.connect(on_click)
        return self.button_width

    def width(self):
        return self.button_width        
