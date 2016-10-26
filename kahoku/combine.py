#!/usr/bin/env python

###########
# Imports #
###########
import glob, sys, argparse, time, os, fnmatch

##############
# IMPORTANT! #
## Set Path ##
##############
PATH = '/Users/horak/JDA-scripts/kahoku/output/'

#######
# CLI #
#######
p = argparse.ArgumentParser(description='combine.py')
p.add_argument('-l', dest='location')
args  = p.parse_args()
legal = ['image', 'document', 'movie', 'other']

#################
# Handle Errors #
##################
if args.location == None:
  print 'Must indicate a location: ie: image, document, movie, other.'
  sys.exit(1)

if args.location not in legal:
  print 'Please specify a legal location. ie: image, document, movie, other.'
  sys.exit(1)

########
# Main #
########
if args.location:
  timestr     = time.strftime('%Y%m%d-%H%M%S')
  folder_path = PATH + args.location.upper() + '_output/'
  file_path   = folder_path + 'combined-' + timestr + '.json'

  # Combine Files
  read_files = glob.glob(folder_path + '*.json')
  with open(file_path, 'wb') as outfile:
    outfile.write('{}'.format(' '.join([open(f, "rb").read() for f in read_files])))
	
  # Prepend "Items" string
  with file(file_path, 'r') as original: data = original.read()
  with file(file_path, 'w') as modified: modified.write('{"items": [' + data)

  # Remove hanging comma
  with open(file_path, 'rb+') as modified:
    modified.seek(-2, os.SEEK_END)
    modified.truncate()

  # Append end of file formatting
  with open(file_path, 'a') as modified: modified.write(']}')

  # And finish by removing the individual un-combined files
  for f in os.listdir(folder_path):
    if fnmatch.fnmatch(f, '*.json') and not fnmatch.fnmatch(f, 'combined-*'):
      os.remove(folder_path + f)
      
  print '****** Combined ' + args.location +'s ******'

else:
  print 'Unpredicted error.'
  sys.exit(1)
