#!/usr/bin/env python

###########
# Imports #
###########
import glob, sys, argparse, time, os

########
# Path #
########
PATH = '/Users/horak/JDA-scripts/kahoku/output/'

#######
# CLI #
#######
p = argparse.ArgumentParser(description='combine.py')
p.add_argument('-l', dest='location')
args = p.parse_args()
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
  read_path   = PATH + args.location.upper() + '_output/'
  result_path = read_path + 'combined-' + timestr + '.json'

  # Combine Files
  read_files = glob.glob(read_path + '*.json')
  with open(result_path, 'wb') as outfile:
    outfile.write('{}'.format(' '.join([open(f, "rb").read() for f in read_files])))
	
  # Prepend "Items" string
  with file(result_path, 'r') as original: data = original.read()
  with file(result_path, 'w') as modified: modified.write('{"items": [' + data)

  # Remove hanging comma
  with open(result_path, 'rb+') as modified:
    modified.seek(-2, os.SEEK_END)
    modified.truncate()

  # Append end of file formatting
  with open(result_path, 'a') as modified: modified.write(']}')

else:
  print 'Unpredicted error.'
  sys.exit(1)
