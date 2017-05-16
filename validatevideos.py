import xml.etree.ElementTree as ET
import subprocess
import argparse
import ConfigParser
import os
import sys
import xml.etree.ElementTree as ET
from difflib import ndiff

def generateFilePolicy(startObj):
	filePolicyFile = startObj + ".mediainfo.xml" #init full path to mediainfo xml file
	filePolicyFileObj = open(filePolicyFile,"w+") #init file obj for that path
	process = subprocess.Popen(["mediainfo","--Output=PBCore2",startObj],stdout=subprocess.PIPE,stderr=subprocess.PIPE) #grip mediainfo output
	output,err = process.communicate() #convert to string
	filePolicyFileObj.write(output) #write mediainfo output to text file
	filePolicyFileObj.close() #close xml file (good housekeeping)	
	return filePolicyFile #return xml file path to main()
	

def verifyFormatPolicy(startObj,startObjPolicyFile,formatPolicyFile,accessionName):
	fops = {} #format policy
	fips = {} #file policy
	ns = "{http://www.pbcore.org/PBCore/PBCoreNamespace.html}" #placeholder for namespace string, could be implemented as dict
	fop = ET.parse(formatPolicyFile).getroot() #get xml root from formatPolicy xml doc
	fip = ET.parse(startObjPolicyFile).getroot() #get policy of file at hand
	audioStreamNum = 0
	#fill dictionary with policy specs
	for itrack in fop.findall(ns+'instantiationTracks'):
		fops['instantiation_tracks'] = itrack.text
	for ietrack in fop.findall(ns+'instantiationEssenceTrack'):
		if ietrack.find(ns+'essenceTrackType').text == "Video":
			fops['video_encoding'] = ietrack.find(ns+'essenceTrackEncoding').text
			fops['video_framerate'] = ietrack.find(ns+'essenceTrackFrameRate').text
			fops['video_bitdepth'] = ietrack.find(ns+'essenceTrackBitDepth').text
			fops['video_framesize'] = ietrack.find(ns+'essenceTrackFrameSize').text
		elif ietrack.find(ns+'essenceTrackType').text == "Audio":
			audioStream = "audio_stream" + str(audioStreamNum)
			fops[audioStream + '_encoding'] = ietrack.find(ns+'essenceTrackEncoding').text
			fops[audioStream + '_datarate'] = ietrack.find(ns+'essenceTrackDataRate').text
			for eta in ietrack.findall(ns+'essenceTrackAnnotation'):
				if eta.get('annotationType') == "Channel(s)":
					fops[audioStream + '_channels'] = eta.text
			audioStreamNum = audioStreamNum + 1		
	#fill dicitonary with file specs
	audioStreamNum = 0
	for itrack in fip.findall(ns+'instantiationTracks'):
		fips['instantiation_tracks'] = itrack.text
	for ietrack in fip.findall(ns+'instantiationEssenceTrack'):
		if ietrack.find(ns+'essenceTrackType').text == "Video":
			fips['video_encoding'] = ietrack.find(ns+'essenceTrackEncoding').text
			fips['video_framerate'] = ietrack.find(ns+'essenceTrackFrameRate').text
			fips['video_bitdepth'] = ietrack.find(ns+'essenceTrackBitDepth').text
			fips['video_framesize'] = ietrack.find(ns+'essenceTrackFrameSize').text
		elif ietrack.find(ns+'essenceTrackType').text == "Audio":
			audioStream = "audio_stream" + str(audioStreamNum)
			fips[audioStream + '_encoding'] = ietrack.find(ns+'essenceTrackEncoding').text
			fips[audioStream + '_datarate'] = ietrack.find(ns+'essenceTrackDataRate').text
			for eta in ietrack.findall(ns+'essenceTrackAnnotation'):
				if eta.get('annotationType') == "Channel(s)":
					fips[audioStream + '_channels'] = eta.text
			audioStreamNum = audioStreamNum + 1			
	#print fops
	#print fips
	#compare the two
	for f in fops:
		#print fops[f]
		#print fips[f]
		if fops[f] != fips[f]:
			print accessionName + " failed at " + f
			foo = raw_input("Eh")
	
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
	accessionaName = os.path.basename(accessionName)
	#set formatPolicy to match extension of startObj
	if ext == '.mov':
		formatPolicy = movFP.strip('"').strip("'")
	elif ext == '.flv':
		formatPolicy = flvFP.strip('"').strip("'")
	elif ext == '.mpeg':
		formatPolicy = mpegFP.strip('"').strip("'")
	elif ext == '.mp4':
		formatPolicy = mp4FP.strip('"').strip("'")
	else:
		print "this file has no associated policy and cannot be processed"
		sys.exit(1)
	#makes a mediainfo.txt file, returns full path to said txt file
	filePolicyXMLFile = generateFilePolicy(startObj)
	#verifies that everything in mediainfo.txt file matches formatPolicy
	verifyFormatPolicy(startObj,filePolicyXMLFile,formatPolicy,accessionName)
	os.remove(filePolicyXMLFile) #remove mediainfo.txt file if match
main()	