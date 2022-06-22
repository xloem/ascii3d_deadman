import curses

def main(stdscr):
    stdscr.nodelay(True)
    stdscr.clear()

    key = 'press key?'

    while key != 'q':
      try:
        key = stdscr.getkey()
      except:
        pass
      stdscr.erase()
      stdscr.addstr(4, 3, key)
      #stdscr.refresh()

curses.wrapper(main)
