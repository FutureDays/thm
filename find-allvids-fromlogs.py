import re
import os
import zipfile
import ast

thisdir = os.path.dirname(__file__)
logdir = os.path.join(thisdir,'thm-logs')
acctxt = open(os.path.join(thisdir,"acc-full-list.txt"),"a")
for txtf in os.listdir(logdir):
	print txtf
	with open(os.path.join(logdir,txtf)) as f:
		content = f.readlines()
	content = [x.strip() for x in content]
	try:
		d = ast.literal_eval(content[3])
		for key,value in d.iteritems():
			print key.replace("/Volumes/G-SPEED Q/Titan-HD/HM/IncomingQT/","").replace("/Volumes/G-SPEED Q/Titan-HD/HM/IncomingSC/","")
			acctxt.write(key.replace("/Volumes/G-SPEED Q/Titan-HD/HM/IncomingQT/","").replace("/Volumes/G-SPEED Q/Titan-HD/HM/IncomingSC/","") + "\n")
			print ""
	except:
		pass