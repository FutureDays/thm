
import subprocess
import argparse
import ConfigParser
import os
import sys

	
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
	ext = ext.lower()
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
	
	output = subprocess.check_output(["mediaconch","-mc",startObj,"-p",formatPolicy])
	print output
main()	