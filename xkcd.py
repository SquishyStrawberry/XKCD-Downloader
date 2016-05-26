#!/usr/bin/env python
from __future__ import print_function
import eventlet
eventlet.monkey_patch()

import os
import re

import bs4
import colorama
import requests

BASE_URL = "https://xkcd.com/{}/"
FILENAME_TEMPLATE = "comics/{:04} - XKCD - {}.png"

# This value limits the pool of coroutines to 255, since that's the maximum
# amount of files you can have open at the same time and thus write to.
MAXIMUM_FILE_OBJECTS = 255

# Python 2 uses `raw_input` instead of `input`
input_ = getattr(__builtins__, "raw_input", input)

# This sets up stdout so that we can catch ANSI escape sequences (for colors)
# and replace them with Win32 API calls.
colorama.init()


def cprint(color, *args, **kwargs):
    print(color, end="")
    print(*args, **kwargs)
    print(colorama.Fore.RESET + colorama.Back.RESET, end="")


def _save_comic(num):
    response_text = requests.get(BASE_URL.format(num)).text
    soup = bs4.BeautifulSoup(response_text, "lxml")
    comic_div = soup.find("div", id="comic")

    # Fixes an issue mentioned on GitHub, by only downloading comics that just
    # have the comic image in the comic div, but I am unsure of any "real"
    # comics that have more than the image.
    if len(comic_div) != 3:
        raise RuntimeError("Comic is not a regular comic!")

    image_src = comic_div.find("img")["src"]
    image_url = "https://" + image_src.replace("//", "")
    title = soup.find("title").text.split("xkcd: ")[1]
    # Remove any invalid characters that aren't allowed in filenames.
    title = re.sub(r"[^A-Za-z 0-9\-]", "", title)

    resp = requests.get(image_url, stream=True)
    filename = FILENAME_TEMPLATE.format(num, title)
    with open(filename, "wb") as comic_file:
        for chunk in resp.iter_content():
            comic_file.write(chunk)
    resp.close()


def save_comic(num):
    cprint(colorama.Fore.YELLOW, "Started downloading comic", num)
    try:
        _save_comic(num)
    except Exception as e:
        return num, e
    else:
        return num, None

def save_comics(start_num, end_num):
    to_go = end_num + 1 - start_num
    comic_numbers = range(start_num, end_num + 1)
    p = eventlet.GreenPool(min(to_go, MAXIMUM_FILE_OBJECTS))
    successful = failed = 0
    try:
        for (num, exception) in p.imap(save_comic, comic_numbers):
            if exception is None:
                cprint(colorama.Fore.GREEN, "Finished downloading comic", num)
                successful += 1
            else:
                cprint(colorama.Fore.RED,
                       "There was an error "
                       "downloading comic {}: {}".format(num, exception))
                failed += 1
            to_go -= 1
    except KeyboardInterrupt:
        # We specifically catch KeyboardInterrupt because the user may want to
        # interrupt the process while it isn't finished, but we don't want to
        # show an ugly error message without printing download status.
        pass
    return successful, failed, to_go

def main():
    comic_input = input_("Enter the number or range of comics to download: ")
    successful = failed = 0

    if not os.path.isdir("comics"):
        os.mkdir("comics")

    if "-" in comic_input:
        start_num, end_num = map(int, comic_input.split("-"))
    else:
        start_num, end_num = 1, int(comic_input)

    successful, failed, to_go = save_comics(start_num, end_num)

    # We print out multiple newlines when we haven't downloaded all the comics
    # to space ourselves from the "^C" that gets printed.
    msg = "DOWNLOADS "
    if to_go == 0:
        msg += "COMPLETED"
    else:
        print()
        msg += "INTERRUPTED"
    print()
    print(msg)
    print("-" * len(msg))

    cprint(colorama.Fore.GREEN,
           "Successfully downloaded", successful, "comics")
    cprint(colorama.Fore.RED, failed, "failed")
    cprint(colorama.Fore.YELLOW, to_go, "skipped")
    print("\nFiles saved in", os.path.join(os.getcwd(), "comics"))

if __name__ == "__main__":
    main()
