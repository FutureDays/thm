#! /usr/bin/python
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
	return

def startup(logfile,rawCaptures,watermark,fontfile,sunnas,sunnascopyto,xendata,xendatacopyto):
	log(logfile,"running")
	
	#see if the process is already running
	#try:
		#x = open(os.path.join(os.path.dirname(os.path.dirname(logfile)),"processing.pid"))
		#fcntl.lockf(x, fcntl.LOCK_EX | fcntl.LOCK_NB)
	#except:
		#log(logfile,"quit, process already running")
		#sys.exit()
	#time.sleep(500)
	#check that there's stuff to work on even
	rawCapList = []
	for f in os.listdir(rawCaptures):
		if not f.startswith('.'):
			rawCapList.append(f)

	if not rawCapList:
		msg = "completed. nothing to process"
		log(logfile,msg)
		sys.exit()

	#check that the files are where we think thye are
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
	
	#check that everything is plugged in
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
	
	#check that nothing is being copied currently
	donezo = False
	while donezo is False:
		fs = walk(rawCaptures)
		#print fs
		time.sleep(240)
		fsagain = walk(rawCaptures)
		#print fsagain
		donezo = compare(fs, fsagain)
		#print donezo

	#check that a filemaker record exists for each accession
	for dirs,subdirs,files in os.walk(rawCaptures):
			for s in subdirs:
				output = subprocess.Popen(["python","fm-stuff.py","-qExist","-id",s],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				out,err = output.communicate()
				if not out:
					msg = "The video script is unable to run because there is not an accession record for " + s + " in FileMaker"
					subprocess.call(["python","send-email.py","-txt",msg,'-att',logfile])
					log(logfile,msg)	
					sys.exit()
	
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



#following three functions are called in startup to check that nothing is being copied currently
def sizeloop(thing):
	#print thing
	startsize = os.stat(thing)
	#print startsize.st_size
	time.sleep(1)
	endsize = os.stat(thing)
	#print endsize.st_size
	if startsize.st_size == endsize.st_size:
		return
	else:
		sizeloop(thing)

def walk(pth):
	thefiles =[]	
	for dirs, subdirs, files in os.walk(pth):
		for files in files:
			fullpath = os.path.join(dirs,files)
			thefiles.append(fullpath)
	#print thefiles
	for f in thefiles:
		fpath = os.path.join(pth,f)
		sizeloop(fpath)
	return thefiles

def compare(fs, fsagain):
	#print fs
	#print fsagain
	for f in fsagain:
		if not f in fs:
			return False
	return True

def validateInputVideos(fflist,scriptRepo,logfile):
	accInvalidList = []
	for acc in fflist:
		with cd(acc):
			for rawmov in fflist[acc]:
				_pass, output = validateVideo(os.path.join(acc,rawmov),scriptRepo,logfile)
				if not _pass:
					msg = "The file " + os.path.join(acc,rawmov) + " is not a valid input for makevideos, this accession skipped\n"
					msg = msg + str(output)
					subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
					log(logfile,msg)
					accInvalidList.append(acc)
				else:
					log(logfile,"the input video " + os.path.join(acc,rawmov) + " is a valid input for makevideos")	
	for acc in accInvalidList:
		fflist.pop(acc, None) #remove from the list of files to process
	return fflist					

def validateOutputVideo(acc,scriptRepo,logfile):
	for video in os.path.listdir(acc):
		_pass, output = validateVideo(os.path.join(acc,video),scriptRepo,logfile)
		if not _pass:
			msg = "The file " + os.path.join(acc,video) + " is not a valid output, this accession not moved from IncomingQT\n"
			msg = msg + str(output)
			subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
			log(logfile,msg)
			return False
		else:
			log(logfile,"the input video " + os.path.join(acc,rawmov) + " is a valid input for makevideos")
			return True

def validateVideo(fullPath,scriptRepo,logfile):
	try:
		output = subprocess.check_output(["python",os.path.join(scriptRepo,"validatevideos.py"),"-so",fullPath],stderr=open(logfile,"a+"))
		returncode = 0
	except subprocess.CalledProcessError,e:
		output = e.output
		returncode = e.returncode
	if returncode > 0:
		#send email to staff
		msg = 'The validation of  ' + fullPath + ' was unsuccessful\n'
		subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
		log(logfile,msg)
		sys.exit() #quit now because if we can't validate the vids we can't process them	
	elif output.startswith("fail"):
		return False, output
	elif output.startswith("pass"):
		return True, output
	else:
		msg = 'The validation of  ' + fullPath + ' was unsuccessful\n'
		msg = msg + output
		subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
		log(logfile,msg)
		sys.exit() #quit now because something weird happened		
	
def ffprocess(acc,fflist,watermark,fontfile,scriptRepo,logfile):
	#concatenate startfiles into endfile.mov
	with cd(acc): #cd into it
		txtfile = open("concat.txt","w") #initialize a txt file that we'll use to concat
		for rawmov in fflist[acc]: #for each file name in the lsit of filenames associated with this accession#
			txtfile.write("file " + rawmov + "\n") #append the filename to the txt file with a newline
		txtfile.close() #housekeeping
		canonicalname = os.path.basename(acc) #set the canonical name of the recording, e.g. A2016_001_001_001.mov (first entry in list fflist[acc])
		segment = canonicalname.split("_")[-1] #the last set of chars in the sequence is the segment number
		flv = canonicalname + ".flv" #filename for flv
		mpeg = canonicalname + ".mpeg" #filename for mpeg
		mp4 = canonicalname + ".mp4" #filename for mp4
		mov = canonicalname + ".mov"
			
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
		
		#transcode endfiles
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
		#easier to init this var here rather than include it in the ffmpeg call
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
			log(logfile,"transcode to mp4 successful")
		except subprocess.CalledProcessError,e:
			output = e.output
			returncode = e.returncode
		if returncode > 0:
			#send email to staff
			msg = 'The transcode to ' + mp4 + ' was unsuccessful\n'
			subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
			log(logfile,msg)
			sys.exit()
		if os.path.exists("concat.mov"):
			os.rename("concat.mov",mov)
		
		#make qctools report for mov
		try:
			subprocess.check_output(['qcli','-i',mov,'-o','/Volumes/G-SPEED Q/Titan-HD/HM/thm/qctools-reports/' + mov + '.qctools.xml.gz'])
			returncode = 0
			log(logfile, "generated QCTools report")
		except subprocess.CalledProcessError,e:
			output = e.output
			returncode = e.returncode
		if returncode > 0:
			#send email to staff
			msg = "makevideos could not generate a QCTools report for " + mov + "\n"
			subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt',msg,'-att',logfile])
			log(logfile,msg)	
	return	

def movevids(acc,sunnascopyto,sunnas,xendata,xendatacopyto,xcluster,scriptRepo,logfile):
	hashlist = {}
	extlist = [".mov",".flv",".mp4",".mpeg"]
	s = os.path.basename(acc)
	with cd(acc):
		if os.path.isfile(s + extlist[0]) and os.path.isfile(s + extlist[1]) and os.path.isfile(s + extlist[2]) and os.path.isfile(s + extlist[3]): #if each file extension exists in there
			
			#copy pres file to lc directory
			log(logfile,"copying archival master to lc folder\n")
			shutil.copy2(os.path.join(acc,s + ".mov"), os.path.join(xcluster,"toLC")) #copy the mov to xendata/copyto
			
			
			#move the mov files
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
			#print "moving flv file"
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
			#print "moving mp4 file"
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
			#print "moving mpeg file"
			output = subprocess.Popen(["python",os.path.join(scriptRepo,"hashmove.py"),"-a","sha1","-np",os.path.join(acc,s + extlist[3]),xendatacopyto],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			hashes,err = output.communicate()
			log(logfile,hashes)
			sourcehash = re.search('srce\s\S+\s\w{40}',hashes)
			desthash = re.search('dest\s\S+\s\w{40}',hashes)
			dh = desthash.group()
			sh = sourcehash.group()
			if sh[-40:] == dh[-40:]:
				hashlist[s + extlist[3]] = sh[-40:]
			
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
		else:
			output = subprocess.Popen(["python",os.path.join(scriptRepo,"hashmove.py"),"-a","sha1","-np",acc,os.path.join(xcluster,"troubleshoot",s)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			
	#cd out of accession dir
	#ok so the accession dir in the capture folder should be empty
	try:
		time.sleep(5)
		log(logfile,"removing " + os.path.join(acc,".DS_Store"))
		if os.path.exists(os.path.join(acc,".DS_Store")):
			os.remove(os.path.join(acc,".DS_Store"))
		log(logfile,"removing accession dir " + acc + " from IncomingQT")
		if os.path.exists(acc):
			os.rmdir(acc)
		#if it's not empty let's move it to a toubleshooting folder
	except:
		output = subprocess.Popen(["python",os.path.join(scriptRepo,"hashmove.py"),"-a","sha1","-np",acc,os.path.join(xcluster,"troubleshoot",s)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	return

def updateFM(hashlist,scriptRepo,logfile):
	log(logfile,"sending hashes to filemaker")
	for fh in hashlist:
		fname,ext = os.path.splitext(fh)
		fdigi = ext.replace(".","")
		output = subprocess.Popen(["python",os.path.join(scriptRepo,"fm-stuff.py"),"-uSha","-id",fname,"-hash",hashlist[fh],"-fdigi",fdigi],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	return

def verifyFM(hashlist,scriptRepo,logfile):
	log(logfile,"verifying hashes in filemaker")
	verifiedwrong = []
	for fh in hashlist:
		fname,ext=os.path.splitext(fh)
		fdigi = ext.replace(".","")
		sys.stdout.flush()
		output = subprocess.Popen(["python",os.path.join(scriptRepo,"fm-stuff.py"),"-qSha","-id",fname,"-fdigi",fdigi],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		fmhash = output.communicate()
		if any(hashlist[fh] in foo for foo in fmhash):
			log(logfile,"hash of " + str(fh) + " verified correctly as: " + str(fmhash))
		else:
			log(logfile,"hash of " + str(fh) + " verified incorrectly")
			log(logfile,"makevideos calculated hash of: " + hashlist[fh])
			log(logfile,"filemaker hash stored is: " + str(fmhash))
			verifiedwrong.append(str(fh))
	if verifiedwrong:
		moveyn = False
	else:
		moveyn = True
	return moveyn

def lowercase(rawCaptures):
	for dirs, subdirs,files in os.walk(rawCaptures):
		for f in files:
			flower = f.lower()
			os.rename(os.path.join(dirs, f), os.path.join(dirs,flower))
			
def log(logfile,msg):
	with open(logfile,"ab") as txtfile:
		txtfile.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
		txtfile.write("\n")
		txtfile.write(msg)
		txtfile.write("\n")

def main():
	#initialize a buncha paaths to various resources
	scriptRepo = os.path.dirname(os.path.abspath(__file__))
	config = ConfigParser.ConfigParser()
	config.read(os.path.join(scriptRepo,"video-post-process-config.txt"))
	watermark = config.get('transcode','whitewatermark')
	fontfile = config.get('transcode','timecodefont')
	rawCaptures = config.get('transcode','rawCaptureDir')
	sunnascopyto = config.get('fileDestinations','sunnascopyto')
	sunnas = config.get('fileDestinations','sunnas')
	xendata = config.get('fileDestinations','xendata')
	xendatacopyto = config.get('fileDestinations','xendatacopyto')
	xcluster = config.get('fileDestinations','xcluster')
	logfile = os.path.join(scriptRepo,"logs","log-" + time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()) + ".txt")
	
	rawCaptures = rawCaptures.strip('"')
	xcluster = xcluster.strip('"')
	
	try:
		#startup(logfile,rawCaptures,watermark,fontfile,sunnas,sunnascopyto,xendata,xendatacopyto)
		
		#lowercases the MOV that comes off the xdcam
		lowercase(rawCaptures)
		 
		#makes a list of files for ffmpeg to transcode
		fflist = makefflist(rawCaptures,logfile)
		print sorted(fflist)
		
		fflist = validateInputVideos(fflist,scriptRepo,logfile)

		for acc in sorted(fflist):
			validateInputVideos(acc,fflist,scriptRepo,logfile)
			
			#actually transcode the files
			ffprocess(acc,fflist,watermark,fontfile,scriptRepo,logfile)
			
			_pass = validateOutputVideos(acc,scriptRepo,logfile)
			
			if _pass:
				print "here"
				foo = raw_input("eh")
				#hashmove
				movevids(acc,sunnascopyto,sunnas,xendata,xendatacopyto,xcluster,scriptRepo,logfile)
			
				#notify that it worked for single accession
				msg = "makevideos processed accession " + str(acc) + " successfully"
				subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt', msg])
				log(logfile,msg)
			else:
				continue
				
		msg = "makevideos completed successfully"

		subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt', msg,'-att',logfile])
		log(logfile,msg)

	except Exception,e:
		print str(e)
		msg = "The script crashed due to an internal error\n"
		msg = msg + str(e)
		subprocess.call(['python',os.path.join(scriptRepo,"send-email.py"),'-txt', msg,'-att',logfile])
		log(logfile,msg)
		log(logfile,str(e))
	return

dependencies()
main()
