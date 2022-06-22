#!/usr/bin/env python3
import curses, numpy as np

X = np.array([1.0,0,0,0])
Y = np.array([0,1.0,0,0])
Z = np.array([0,0,1.0,0])
W = np.array([0,0,0,1.0])

class CoordFrame:
    def __init__(self, mat = None):
        if mat is None:
            mat = np.identity(4)
        self.mat = mat
    def apply(self, vec):
        return self.mat @ vec
    def inverted(self):
        return CoordFrame(self.mat.inverse())
    @classmethod
    def fromaxisangle(cls, axis, angle):
        # from https://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle
        cos_theta = np.cos(angle)
        sin_theta = np.sin(angle)
        axis = axis[:3]
        axis = axis / np.linalg.norm(axis)
        mat = np.identity(4)
        I = mat[:3,:3]
        mat[:3, :3] =  (
            cos_theta * I +
            sin_theta * np.cross(axis, -I) +
            (1 - cos_theta) * np.outer(axis, axis)
        )
        return cls(mat)
        

# to move into camera space, call cameraframe.inverted().apply(vector)
# to move into outer space, call innerframe.apply(vector)

class Point:
    def __init__(self, str, pos):
        self.points = np.array([pos])
        self.str = str
    def _points(self):
        return self.points
    def draw(self, engine, projected_points):
        x, y, _ = projected_points[0]
        engine.plot(x, y, self.str)


class Engine:
    def run(self):
        curses.wrapper(self.__run)
    def __init(self):
        self.window.nodelay(True)
        self.window.clear()
    def __run(self, window):
        self.window = window
        self.__init()
        while True:
            self.update(self.__update())
    def plot(self, x, y, str):
        line = round(y / self.char_height)
        row = round(x / self.char_width)
        self.window.addstr(line, row, str)
    def __update(self):
        # getting a key also refreshes
        try:
            key = self.window.getkey()
        except:
            key = ''
        # wipe for next draw
        self.cols = curses.COLS
        self.lines = curses.LINES
        self.char_width = 8
        self.char_height = 16
        self.width = self.cols * self.char_width
        self.height = self.lines * self.char_height
        self.window.erase()
        return key

class App(Engine):
    def __init__(self):
        self.last_key = 'press key?'
    def update(self, key = ''):
        if key:
            self.last_key = key
        self.plot(self.width / 2, self.height / 2, self.last_key)

if __name__ == '__main__':
    frame = CoordFrame.fromaxisangle(Y, 0.2)
    print(frame.mat)
    #App().run()
