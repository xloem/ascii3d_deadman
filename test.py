#!/usr/bin/env python3
import curses, time, numpy as np

X = np.array([1.0,0,0,0])
Y = np.array([0,1.0,0,0])
Z = np.array([0,0,1.0,0])
W = np.array([0,0,0,1.0])

class CoordFrame:
    def __init__(self, mat = None, position=[0,0,0], scale=1, axis=Z, angle=0):
        if mat is None:
            self.mat = np.identity(4)
            self.set(position=position, scale=scale, axis=axis, angle=angle)
        else:
            self.mat = mat
    def apply(self, vec, out=None):
        if type(vec) is CoordFrame:
            vec = vec.mat
        if type(out) is CoordFrame:
            out = out.mat
        return np.matmul(vec, self.mat, out=out)
    def inverted(self):
        return CoordFrame(np.linalg.inv(self.mat))
    def set(self, mat = None, position=[0,0,0], scale=1, axis=None, angle=0):
        # from https://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle
        if mat is not None:
            if type(mat) is CoordFrame:
                mat = mat.mat
            self.mat[:] = mat
            return
        else:
            cos_theta = np.cos(angle)
            sin_theta = np.sin(angle)
            if axis is not None:
                axis = axis[:3]
                axis = axis / np.linalg.norm(axis)
                I = self.mat[:3,:3]
                I[:] = np.identity(3)
                self.mat[:3, :3] =  (
                    cos_theta * I +
                    sin_theta * np.cross(axis, -I) +
                    (1 - cos_theta) * np.outer(axis, axis)
                ) * scale
            self.mat[3,:3] = position[:3]
        return self

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
        col = round(x / self.char_width)
        self.window.addstr(line, col, str)
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
        self.screen_translation = np.zeros(2)
        self.screen_scale = np.ones(2)
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
            self.untransformed_points = np.concatenate(self.object_points, axis=0, dtype=float)
            self.transformed_xyzw = self.untransformed_points.copy()
            self.transformed_z = self.transformed_xyzw[:,2:3]
            self.transformed_xy = self.transformed_xyzw[:,:2]
            self.transformed_xyz = self.transformed_xyzw[:,:3]
            # find offsets for objects
            offset = 0
            self.object_point_ranges = []
            for idx, points in enumerate(self.object_points):
                next_offset = offset + len(points)
                self.object_point_ranges.append((offset, next_offset))
                offset = next_offset
    def __update(self, camera_frame):
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
        # update screen vecs
        self.screen_translation[:] = (self.width, self.height)
        self.screen_translation /= 2
        min_dim = self.screen_translation.min()
        self.screen_scale[:] = (min_dim, -min_dim)
        # draw the geometry
        if camera_frame is not None:
            inverse_camera_frame = camera_frame.inverted()
            if len(self.object_points):
                # transform from 3d to 2d
                untransformed_points = np.concatenate(self.object_points)
                inverse_camera_frame.apply(untransformed_points, out=self.transformed_xyzw)
                self.transformed_xy /= self.transformed_z
                self.transformed_xy *= self.screen_scale
                self.transformed_xy += self.screen_translation
                # draw
                for idx, (object, range) in enumerate(zip(self.objects, self.object_point_ranges)):
                    object.draw(self, self.transformed_xyz[range[0]:range[1]])
        # update time and calculate change
        now = time.monotonic() - self.monotonic_start
        time_change = now - self.time
        self.time = now
        return time_change, key

class Scene(Engine):
    def __init__(self):
        self.last_key = 'press key?'
        self.pitch_angle = -0.75
        self.yaw_angle = 0
        self.distance = 20
        self.camframe_pitch = CoordFrame(axis=X, angle=self.pitch_angle)
        self.camframe_yaw = CoordFrame(axis=Y, angle=self.yaw_angle)
        self.camframe_distance = CoordFrame(position=[0,0,-self.distance])
        self.camframe_final = CoordFrame()
        #self.text_object = Point("press key?", [0,0,0,1])
        self.text_objects = [
            Point("press key?", [pos[0]*8, 0, pos[1]*8, 1])
            for pos in (
                (1, 1),
                (1, -1),
                (-1, -1),
                (-1, 1)
            )
        ]
        super().__init__(*self.text_objects)
    def handle_key(self, time_change, key):
        if key == 'q':
            return False
        # keys were set to angles just during debugging
        if key in ('a', 'A', 'h', 'H', 'KEY_LEFT'):
            # left
            self.yaw_angle -= 0.125#time_change * 32
            key = str(self.yaw_angle)
        elif key in ('d', 'D', 'l', 'L', 'KEY_RIGHT'):
            # right
            self.yaw_angle += 0.125#time_change * 32
            key = str(self.yaw_angle)
        elif key in ('w', 'W', 'k', 'K', 'KEY_UP'):
            # up
            self.pitch_angle -= 0.125#time_change * 32
            key = str(self.pitch_angle)
        elif key in ('s', 'S', 'j', 'J', 'KEY_DOWN'):
            # down
            self.pitch_angle += 0.125#time_change * 32
            key = str(self.pitch_angle)
        elif key:
            for text_object in self.text_objects:
                text_object.str = key
        return True
    def update(self, time_change, key = ''):
        if self.handle_key(time_change, key) == False:
            return None

        self.camframe_pitch = CoordFrame(axis=X, angle=self.pitch_angle)
        self.camframe_yaw = CoordFrame(axis=Y, angle=self.yaw_angle)
        self.camframe_distance.set(position=[0,0,-self.distance])

        self.camframe_pitch.apply(self.camframe_distance, out=self.camframe_final)
        self.camframe_yaw.apply(self.camframe_final, out=self.camframe_final)

        #self.camframe_final.set(axis=X, angle=-np.pi/4, position=[0,10,-10,1])

        return self.camframe_final

if __name__ == '__main__':
    Scene().run()
