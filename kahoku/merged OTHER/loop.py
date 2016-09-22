#################################################
# This script is for concatenating the contents 
# of the scraped contents of the Kahoku Shimpo 
# Disaster Archive. Run it with '$ python loop.py'
#################################################

import os
import glob

read_files = glob.glob("*.json")
with open("merged_file.json", "wb") as outfile:
    outfile.write('[{}]'.format(
        ' '.join([open(f, "rb").read() for f in read_files])))

print('done')
