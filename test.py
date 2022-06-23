#!/usr/bin/env python3
import curses, time, numpy as np

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
        return vec @ self.mat
    def inverted(self):
        return CoordFrame(np.linalg.inv(self.mat))
    @classmethod
    def fromaxisangle(cls, axis, angle, position=[0,0,0,0]):
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
        mat[3,:3] = position[:3]
        return cls(mat)

class Point:
    def __init__(self, str, pos):
        self._points = np.array([pos])
        self.str = str
    def points(self):
        return self._points
    def draw(self, engine, projected_points):
        x, y, _ = projected_points[0]
        engine.plot(x, y, self.str)


class Engine:
    def __init__(self, *initial_objects):
        self.objects = []
        self.object_points = []
        self.add(*initial_objects)
    def run(self):
        curses.wrapper(self.__run)
    def plot(self, x, y, str):
        line = round(y / self.char_height)
        row = round(x / self.char_width)
        self.window.addstr(line, row, str)
    def add(self, *objects):
        self.objects.extend(objects)
        self.__update_pointslist()
    def __run(self, window):
        self.__init(window)
        self.running = True
        camera = None
        while self.running:
            camera = self.update(*self.__update(camera))
            if camera is None:
                break
    def __init(self, window):
        # curses
        self.window = window
        self.window.nodelay(True)
        self.window.clear()
        # time
        self.monotonic_start = time.monotonic()
        self.time = 0
    def __update_pointslist(self):
        self.object_points = [object.points() for object in self.objects]
        if len(self.object_points):
            # allocate space
            self.untransformed_points = np.concatenate(self.object_points, axis=0)
            self.transformed_points = self.untransformed_points.copy()[:,:3]
            # find offsets for objects
            offset = 0
            self.object_point_ranges = []
            for idx, points in enumerate(self.object_points):
                next_offset = offset + len(points)
                self.object_point_ranges.append((offset, next_offset))
                offset = next_offset
    def __update(self, camera_frame):
        # draw the geometry
        if camera_frame is not None:
            inverse_camera_frame = camera_frame.inverted()
            if len(self.object_points):
                untransformed_points = np.concatenate(self.object_points)
                transformed_points = inverse_camera_frame.apply(untransformed_points)
                for idx, (object, range) in enumerate(zip(self.objects, self.object_point_ranges)):
                    object.draw(self, transformed_points[range[0]:range[1]])
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
        # update time and calculate change
        now = time.monotonic() - self.monotonic_start
        time_change = now - self.time
        self.time = now
        return time_change, key

class Scene(Engine):
    def __init__(self):
        self.last_key = 'press key?'
        self.camera = CoordFrame.fromaxisangle(Z, 0, [0,10,-10,1])
        self.text_object = Point("press key?", [0,0,0,1])
        super().__init__(self.text_object)
    def update(self, time_change, key = ''):
        if key:
            if key == 'q':
                return self.stop()
            self.text_object.str = key
        #self.plot(self.width / 2, self.height / 2, self.last_key)
        return self.camera

if __name__ == '__main__':
    Scene().run()
