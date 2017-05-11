import xml.etree.ElementTree as ET
import subprocess
import argparse
import ConfigParser
import os
import sys
from difflib import ndiff

def generateFilePolicy(startObj):
	filePolicyFile = startObj + ".mediainfo.txt" #init full path to mediainfo txt file
	filePolicyFileObj = open(filePolicyFile,"w") #init file obj for that path
	process = subprocess.Popen(["mediainfo",startObj],stdout=subprocess.PIPE,stderr=subprocess.PIPE) #grip mediainfo output
	output,err = process.communicate() #convert to string
	filePolicyFileObj.write(output) #write mediainfo output to text file
	filePolicyFileObj.close() #close txt file (good housekeeping)	
	return filePolicyFile #return txt file path to main()
	

def verifyFormatPolicy(startObj,filePolicyFile,formatPolicyFile):
	#make list of tags that we don't check because they change from file to file, e.g. duration, stream size percentage
	reservedKeyList = [
		"Completename",
		"Filesize",
		"Duration",
		"Stream size"
	]
	formatPolicyFileObj = open(formatPolicyFile,"r") #init full path to format policy txt file
	formatPolicyList = formatPolicyFileObj.read().splitlines() #read that file into a list, separating list elements by newline
	formatPolicyListDeSpaced = [] #init list for same as above but without spaces
	for f in formatPolicyList:
		formatPolicyListDeSpaced.append(f.replace(" ","")) #remove every space from the list
	filePolicyFileObj = open(filePolicyFile,"r")
	filePolicyList = filePolicyFileObj.read().splitlines()
	filePolicyListDeSpaced = []
	for f in filePolicyList:
		filePolicyListDeSpaced.append(f.replace(" ",""))
	for index,f in enumerate(filePolicyListDeSpaced): #loop through the index and value at index (f) of the despaced list of the file
		match = ''
		match = [rk for rk in reservedKeyList if rk in f] #checks that the reserved key isn't in f
		if not match:
			if not f == formatPolicyListDeSpaced[index]: #if the value of the file isn't the same value as the format policy
				print "file " + startObj + " failed on policy attribute " + filePolicyListDeSpaced[index]
				print "file policy attribute should be " + formatPolicyListDeSpaced[index]
				sys.exit(1) #exit with rtncode 1
	
def main():
	parser = argparse.ArgumentParser(description="verifies a file against its format policy")
	parser.add_argument('-so','--startObj',dest='so',help='the full path of the file to be verified')
	args = parser.parse_args() #allows us to access arguments with args.argName
	config = ConfigParser.ConfigParser()
	scriptRepo = os.path.dirname(os.path.abspath(__file__)) #grip the path to the directory where ~this~ script is located
	config.read(os.path.join(scriptRepo,"video-post-process-config.txt")) #grip the txt file with configuration info
	movFP = config.get('formatPolicy','mov_format_policy')
	flvFP = config.get('formatPolicy','flv_format_policy')
	mpegFP = config.get('formatPolicy','mpeg_format_policy')
	mp4FP = config.get('formatPolicy','mp4_format_policy')
	startObj = args.so
	startDir = os.path.dirname(startObj)
	accessionName,ext = os.path.splitext(startObj)
	#set formatPolicy to match extension of startObj
	if ext == '.mov':
		formatPolicy = movFP.strip('"')
	elif ext == '.flv':
		formatPolicy = flvFP
	elif ext == '.mpeg':
		formatPolicy = mpegFP
	elif ext == '.mp4':
		formatPolicy = mp4FP
	else:
		print "this file has no associated policy and cannot be processed"
		sys.exit(1)
	#makes a mediainfo.txt file, returns full path to said txt file
	filePolicyTxtFile = generateFilePolicy(startObj)
	#verifies that everything in mediainfo.txt file matches formatPolicy
	verifyFormatPolicy(startObj,filePolicyTxtFile,formatPolicy)
	os.remove(filePolicyTxtFile) #remove mediainfo.txt file if match
main()	