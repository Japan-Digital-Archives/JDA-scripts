################
# Helper Files #
################

import time, os

##############
# IMPORTANT! #
## Set Path ##
##############
global PATH
PATH = '/Users/horak/JDA-scripts/kahoku/output/.category'

# Sets the category type
def setCAT(cat):
	global PATH
	with open(PATH, 'w+') as f:
		print '****** SCRAPING ' + cat + 's *******'		
		f.truncate()
		f.write(cat)
		f.close()

# Returns and removes category type
def getCAT():
	global PATH
	with open(PATH, 'r+') as f:
		data = f.read()
		return data
		f.close()
	os.remove(PATH) # Then remove in preparation for the next call

def removeEmptyFiles(output_path):
	for filename in os.listdir(output_path):
		if os.stat(output_path + filename).st_size == 0:
			os.remove(output_path + filename)

def getDateString():
	timestr = time.strftime('%Y%m%d-%H%M%S') 
	return timestr

# Returns a string and handles null 
def processField(field):
	if not field: field = ''
	else:
		if isinstance(field, list): return field[0]
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
