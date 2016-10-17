#################################################
# This script is for concatenating the contents
# of the scraped contents of the Kahoku Shimpo
# Disaster Archive.
#################################################
import glob, sys, argparse

p = argparse.ArgumentParser(description='loop.py')
p.add_argument('-l', dest='location')

args = p.parse_args()
legal = ['image', 'document', 'movie', 'other']

# Handle Errors
if args.location == None:
    print 'Must indicate a location: ie: image, document, movie, other.'
    sys.exit(1)
if args.location not in legal:
    print 'Please specify a legal location. ie: image, document, movie, other.'
    sys.exit(1)


if args.location:
	path = '/Users/horak/Dropbox/JDA/JDA-scripts/kahoku/' + args.location + '_output/'

	read_files = glob.glob(path + '*.json')
	with open(path + 'merged_file.json', 'wb') as outfile:
	    outfile.write('[{}]'.format(
	        ' '.join([open(f, "rb").read() for f in read_files])))
else:
    print 'Unpredicted error.'
    sys.exit(1)
