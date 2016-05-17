#!/usr/bin/env python
from __future__ import print_function
import eventlet; eventlet.monkey_patch()

import os
import re
import threading
import warnings

import bs4
import colorama
import requests

BASE_URL = "http://xkcd.com/{}/"
FILENAME_TEMPLATE = "comics/{:04} - XKCD - {}.png"

# We need to create a semaphore for opening files, since on most OSes you can
# only open a maximum of 256 files at the same time.
fileobj_semaphore = threading.Semaphore(255)

# Ignore BeautifulSoup warning about not specifying a parser.
warnings.simplefilter("ignore", category=UserWarning)


def _save_comic(num):
    # Get the so-called "soup of elements".
    response_text = requests.get(BASE_URL.format(num)).text
    soup = bs4.BeautifulSoup(response_text)

    # Find the image url
    comic_div = soup.find("div", {"id": "comic"})
    image = comic_div.find("img")
    image_url = "http://" + image["src"].replace("//", "")

    # Find the official title of the comic.
    title = soup.find("title").text
    title = title.split("xkcd: ")[1]

    # Remove any invalid characters that aren't allowed in filenames.
    title = re.sub(r"[^A-Za-z 0-9\-]", "", title)

    resp = requests.get(image_url, stream=True)
    filename = FILENAME_TEMPLATE.format(num, title)

    with fileobj_semaphore, open(filename, "wb") as comic_file:
        print(colorama.Fore.MAGENTA, end="")
        print("Started writing comic", num, "to file")
        print(colorama.Fore.RESET, end="")
        # Write file kibibyte by kibibyte.
        for chunk in resp.iter_content(1024):
            comic_file.write(chunk)
    resp.close()  # You need to close stream requests


def save_comic(num, print_status=True):
    if print_status:
        print(colorama.Fore.YELLOW, end="")
        print("Started downloading comic", num)
        print(colorama.Fore.RESET, end="")
    try:
        _save_comic(num)
    except Exception as e:
        return num, e
    else:
        return num, None


def main():
    comic_input = input("Enter the number or range of comics to download: ")
    successful = failed = 0

    if not os.path.isdir("comics"):
        os.mkdir("comics")

    if "-" in comic_input:
        # A range was entered
        start_num, end_num = map(int, comic_input.split("-"))
    else:
        # A single number was entered
        start_num, end_num = 1, int(comic_input)

    # Download all the comics asynchronously, which makes it way, WAY, faster.
    p = eventlet.GreenPool(end_num + 1 - start_num)
    for (num, exception) in p.imap(save_comic, range(start_num, end_num + 1)):
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

    print("\nDOWNLOADS COMPLETED")
    print("-" * len("DOWNLOADS COMPLETED"))

    print(colorama.Fore.GREEN, end="")
    print("Successfully downloaded", successful, "comics")
    print(colorama.Fore.RED, end="")
    print(failed, "failed")
    print(colorama.Fore.RESET, end="")
    print("\nFile saved in", os.path.join(os.getcwd(), "comics"))

if __name__ == "__main__":
    main()
