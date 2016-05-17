#!/usr/bin/env python3
import html.parser
import os
import re
import shutil
import traceback

import colorama
import requests
from bs4 import BeautifulSoup

# TODO Paralellize this code


class _LazyAttribute(object):
    def __init__(self, name, method_name):
        self.name = name
        self.method_name = method_name

    def __get__(self, instance, owner):
        if not hasattr(instance, "_lazy_attributes"):
            instance._lazy_attributes = {}
        if self.method_name not in instance._lazy_attributes:
            instance._lazy_attributes[self.method_name] = \
                getattr(owner, self.method_name)(instance)
        return instance._lazy_attributes[self.method_name][self.name]


class Comic:
    BASE_URL = "http://xkcd.com/{}/"
    FILENAME_TEMPLATE = "comics/{:04} - XKCD - {}.png"

    image_url = _LazyAttribute("image_url", "_get_image_data")
    title = _LazyAttribute("title", "_get_image_data")

    def __init__(self, num):
        self.num = num
        self.url = self.BASE_URL.format(self.num)

    def _get_image_data(self):
        response_text = requests.get(self.url).text
        soup = BeautifulSoup(response_text, "html.parser")

        # Find the image url
        comic_div = soup.find("div", {"id": "comic"})
        image = comic_div.find("img")
        image_url = "http://" + image["src"].replace("//", "")

        # Find the official title of the comic.
        title = soup.find("title").text
        title = title.split("xkcd: ")[1]

        # Remove any invalid characters that aren't allowed in filenames.
        title = re.sub(r"[^A-Za-z 0-9\-]", "", title)

        return {
            "image_url": image_url,
            "title": title,
        }

    def download_and_save_image(self):
        resp = requests.get(self.image_url, stream=True)
        filename = self.FILENAME_TEMPLATE.format(self.num, self.title)

        with open(filename, "wb") as comic_file:
            shutil.copyfileobj(resp.raw, comic_file)
        resp.close()  # You need to close stream requests

def main():
    comic_input = input("Enter the number or range of comics to download: ")
    start_num = 1
    end_num = 0

    if "-" in comic_input:
        # A range was entered
        start_num, end_num = map(int, comic_input.split("-"))
    else:
        # A single number was entered
        end_num = int(comic_input)

    # Create folder comics inside cwd if it doesn't exist
    if not os.path.exists("comics"):
        os.makedirs("comics")

    successful = failed = 0

    # Loop through and download the comics
    for i in range(start_num, end_num+1):
        try:
            Comic(i).download_and_save_image()
        except:
            print("There was an error downloading comic", i)
            traceback.print_exc()
            failed += 1
        else:
            successful += 1

    print("\nDOWNLOADS COMPLETED")
    print("-------------------")

    print(colorama.Fore.GREEN + "Successfully downloaded",
                                 successful,
                                 "comics")
    print(colorama.Fore.RED + str(failed),
                              "failed")
    print(colorama.Fore.RESET + "\nFile saved in",
                                os.path.join(os.getcwd(), "comics"))

if __name__ == "__main__":
    main()
