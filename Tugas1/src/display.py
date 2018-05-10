import sys, os
import math

def progress_bar(progress, width):
    blocks = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    total = progress * width
    count = total
    text = ""
    size = len(blocks)
    top = size - 1
    while count > 0:
        if count >= 1:
            count -= 1
            text += blocks[top]
        else:
            count = 0
            text += blocks[round(count * top)]
    for _ in range(int(total), width):
        text += " "
    return text

displayed = False
last = 0
def show(text, name="-", progress=-1, current=-1, max=-1, max_width=50):
    global last
    width, _ = os.get_terminal_size()
    # Offset the cursor and clear lines.
    for _ in range(0, last): 
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")
    # Resets the lines taken count
    last = 0
    # Printes the title
    for t in text:
        print(t)
        last += 1
    # Writes the item name
    sys.stdout.write(name)
    t_curr = "-"
    t_max = "-"
    if current > -1:
        t_curr = str(current)
    if max > -1:
        t_max = str(max)
    t_progress = t_curr + "/" + t_max
    # Offset of the right-align items form the left.
    offset = len(name) + len(t_progress)

    if width < offset:
        print()
        last += 1
    elif width > max_width:
        width = max_width
    offset = width - offset
    for _ in range(0, offset):
        sys.stdout.write("\033[C")
    print(t_progress)
    last += 1
    # Writes progress
    t_progress = "-"
    if progress > -1:
        t_progress = "{:.2f}%".format(progress * 100)
        while len(t_progress) < 7:
            t_progress = " " + t_progress
    offset = len(t_progress) + 2
    if offset > width:
        print(t_progress)
    else:
        w = width
        if w > max_width:
            w = max_width
        print(progress_bar(progress, w - offset), t_progress)
    last += 1
