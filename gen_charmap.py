import pprint
import rotelhex
import time

r=rotelhex.Rotel(port="/dev/serial0")
time.sleep(1)
r._display.label_change=True
r.label_change()
time.sleep(2) # just in case
last_char = r._display._current_char.decode('cp850')
charmap = [last_char]
while True:
    print("outer: {}".format(last_char))
    r.char_next()
    while last_char == r._display._current_char.decode('cp850'):
        print(r._display)
        time.sleep(0.1)
    last_char = r._display._current_char.decode('cp850')
    if last_char == charmap[0]:
        break
    else:
        charmap.append(last_char)

charmap[0] = ' ' # actually the first char is a space

with open("rotelhex/charmap.py","w") as f:
    f.write("CHARMAP = ")
    f.write(pprint.pformat(charmap))