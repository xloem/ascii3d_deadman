#!/usr/bin/env python3
import curses

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
    App().run()
