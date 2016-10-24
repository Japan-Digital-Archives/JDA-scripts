################
# Helper Files #
################

import time, os

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

def saveResumptionToken(token, token_path):
	if token:
		with open(token_path, 'w+r') as f:
			print '****** (OVER)WRITING RESUMPTION TOKEN: ' + token[0] + ' ******'
  			f.truncate()
		  	f.write(token[0])
  			f.close() 
	else:
		print '****** NO RESUMPTION TOKEN: FINAL RESPONSE PAGE ******'
