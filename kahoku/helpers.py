################
# Helper Files #
################

import time, os

def setCAT(cat):
	path = '/Users/horak/JDA-scripts/kahoku/output/category'
	with open(path, 'w+') as f:
		print '****** SCRAPING ' + cat + 's *******'		
		f.truncate()
		f.write(cat)
		f.close()

def getCAT():
	path = '/Users/horak/JDA-scripts/kahoku/output/category'
	with open(path, 'r+') as f:
		data = f.read()
		return data
		f.close()

def rmCAT():
	path = '/Users/horak/JDA-scripts/kahoku/output/category'
	os.remove(path)

def removeEmptyFiles(output_path):
	for filename in os.listdir(output_path):
		if os.stat(output_path + filename).st_size == 0:
			os.remove(output_path + filename)

def getDateString():
	timestr = time.strftime('%Y%m%d-%H%M%S') 
	return timestr

def handleNull(field):
	if not field:
		field = ''
	else:
		field = field[0]
	return field

def saveResumptionToken(token, path):
	if token:
		with open(path, 'w+r') as f:
			print '****** (OVER)WRITING RESUMPTION TOKEN: ' + token[0] + ' ******'
  			f.truncate()
		  	f.write(token[0])
  			f.close() 
	else:
		print '****** NO RESUMPTION TOKEN: FINAL RESPONSE PAGE ******'
