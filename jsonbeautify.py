# jsonbeautify.py 
import sys 
import simplejson as json 

if len(sys.argv) != 2: 
	print 'Usage: jsonbeautify.py infile > outfile' 
else: 
	fname = sys.argv[1] 
	with open(fname,'r') as f: 
		data = json.load(f) 
		print json.dumps(data, sort_keys=True, indent=4)
