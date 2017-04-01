#!/usr/bin/python
#the history makers makevideos.py
#concatenates, transcodes, moves videos for The History Makers

import os
import sys
import subprocess
import sys
import glob
import re
import time
import random
import shutil
import fcntl
import argparse
import ConfigParser
from distutils import spawn

###UTILITY FUNCTIONS###
#Context manager for changing the current working directory
class cd:
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
		os.chdir(self.savedPath)

#check that we have required software installed
def dependencies():
	depends = ['ffmpeg','ffprobe']
	for d in depends:
		if spawn.find_executable(d) is None:
			print "Buddy, you gotta install " + d
			sys.exit()
###END UTILS###
###VALIDATE INPUTS###
def startup(logfile,rawCaptures,watermark,fontfile,sunnas,sunnascopyto,xendata,xendatacopyto):
	log(logfile,"running")
	###MAKE SURE START DIRECTORY NOT EMPTY###
	rawCapList = []
	for f in os.listdir(rawCaptures):
		if not f.startswith('.'):
			rawCapList.append(f)
	if not rawCapList:
		msg = "completed. nothing to process"
		log(logfile,msg)
		sys.exit()
	###END START DIRECTORY CHECK###
	###MAKE SURE FONT AND WATERMARK FILES EXIST###
	if not os.path.exists(watermark) and not os.path.exists(watermark.strip('"')):
		msg = "The white-watermark file cannot be found. Please put the white watermark file at " + watermark
		with open(logfile,"r+") as l:
			thelog = l.read()
		subprocess.call(["python","send-email.py","-txt",msg + "\n" + str(thelog)])
		log(logfile,msg)
		sys.exit()
	if not os.path.exists(fontfile):
		msg = "The fontfile cannot be found. Please put the fontfile at " + fontfile
		with open(logfile,"r+") as l:
			thelog = l.read()
		subprocess.call(["python","send-email.py","-txt",msg + "\n" + str(thelog)])
		log(logfile,msg)
		sys.exit()
	###END FONT AND WATERMARK CHECK###
	###MAKE SURE DRIVES ARE MOUNTED###
	if not os.path.exists(sunnas):
		msg = "The video script is unable to run because SUNNAS is not mounted as expected. Please mount SUNNAS on XCluster at " + sunnas
		with open(logfile,"r+") as l:
			thelog = l.read()
		subprocess.call(["python","send-email.py","-txt",msg + "\n" + str(thelog)])
		log(logfile,msg)
		sys.exit()
	if not os.path.exists(sunnascopyto):
		msg = "The video script is unable to run because SUNNAS is not mounted as expected. Please mount SUNNAS on XCluster at " + sunnascopyto
		with open(logfile,"r+") as l:
			thelog = l.read()
		subprocess.call(["python","send-email.py","-txt",msg + "\n" + str(thelog)])
		log(logfile,msg)
		sys.exit()
	if not os.path.exists(xendata):
		msg = "The video script is unable to run because Xendata is not mounted as expected. Please mount Xendata on XCluster at " + xendata
		with open(logfile,"r+") as l:
			thelog = l.read()
		subprocess.call(["python","send-email.py","-txt",msg + "\n" + str(thelog)])
		log(logfile,msg)
		sys.exit()
	if not os.path.exists(xendatacopyto):
		msg = "The video script is unable to run because Xendata is not mounted as expected. Please mount Xendata on XCluster at " + xendatacopyto
		with open(logfile,"r+") as l:
			thelog = l.read()
		subprocess.call(["python","send-email.py","-txt",msg + "\n" + str(thelog)])
		log(logfile,msg)
		sys.exit()
	###END DRIVE MOUNTED CHECK###
	###CHECK IF SOMETHING IS BEING COPIED IN RIGHT NOW###
	donezo = False
	while donezo is False:
		fs = walk(rawCaptures)
		time.sleep(240)
		fsagain = walk(rawCaptures)
		donezo = compare(fs, fsagain)
	###END COPY-IN CHECK###
	###CHECK THAT A FILEMAKER RECORD EXISTS FOR EACH FOUND ACCESSION###
	for dirs,subdirs,files in os.walk(rawCaptures):
			for s in subdirs:
				output = subprocess.Popen(["python","fm-stuff.py","-qExist","-id",s],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				out,err = output.communicate()
				if not out:
					msg = "The video script is unable to run because there is not an accession record for " + s + " in FileMaker"
					subprocess.call(["python","send-email.py","-txt",msg,'-att',logfile])
					log(logfile,msg)	
					sys.exit()
	###END FILEMAKER CHECK###

###COPY-IN CHECK SUB-FUNCTIONS###
###MEASURE FILESIZE TWICE 1S APART###
def sizeloop(thing):
	startsize = os.stat(thing)
	time.sleep(1)
	endsize = os.stat(thing)
	if startsize.st_size == endsize.st_size:
		return
	else:
		sizeloop(thing)
###END MEASURE FILESIZE###
###GENERATE LIST OF EVERY FILE###
def walk(pth):
	thefiles =[]	
	for dirs, subdirs, files in os.walk(pth):
		for files in files:
			fullpath = os.path.join(dirs,files)
			thefiles.append(fullpath)
	for f in thefiles:
		fpath = os.path.join(pth,f)
		sizeloop(fpath)
	return thefiles
###END FILE LIST GENERATION###
###VERIFY NO NEW FILES ADDED###
def compare(fs, fsagain):
	for f in fsagain:
		if not f in fs:
			return False
	return True
###END NEW FILE CHECK###
###END INPUT VALIDATION###
###GENERATE LIST OF FILES FOR FFMPEG###
def makefflist(rawCaptures,logfile):
	fflist = {} #initialize a list of files for ffmpeg to transcode
	for dirs, subdirs, files in os.walk(rawCaptures): #loop thru holding dir on xcluster
		for acc in subdirs: #for each accession# (subdir) in the list of subdirs
			with cd(os.path.join(dirs,acc)): #cd into accession dir
				rawcaplist = [] #init a list that will contain raw captures in each dir
				for rawmov in os.listdir(os.getcwd()): #for each file in the current working directory
					if rawmov.endswith(".mov") or rawmov.endswith(".MOV"): #if it is a mov
						rawcaplist.append(rawmov) #append it to our list of raw captures
				if rawcaplist:
					fflist[os.path.join(dirs,acc)] = sorted(rawcaplist) #add the list of ['rawcapture filenames'] to a dict key of 'full path to accession# on xcluster'
	log(logfile,str(fflist))
	return fflist
###END FFMPEG FILE LIST GENERATION###
###PROCCESS THE FILES WITH FFMPEG###
def ffprocess(acc,fflist,watermark,fontfile,scriptRepo,logfile):
	#concatenate startfiles into endfile.mov
	with cd(acc): #cd into it
		###INIT VARS###
		txtfile = open("concat.txt","w") #initialize a txt file that we'll use to concat
		for rawmov in fflist[acc]: #for each file name in the lsit of filenames associated with this accession#
			txtfile.write("file " + rawmov + "\n") #append the filename to the txt file with a newline
		txtfile.close() #housekeeping
		canonicalname = os.path.basename(acc) #set the canonical name of the recording, e.g. A2016_001_001_001.mov (first entry in list fflist[acc])
		segment = canonicalname.split("_")[-1] #the last set of chars in the sequence is the segment number
		flv = canonicalname + ".flv" #filename for flv
		mpeg = canonicalname + ".mpeg" #filename for mpeg
		mp4 = canonicalname + ".mp4" #filename for mp4
		mov = canonicalname + ".mov" #filename for mov
		###END INIT###
		###MAKE PRESERVATION MOV###	
		concatstr = 'ffmpeg -f concat -i concat.txt -map 0:v -map 0:a -c:v copy -c:a copy -timecode ' + segment[-2:] + ':00:00:00 rawconcat.mov'
		try:
			output = subprocess.check_output(concatstr,stderr=open(logfile,"a+"),shell=True) #concatenate them
			returncode = 0
			log(logfile, "concatenation of raw MOVs successful")
		except subprocess.CalledProcessError,e:
			output = e.output
			returncode = e.returncode
		if returncode > 0:
			#send email to staff
			msg = 'The concatenation of  ' + canonicalname + ' was unsuccessful\n'
			subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
			log(logfile,msg)
			sys.exit() #quit now because this concat is really important
		for rawmov in fflist[acc]: #for each raw file name in the list of concats that are the raw captures
			os.remove(rawmov) #delete them (they've been concatted into 1 big ol file successfully)
			if os.path.exists(rawmov + ".md5"): #if they have any associated files get rid of them
				os.remove(rawmov + ".md5")
			if os.path.exists("concat.txt"):
				os.remove("concat.txt") #also delete the txt file because we don't need it anymore
		
		#streamcopy audio stream 2 to a new mov
		stream2audioout	= 'ffmpeg -i rawconcat.mov -map 0:a:1 -map -0:d -map -0:v -c:a copy rawconcat-as2.mov'
		try:
			output = subprocess.check_output(stream2audioout,stderr=open(logfile,"a+"),shell=True) #concatenate them
			returncode = 0
			log(logfile, "concatenation of raw MOVs successful")
		except subprocess.CalledProcessError,e:
			output = e.output
			returncode = e.returncode
		if returncode > 0:
			#send email to staff
			msg = 'The streamcopy of audio stream 2 of ' + canonicalname + ' was unsuccessful\n'
			subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
			log(logfile,msg)
			sys.exit() #quit now because this concat is really important
		
		#re-wrap in another mov
		stream2audioin = 'ffmpeg -i rawconcat.mov -i rawconcat-as2.mov -map 0:v -map 0:a:0 -map 1:a:0 -map 0:d -c copy concat.mov'
		try:
			output = subprocess.check_output(stream2audioin,stderr=open(logfile,"a+"),shell=True) #concatenate them
			returncode = 0
			log(logfile, "re-wrap of audio stream 2 successful")
		except subprocess.CalledProcessError,e:
			output = e.output
			returncode = e.returncode
		if returncode > 0:
			#send email to staff
			msg = 'The re-wrap of audio stream 2 of  ' + canonicalname + ' was unsuccessful\n'
			subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
			log(logfile,msg)
			sys.exit() #quit now because this concat is really important
		
		#delete intermediate files
		os.remove("rawconcat.mov")
		os.remove("rawconcat-as2.mov")
		###END MAKE PRESERVATION MOV###
		###TRANSCODE ENDFILES###
		#endfile.flv + HistoryMakers watermark
		try:
			flvstr = 'ffmpeg -i concat.mov -i ' + watermark + ' -filter_complex "scale=320:180,overlay=0:0;[0:a:0][0:a:1]amerge=inputs=2[a]" -c:v libx264 -preset fast -b:v 700k -r 29.97 -pix_fmt yuv420p -c:a aac -ac 2 -map 0:v -map "[a]" -timecode ' + segment[-2:] + ':00:00:00 -threads 0 ' + flv
			output = subprocess.check_output(flvstr, stderr=open(logfile,"a+"), shell=True)
			returncode = 0
			log(logfile, "transcode to flv successful")
		except subprocess.CalledProcessError,e:
			output = e.output
			returncode = e.returncode
		if returncode > 0:
			#send email to staff
			msg = 'The transcode to ' + flv + ' was unsuccessful\n'
			subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
			log(logfile,msg)
			sys.exit()

		#endfile.mpeg + timecode
		drawtext = '"drawtext=fontfile=' + "'" + fontfile + "'" + ": timecode='" + segment[-2:] + "\:00\:00\:00'" + ': r=29.97: x=(w-tw)/2: y=h-(2*lh): fontcolor=white: fontsize=72: box=1: boxcolor=0x00000099'
		try:
			mpegstr = 'ffmpeg -i concat.mov -target ntsc-dvd -filter_complex "[0:a:0][0:a:1]amerge=inputs=2[a]" -b:v 5000k -vtag xvid -vf ' + drawtext + ',scale=720:480" -map 0:v -map "[a]" -ac 2 -threads 0 ' + mpeg
			subprocess.check_output(mpegstr,stderr=open(logfile,"a+"), shell=True)
			returncode = 0
			log(logfile, "transcode to mpeg successful")
		except subprocess.CalledProcessError,e:
			output = e.output
			returncode = e.returncode
		if returncode > 0:
			#send email to staff
			msg = 'The transcode to ' + mpeg + ' was unsuccessful\n'
			subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
			log(logfile,msg)
			sys.exit()

		#endfile.mp4 + timecode
		try:
			mp4str = 'ffmpeg -i concat.mov -c:v mpeg4 -b:v 372k -pix_fmt yuv420p -r 29.97 -vf ' + drawtext + ',scale=420:270" -filter_complex "[0:a:0][0:a:1]amerge=inputs=2[a]" -c:a aac -ar 44100 -ac 2 -map 0:v -map "[a]" -threads 0 ' + mp4
			subprocess.check_output(mp4str,stderr=open(logfile,"a+"), shell=True)
			returncode = 0
		except subprocess.CalledProcessError,e:
			output = e.output
			returncode = e.returncode
			log(logfile,"transcode to mp4 successful")
		if returncode > 0:
			#send email to staff
			msg = 'The transcode to ' + mp4 + ' was unsuccessful\n'
			subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
			log(logfile,msg)
			sys.exit()
		###END ENDFILE TRANSCODE###
		#rename concat.mov to our accession name
		if os.path.exists("concat.mov"):
			os.rename("concat.mov",mov)
###END FFMPEG FILE PROCESSING###
###MOVE AND HASH THE PROCESSED FILES###
def movevids(acc,sunnascopyto,sunnas,xendata,xendatacopyto,xcluster,scriptRepo,logfile):
	###INIT VARS###
	hashlist = {}
	extlist = [".mov",".flv",".mp4",".mpeg"]
	s = os.path.basename(acc)
	###END INIT###
	###MOVE AND HASH FILES###
	with cd(acc):
		#verify that everything exists
		if os.path.isfile(s + extlist[0]) and os.path.isfile(s + extlist[1]) and os.path.isfile(s + extlist[2]) and os.path.isfile(s + extlist[3]): #if each file extension exists in there
			###MOVE FILES TO SERVERS AND GRIP HASHES###
			#copy pres file to lc directory
			log(logfile,"copying archival master to lc folder\n")
			shutil.copy2(os.path.join(acc,s + ".mov"), os.path.join(xcluster,"toLC")) #copy the mov to xendata/copyto
			
			#move the mov file
			sys.stdout.flush()
			output = subprocess.Popen(["python",os.path.join(scriptRepo,"hashmove.py"),"-a","sha1","-np",os.path.join(acc,s + extlist[0]),xendatacopyto],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			hashes,err = output.communicate()
			log(logfile,hashes)
			sourcehash = re.search('srce\s\S+\s\w{40}',hashes)
			desthash = re.search('dest\s\S+\s\w{40}',hashes)
			dh = desthash.group()
			sh = sourcehash.group()
			if sh[-40:] == dh[-40:]:
				hashlist[s + extlist[0]] = sh[-40:]

			#move the flv file
			output = subprocess.Popen(["python",os.path.join(scriptRepo,"hashmove.py"),"-a","sha1","-np",os.path.join(acc,s + extlist[1]),sunnascopyto],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			hashes,err = output.communicate()
			log(logfile, hashes)
			sourcehash = re.search('srce\s\S+\s\w{40}',hashes)
			desthash = re.search('dest\s\S+\s\w{40}',hashes)
			dh = desthash.group()
			sh = sourcehash.group()
			if sh[-40:] == dh[-40:]:
				hashlist[s + extlist[1]] = sh[-40:]
			
			#move the mp4 file
			output = subprocess.Popen(["python",os.path.join(scriptRepo,"hashmove.py"),"-a","sha1","-np",os.path.join(acc,s + extlist[2]),sunnascopyto],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			hashes,err = output.communicate()
			log(logfile,hashes)
			sourcehash = re.search('srce\s\S+\s\w{40}',hashes)
			desthash = re.search('dest\s\S+\s\w{40}',hashes)
			dh = desthash.group()
			sh = sourcehash.group()
			if sh[-40:] == dh[-40:]:
				hashlist[s + extlist[2]] = sh[-40:]
			
			#move the mpeg file
			output = subprocess.Popen(["python",os.path.join(scriptRepo,"hashmove.py"),"-a","sha1","-np",os.path.join(acc,s + extlist[3]),xendatacopyto],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			hashes,err = output.communicate()
			log(logfile,hashes)
			sourcehash = re.search('srce\s\S+\s\w{40}',hashes)
			desthash = re.search('dest\s\S+\s\w{40}',hashes)
			dh = desthash.group()
			sh = sourcehash.group()
			if sh[-40:] == dh[-40:]:
				hashlist[s + extlist[3]] = sh[-40:]
			###END MOVE FILES AND GRIP HASHES###
			###DO FILEMAKER HASH STUFF###
			#send file hashes to filemaker
			updateFM(hashlist,scriptRepo,logfile)
			
			time.sleep(5) #give FM a chance to catch up
			
			#verify hashes
			moveyn = verifyFM(hashlist,scriptRepo,logfile)
			
			if moveyn is True:
				#move the files to various copytos
				output = subprocess.Popen(["mv",os.path.join(xendatacopyto,s + extlist[0]),os.path.join(xendata,s + extlist[0])],stdout=subprocess.PIPE,stderr=subprocess.PIPE) #copy the mov to xendata
				log(logfile,"moving archival master from copyto")
				output = subprocess.Popen(["mv",os.path.join(xendatacopyto,s + extlist[3]),os.path.join(xendata,s + extlist[3])],stdout=subprocess.PIPE,stderr=subprocess.PIPE) #copy the mpeg to xendata
				log(logfile,"moving mpeg from copyto")
				output = subprocess.Popen(["mv",os.path.join(sunnascopyto,s + extlist[1]),os.path.join(sunnas,s + extlist[1])],stdout=subprocess.PIPE,stderr=subprocess.PIPE) #copy the flv to sunnas
				log(logfile,"moving flv from copyto")
				output = subprocess.Popen(["mv",os.path.join(sunnascopyto,s + extlist[2]),os.path.join(sunnas,s + extlist[2])],stdout=subprocess.PIPE,stderr=subprocess.PIPE) #copy the mp4 to sunnas
				log(logfile,"moving mp4 from copyto")
			else:
				msg = "hashes in FileMaker do not match hashes calculated for one or more files. Files not moved from /copyto.\nSee included log for details"
				subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt', msg,'-att',logfile])
				log(logfile,msg)
			###END FILEMAKER HASH STUFF###		
		else:#if above didn't work, send accession directory to troubleshooting folder to examine later
			output = subprocess.Popen(["python",os.path.join(scriptRepo,"hashmove.py"),"-a","sha1","-np",acc,os.path.join(xcluster,"troubleshoot",s)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	###END MOVE AND HASH FILES###		
	###CLEANUP###
	#ok so the accession dir in the capture folder should be empty
	try:
		time.sleep(5) #give filetable time to catch up
		log(logfile,"removing " + os.path.join(acc,".DS_Store"))
		if os.path.exists(os.path.join(acc,".DS_Store")):
			os.remove(os.path.join(acc,".DS_Store"))
		log(logfile,"removing accession dir " + acc + " from IncomingQT")
		if os.path.exists(acc):
			os.rmdir(acc)
		#if it's not empty let's move it to a toubleshooting folder
	except:
		output = subprocess.Popen(["python",os.path.join(scriptRepo,"hashmove.py"),"-a","sha1","-np",acc,os.path.join(xcluster,"troubleshoot",s)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	###END CLEANUP###
###END MOVE AND HASH THE PROCESSED FILES###
###UPDATE FILEMAKER WITH HASH VALUES###
def updateFM(hashlist,scriptRepo,logfile):
	log(logfile,"sending hashes to filemaker")
	for fh in hashlist:
		fname,ext = os.path.splitext(fh)
		fdigi = ext.replace(".","") #format extension for THM FM field
		output = subprocess.Popen(["python",os.path.join(scriptRepo,"fm-stuff.py"),"-uSha","-id",fname,"-hash",hashlist[fh],"-fdigi",fdigi],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	return
###END FILEMAKER UPDATE###
###VERIFY HASHES IN FILEMAKER AND ON DISK###
def verifyFM(hashlist,scriptRepo,logfile):
	log(logfile,"verifying hashes in filemaker")
	verifiedwrong = [] #init var for list of files that dont verify correctly
	for fh in hashlist:
		fname,ext=os.path.splitext(fh)
		fdigi = ext.replace(".","")
		sys.stdout.flush() #clear the standard out of the CLI so we dont get any noise
		output = subprocess.Popen(["python",os.path.join(scriptRepo,"fm-stuff.py"),"-qSha","-id",fname,"-fdigi",fdigi],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		fmhash = output.communicate()
		if any(hashlist[fh] in foo for foo in fmhash): #success
			log(logfile,"hash of " + str(fh) + " verified correctly as: " + str(fmhash)) #print hashes to log
		else: #fail
			log(logfile,"hash of " + str(fh) + " verified incorrectly")
			log(logfile,"makevideos calculated hash of: " + hashlist[fh])
			log(logfile,"filemaker hash stored is: " + str(fmhash))
			verifiedwrong.append(str(fh))
	if verifiedwrong: #if a file didn't verify dont move it
		moveyn = False
	else:
		moveyn = True
	return moveyn
###END HASH VERIFY###
###WRITE MESSAGES TO A LOG FILE###	
def log(logfile,msg):
	with open(logfile,"ab") as txtfile:
		txtfile.write(time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime()))#give our logged msg a timestamp
		txtfile.write("\n")#newline
		txtfile.write(msg)#supplied message from calling fucntion
		txtfile.write("\n")
###END LOGFILE###
###MAIN FUNCTION CONTROLLER###
def main():
	###INIT VARS###
	scriptRepo = os.path.dirname(os.path.abspath(__file__))#get directory this script runs from
	config = ConfigParser.ConfigParser() #init a parser for our configuration file
	config.read(os.path.join(scriptRepo,"video-post-process-config.txt")) #read our configuration file w/ parser
	watermark = config.get('transcode','whitewatermark')
	fontfile = config.get('transcode','timecodefont')
	rawCaptures = config.get('transcode','rawCaptureDir')
	sunnascopyto = config.get('fileDestinations','sunnascopyto')
	sunnas = config.get('fileDestinations','sunnas')
	xendata = config.get('fileDestinations','xendata')
	xendatacopyto = config.get('fileDestinations','xendatacopyto')
	xcluster = config.get('fileDestinations','xcluster')
	logfile = os.path.join(scriptRepo,"logs","log-" + time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()) + ".txt")
	rawCaptures = rawCaptures.strip('"') #adjust for spaces in pathname
	xcluster = xcluster.strip('"')
	###END INIT###
	###DO THE THING###
	try: #ATTEMPTS THE FOLLOWING PROCESS
		#verifies our inputs
		startup(logfile,rawCaptures,watermark,fontfile,sunnas,sunnascopyto,xendata,xendatacopyto)
		
		#makes a list of files for ffmpeg to transcode
		fflist = makefflist(rawCaptures,logfile)
		
		#loops through list in filename order
		for acc in sorted(fflist):
			#actually transcode the files
			ffprocess(acc,fflist,watermark,fontfile,scriptRepo,logfile)

			#moves files from processing dirs to Xendata and SUNNAS
			#movevids(acc,sunnascopyto,sunnas,xendata,xendatacopyto,xcluster,scriptRepo,logfile)
			
			#log and email that this single accession was successful
			msg = "makevideos processed accession " + str(acc) + " successfully"
			subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt', msg])
			log(logfile,msg)
		
		###LOG AND EMAIL SUCCESS###
		msg = "makevideos completed successfully"
		subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt', msg,'-att',logfile])
		log(logfile,msg)
		###END SUCCESS###
	
	###IF ABOVE ATTEMPT FAILS DO THIS###
	except Exception,e: 
		print str(e)
		msg = "The script crashed due to an internal error\n"
		msg = msg + str(e)
		subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt', msg,'-att',logfile])
		log(logfile,msg)
		log(logfile,str(e))
	###end exception###
###END MAIN FUNCTION CONTROLLER###

dependencies()
main()
