import curses
import curses.textpad

stdscr = curses.initscr()
# don't echo key strokes on the screen
curses.noecho()
# read keystrokes instantly, without waiting for enter to ne pressed
curses.cbreak()
# enable keypad mode
stdscr.keypad(1)
stdscr.clear()
stdscr.refresh()
win = curses.newwin(1, 60, 3, 10)
tb = curses.textpad.Textbox(win)
text = tb.edit()
win.addstr(4,1,text.encode('utf_8'))