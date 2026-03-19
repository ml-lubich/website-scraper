"""
Utils.py
Module "Utils"
@author Misha Lubich 7/16/2020
Last Updated: 7/16/2020
"""
import os.path

#Definitions:
did_scraper_run_f = "status/did_scraper_run.txt"
is_script_active_f = "status/is_script_active.txt"
data_filtStatusFile

#Initialization:
def initialize():
	

#Basic File Functions
def open_file(filename, string):
	assert isinstance(filename, str)
	assert isinstance(string, str)
	assert os.path.isfile(filename)
	f = open(file, "w")
	f.write(string)
	f.close()

def read_file(filename):
	assert isinstance(filename, str)
	assert os.path.isfile(filename)
	filename

def file_exists(filename):
	assert isinstance(filename, str)
	if os.path.isfile(filename):
		return True
	else:
		return False
	
#Statuses:
def is_script_active():
	f = open("is_script_active.txt", "r")
