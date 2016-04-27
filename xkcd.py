import requests
import shutil
import os
from bs4 import BeautifulSoup
import html.parser
import colorama
import re


BASE_URL = "http://xkcd.com/"


class comic:
	def __init__(self, num):
		self.num = num
		self.url = None
		self.imageUrl = None
		self.title = None

	def download_and_save_image(self):
		resp = requests.get(self.imageUrl, stream=True)
		fileName = "comics/" + str(self.num) + " - XKCD - " + self.title + ".png"
		
		with open(fileName, "wb") as comicFile:
			shutil.copyfileobj(resp.raw, comicFile)
		
	def get_image_data(self):
		self.url = BASE_URL + str(self.num) + "/"
		
		respText = requests.get(self.url).text
		soup = BeautifulSoup(respText, "html.parser")
		
		
		#find the link to download the image from
		comicDiv = soup.find("div", {"id": "comic"})
		image = comicDiv.find("img")
		imageSrc = image['src']
		fixedLink = "http://" + imageSrc.replace("//", "")
		self.imageUrl = fixedLink
		
		#find the official title of the comic
		title = soup.find("title")
		fixedTitle = title.text.split("xkcd: ")[1]
		
		#remove any invalid characters that aren't allowed in windows filenames
		fixedTitle = re.sub(r"[^A-Za-z 0-9\-]", "", fixedTitle)
		
		self.title = fixedTitle
		

comicInput = input("Enter the number or range of comics to download: ")
startNum = 1
endNum = 0


if "-" in comicInput:
	#a range was entered
	
	startNum = int(comicInput.split("-")[0])
	endNum = int(comicInput.split("-")[1])
else:

	#a single number was entered
	endNum = int(comicInput)
	

#create folder comics inside cwd if it doesn't exist
if not os.path.exists("comics"):
	os.makedirs("comics")


successfulDownloads = 0
failedDownloads = 0
#loop through and download the comics
for i in range(startNum, endNum+1):
	try:
		currentComic = comic(i)
		currentComic.get_image_data()
		currentComic.download_and_save_image()
		successfulDownloads += 1
	except Exception as e:
		print("There was an error downloading comic", i, e)
		failedDownloads += 1
		
		
print("\nDOWNLOADS COMPLETED")
print("-------------------")

print(colorama.Fore.GREEN + "Successfully downloaded", successfulDownloads, "comics")
print(colorama.Fore.RED + str(failedDownloads), "failed")
print(colorama.Fore.RESET + "\nFile saved in", os.path.join(os.getcwd(), "comics"))
		

	
