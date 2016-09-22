#!/usr/bin/env python

try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET
try:
       # Python 2.6-2.7
       from HTMLParser import HTMLParser
except ImportError:
       # Python 3
       from html.parser import HTMLParser

import os
import glob
import json
import re
import urllib
from dateutil.parser import parse
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# Set location to store .json and .jpg files.
# This location should match the location that pullDownFeed downloads .xml files.
PATH = "/var/www/alex/asahi_rss_test/feed"

# Iterate through each asahi rss xml file, convert each item within it to single json
# file, thus elliminating duplicates, and then remove the xml files.
filepath = os.path.join(PATH, "*.xml")
for filename in glob.iglob(filepath):

	# Extract text from filename
	f = open(filename, "r")
	dataxml = f.read()

	# Create XML tree from NITF document
	parser = ET.XMLParser(encoding="utf-8")
	root = ET.fromstring(dataxml)

	# Create a list for within-the-same-file item duplication checking
	duplicate_item_list = []

	# Iterate through each item within the file and process metadata
	for item in root.findall(".//item"):

		#######
		# uri #
		#######
		uri = item.find("link").text

		################
		# id_at_source #
		################
		temp_uri = uri.split("/")[-1]
		id_at_source = temp_uri.split(".")[0]

		# Do not proceed if file already exists
		id_path = os.path.join(PATH, id_at_source) + ".json"
		if (os.path.exists(id_path)) or (id_at_source in duplicate_item_list):
			break
		else:
			duplicate_item_list.append(id_at_source)

			########
			# Date #
			########
			article_date = item.find("pubDate").text
			article_date = parse(article_date)
			article_date = str(article_date)

			############
			# Headline #
			############
			article_headline = item.find("title").text

			########
			# Text #
			########
			article_text_unformatted = item.find("description").text
			article_text_unformatted = str(article_text_unformatted)
			# replace included full width parens with normal parens
			article_text_unformatted = re.sub(ur'[\xef\xbc\x88]+', '(', article_text_unformatted)
			article_text_unformatted = article_text_unformatted[:-3]+ ')'
			# ... and remove author string from article_fulltext
			article_text_unformatted_regex = re.compile('.*>')
			article_text_formatted = article_text_unformatted_regex.findall(article_text_unformatted)[0]

			##########
			# Author #
			##########
			# Grab author string by looking for last closing </p> tag...
			author_regex = re.compile('(?!.*>).')
			author = author_regex.findall(article_text_unformatted)
			# and collapse the resulting array of captured groups
			author = ''.join(author)
			# remove end parentheses
			author = author.replace('(', '')
			author = author.replace(')', '')
			# remove the "By" that may precede the author string
			author_clean_regex = re.compile('(?<=[Bb]y ).*')
			author = author_clean_regex.findall(author)[0]
			# and the "/..." that could follow.
			author_clean_regex2 = re.compile('.*(?=/)')
			article_author = author_clean_regex2.findall(author)[0]

			#########
			# Photo #
			#########
			article_photo = ''
                        # Does the item include a photo?
			if item.find("enclosure") is not None:
				photo_text = root.find(".//enclosure").text
				photo_url_original = item.find("enclosure").attrib.get("url")
				photo_filename = photo_url_original.split('/')[-1]
				photo_fullfilename = os.path.join(PATH, photo_filename)
				# download photo into directory
				urllib.urlretrieve(photo_url_original, photo_fullfilename)
                                # and reference its future s3 location
				article_photo = "https://s3.amazonaws.com/JDA-Files/" + photo_filename

			###########
			# JSONify #
			###########
			name = id_at_source + '.json'
			storagePath = os.path.join(PATH, name)
			current_file = open(path, 'a')

			current_file.write('{"items": [')

			article_headline =       json.dumps(article_headline, ensure_ascii=False)
			article_text_formatted = json.dumps(article_text_formatted, ensure_ascii=False)
			id_at_source =           json.dumps(id_at_source, ensure_ascii=False)
			article_photo =          json.dumps(article_photo, ensure_ascii=False)
			article_date =           json.dumps(article_date, ensure_ascii=False)
			uri =                    json.dumps(uri, ensure_ascii=False)
			article_author =         json.dumps(article_author, ensure_ascii=False)

			json_data = '{"title": "' + article_headline[1:-1] + '", "text": "' + article_text_formatted[1:-1] + '", "uri": "' + uri[1:-1] + '", "attribution_uri": "' + uri[1:-1] + '", "archive": "Asahi Asia & Japan Watch", "media_type": "Article", "layer_type": "Article", "image_url": "", "thumbnail_url": "' + article_photo[1:-1] + '", "child_items_count": 0' + ', "location": "", "media_date_created": "' + article_date[1:-1] + '", "media_creator_username": "' + article_author[1:-1] + '", "media_creator_realname": "' + article_author[1:-1] + '", "license": "", "attributes": [], "child_items": [], "tags": [], "id_at_source": "' + id_at_source[1:-1] + '", "published": 1}'

			current_file.write(json_data.encode('utf-8'))
			current_file.write(']}')
			current_file.close()

	# delete xml files
	if filename:
		os.remove(filename)
