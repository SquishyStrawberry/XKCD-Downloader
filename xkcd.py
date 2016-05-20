#!/usr/bin/env python
from __future__ import print_function
import eventlet; eventlet.monkey_patch()

import os
import re
import sys
import threading

import colorama
import lxml.etree
import requests

BASE_URL = "http://xkcd.com/{}/"
FILENAME_TEMPLATE = "comics/{:04} - XKCD - {}.png"

# Python 2 uses `raw_input` instead of `input`
input_ = getattr(__builtins__, "raw_input", input)

# This value limits the amount of coroutines created, which are limited by the
# amount of sockets you can have in a select() call.
if sys.platform.startswith("win"):
    MAXIMUM_COROUTINES = 512
else:
    MAXIMUM_COROUTINES = 32767

# This semaphore limits the amounts of file objects that are open at one time,
# which is actually a variable value with a default of 255.
file_semaphore = threading.BoundedSemaphore(255)


def _save_comic(num):
    # Get the so-called "soup of elements".
    response_text = requests.get(BASE_URL.format(num)).text
    root = lxml.etree.HTML(response_text)

    # Find the image url
    comic_div = root.xpath('//div[@id="comic"]')[0]

    # Fixes an issue mentioned on GitHub, by only downloading comics that just
    # have the comic image in the comic div, but I am unsure of any "real"
    # comics that have more than the image.
    if len(comic_div) != 1:
        raise RuntimeError("Comic is not a regular comic!")

    image_src = comic_div.find("img").get("src")
    image_url = "http://" + image_src.replace("//", "")

    # Find the official title of the comic.
    title = root.xpath("/html/head/title/text()")[0].split("xkcd: ")[1]

    # Remove any invalid characters that aren't allowed in filenames.
    title = re.sub(r"[^A-Za-z 0-9\-]", "", title)

    resp = requests.get(image_url, stream=True)
    filename = FILENAME_TEMPLATE.format(num, title)

    with file_semaphore, open(filename, "wb") as comic_file:
        print(colorama.Fore.MAGENTA, end="")
        print("Started writing comic", num, "to file")
        print(colorama.Fore.RESET, end="")
        # Write file kibibyte by kibibyte.
        for chunk in resp.iter_content(1024):
            comic_file.write(chunk)
    resp.close()  # You need to close stream requests


def save_comic(num):
    print(colorama.Fore.YELLOW, end="")
    print("Started downloading comic", num)
    print(colorama.Fore.RESET, end="")
    try:
        _save_comic(num)
    except Exception as e:
        return num, e
    else:
        return num, None

def save_comics(start_num, end_num):
    # Download all the comics asynchronously, which makes it way, WAY, faster.
    to_go = end_num + 1 - start_num
    comic_numbers = range(start_num, end_num + 1)
    p = eventlet.GreenPool(min(to_go, MAXIMUM_COROUTINES))
    successful = failed = 0
    try:
        for (num, exception) in p.imap(save_comic, comic_numbers):
            if exception is None:
                print(colorama.Fore.GREEN, end="")
                print("Finished downloading comic", num)
                print(colorama.Fore.RESET, end="")
                successful += 1
            else:
                print(colorama.Fore.RED, end="")
                print("There was an error downloading comic", num, end=": ")
                print(exception)
                print(colorama.Fore.RESET, end="")
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
        # A range was entered
        start_num, end_num = map(int, comic_input.split("-"))
    else:
        # A single number was entered
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

    print(colorama.Fore.GREEN, end="")
    print("Successfully downloaded", successful, "comics")
    print(colorama.Fore.RED, end="")
    print(failed, "failed")
    print(colorama.Fore.YELLOW, end="")
    print(to_go, "skipped")
    print(colorama.Fore.RESET, end="")
    print("\nFiles saved in", os.path.join(os.getcwd(), "comics"))

if __name__ == "__main__":
    main()
