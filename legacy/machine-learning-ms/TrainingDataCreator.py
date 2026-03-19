"""
TrainingDataCreator.py 7/15/2020
@author Misha Lubich
Last Updated: 7/16/2020
"""

import os.path
import pandas as pd
import nltk
from nltk.stem import PorterStemmer

#CONFIG
df = None


if not os.path.isfile("scraperStatus.txt"):
	scraperStatusFile = open("scraperStatus.txt", "w")
	scraperStatusFile.write("false")
	scraperStatusFile.close()

scraperStatusFile = open("scraperStatus.txt", "r")
isScriptActive = open("isScriptActive.txt", "r")

if scraperStatusFile.read() == "false":

	print("Run the webscraper first")

	confirmation = input("Do you want to execute the scraper now? (y/n) ")

	if confirmation == "y" or confirmation == "yes" or confirmation == "Y" or confirmation == "Yes":
		execfile("RedditScraper.py")

	elif confirmation == "n" or confirmation == "no" or confirmation == "N" or confirmation == "No":
		exit()

	else:
		confirmation = input("Invalid input (y/n) ")

elif scraperStatusFile.read() == "true":
	from RedditScraper.py import df
	df = pd.read_csv("data.csv")
	dataFiltStatusFile = open("dataFiltStatusFile.txt", "r")
	
	if dataFiltStatusFile.read() == "false":
		#FILTERING DATA
		print("Filtering Data...", end="\r")

		#Not null comments
		df = df[df.comment.notnull()]
		df = df[df.comment != "[deleted]"]
		dataFiltStatusFile = open("dataFiltStatusFile.txt", "w")
		dataFiltStatusFile.write("true")
		dataFiltStatusFile.close()

	elif dataFiltStatusFile.read() != "true":
		print("Run the webscraper first")

		


	df.to_csv('data.csv', encoding='utf-8-sig')


	print("                        ")
	print("Done!", end="\r")


else:
	print("Error: Scraper/Training not initialized — run scraper or training data creator again.")
	exit()


#Lemilization
porter = PorterStemmer()


