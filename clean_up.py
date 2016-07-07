#################################################
# This script is for cleaning up a json file for
# import
#################################################

import os
import glob


read_files = glob.glob("merged_file.json")
with open("merged_file.json", "rb+") as outfile:
  content = outfile.read()
  line = '{ "items": '
  outfile.seek(0,0)
  outfile.write(line + content)

  outfile.seek(-3, os.SEEK_END) # remove the ", " at the end
  outfile.truncate()
  outfile.seek(-1, os.SEEK_END)
  outfile.write("}]}")

