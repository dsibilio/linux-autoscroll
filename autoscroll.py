#!/home/dsibilio/python-workspace/linux-autoscroll/.autoscroll/bin/python3
import re
from subprocess import PIPE, Popen
from threading import Event
from time import sleep
import time

from pynput.mouse import Button, Controller as MouseController, Listener
from pynput.keyboard import Key, Controller as KeyboardController


def get_activityname():

    root = Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stdout=PIPE)
    stdout, stderr = root.communicate()
    m = re.search(b'^_NET_ACTIVE_WINDOW.* ([\w]+)$', stdout)

    if m is not None:

        window_id = m.group(1)

        windowname = None
        window = Popen(['xprop', '-id', window_id, 'WM_NAME'], stdout=PIPE)
        stdout, stderr = window.communicate()
        wmatch = re.match(b'WM_NAME\(\w+\) = (?P<name>.+)$', stdout)
        if wmatch is not None:
            windowname = wmatch.group('name').decode('UTF-8').strip('"')

        processname1, processname2 = None, None
        process = Popen(['xprop', '-id', window_id, 'WM_CLASS'], stdout=PIPE)
        stdout, stderr = process.communicate()
        pmatch = re.match(b'WM_CLASS\(\w+\) = (?P<name>.+)$', stdout)
        if pmatch is not None:
            processname1, processname2 = pmatch.group(
                'name').decode('UTF-8').split(', ')
            processname1 = processname1.strip('"')
            processname2 = processname2.strip('"')

        return {
            'windowname':   windowname,
            'processname1': processname1,
            'processname2': processname2
        }

    return {
        'windowname':   None,
        'processname1': None,
        'processname2': None
    }


def is_discord():
    return get_activityname()['processname1'] == 'discord'


def on_move(x, y):
    global pos, scroll_mode, direction, interval, DELAY, DEAD_AREA
    if scroll_mode.is_set():
        delta = pos[1] - y
        if abs(delta) <= DEAD_AREA:
            direction = 0
        elif delta > 0:
            direction = 1
        elif delta < 0:
            direction = -1
        if abs(delta) <= DEAD_AREA + DELAY * 2:
            interval = 0.5
        else:
            interval = DELAY / (abs(delta) - DEAD_AREA)


def on_click(x, y, button, pressed):
    global pos, scroll_mode, direction, interval, BUTTON_START, BUTTON_STOP
    if button == BUTTON_START and pressed and not scroll_mode.is_set() and is_discord():
        pos = (x, y)
        direction = 0
        interval = 0
        scroll_mode.set()
        delete_all()
    elif button in BUTTONS_STOP and pressed and scroll_mode.is_set():
        scroll_mode.clear()


def delete_all():
    with keyboard.pressed(Key.ctrl):
        keyboard.press('a')
        time.sleep(0.1)
        keyboard.press(Key.backspace)
    keyboard.release('a')
    keyboard.release(Key.backspace)


def autoscroll():
    global mouse, scroll_mode, direction, interval
    while True:
        scroll_mode.wait()
        sleep(interval)
        mouse.scroll(0, direction)


mouse = MouseController()
keyboard = KeyboardController()
listener = Listener(on_move=on_move, on_click=on_click)
scroll_mode = Event()
pos = mouse.position
direction = 0
interval = 0

# modify this to adjust the speed of scrolling
DELAY = 5
# modify this to change the button used for entering the scroll mode
BUTTON_START = Button.middle
# modify this to change the button used for exiting the scroll mode
BUTTONS_STOP = [Button.middle, Button.left]
# modify this to change the size (in px) of the area below and above the starting point where the scrolling is paused
DEAD_AREA = 30

listener.start()
autoscroll()
