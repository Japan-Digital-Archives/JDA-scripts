#!/usr/bin/env python

###########
# Imports #
###########
from scrapy.spider import BaseSpider
from scrapy.selector import XmlXPathSelector
from scrapy.http import Request
import urllib, json, contextlib, os, glob, time
from helpers import *

class XmlSpider(BaseSpider):

  ##############
  # IMPORTANT! #
  ## Set Path ##
  ##############
  PATH         = '/Users/horak/JDA-scripts/kahoku/output/'
  template_url = 'http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set='

  ######################
  # Customimze Scraper #
  ######################
  def __init__(self, cat='', *a, **kw):
    super(XmlSpider, self).__init__(*a, **kw)
    
    # Use category arg to determine which type of page to scrape (document, image, ...) 
    category = cat.upper()

    # Persist category type and set paths
    setCAT(cat)
    output_path = self.PATH + category.lower() + '_output/'
    token_path  = output_path + '.previous_resumption_token'

    # Create URL to scrape
    url = self.template_url + category

    # Continue scraping where we left off (if we did)
    tokenFileExists = os.path.exists(token_path)
    if tokenFileExists:
      token = open(token_path, 'r').read()
      url   = url + '&resumptionToken=' + token
      print '****** RESUMING WITH TOKEN: ' + token + ' ******' 

    self.start_urls[0] = url

  ################
  # Scraper Init #
  ################
  name            = 'xmlscrape'
  allowed_domains = ['kahoku-archive.shinrokuden.irides.tohoku.ac.jp']
  start_urls      = ['http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE']

  ##############
  # Parse Feed #
  ##############
  def parse(self, response):

    #########
    # Setup #
    #########
    x = XmlXPathSelector(response)
    x.remove_namespaces()
    x.register_namespace('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')

    category     = getCAT()
    category     = category.upper()
    output_path  = self.PATH + category.lower() + '_output/'
    token_path   = output_path + '.previous_resumption_token'
    dup_path     = output_path + '.dup_list'
    items        = []
    items        = x.select('//record/metadata/RDF')
    result       = []
    id_list      = []
    nextFileLink = ''

    resumption_token = x.select('//resumptionToken/text()').extract()
    saveResumptionToken(resumption_token, token_path)

    ###############
    # Parse Items #
    ###############
    print '****** PARSING FILE... ******'
    for item in items:

      ####################
      ##### creator ######
      ##### archive ######
      #### layer_type ####
      ####################
      media_creator_username = 'Kahoku Shimpo Publishing Co.'
      archive                = 'Kahoku Shimpo Disasters Archive'
      layer_type             = 'Image' 

      ####################
      #### media_type ####
      ####################
      if category == 'MOVIE': media_type = 'Video'
      if category == 'DOCUMENT' or category == 'OTHER': media_type = 'Headline'
      if category == 'IMAGE': media_type = 'Image'

      ######################
      # media_date_created #
      ######################
      media_date_created = item.select('Resource/created/text()').extract()
      media_date_created = processField(media_date_created)

      ##################
      #### abstract ####
      ##### title ######
      ##################
      abstract = item.select('Resource/abstract/text()').extract()
      title    = item.select('Resource/title/text()').extract()
      title    = processField(title)
      abstract = processField(abstract)
      abstract = abstract.replace('\r\n', '')

      # Abstract tends to be more unique, though not always there. Title is often repetitive but more consistently present.
      if not abstract: abstract = title

      ###################
      #### unique_id ##### 
      ###################
      unique_id = item.select('Resource/identifier/text()').extract()
      unique_id = str(unique_id[0])
      # Used for de-duping
      id_list.append(unique_id)

      ####################
      ###### Source ###### 
      ####################
      source = item.select('Resource/@rdf:about').extract()
      source = processField(source)

      ####################
      ####### URI ######## 
      ####################
      # Download image if it has not already been downloaded
      if category == 'IMAGE':
      	uri = item.select('Resource/screen/Image/@rdf:about').extract()
      	downloaded = os.path.exists(output_path + unique_id + '.jpg')
      	if uri and not downloaded:
      	  uri = uri[0]
      	  urllib.urlretrieve(uri, output_path + unique_id + '.jpg')
      	  uri = 'https://s3.amazonaws.com/JDA-Files/' + unique_id
      
      if category == 'MOVIE':
      	uri = item.select('Resource/ogg/Image/@rdf:about').extract()
	      
      if category == 'DOCUMENT' or category == 'OTHER':
      	uri = source

      uri = processField(uri)

      ####################
      #### Thumbnail ##### 
      ####################
      thumbnail_url = item.select('Resource/thumbnail/Image/@rdf:about').extract()
      thumbnail_url = processField(thumbnail_url)

      ####################
      ####### Tags ####### 
      ####################
      tags = item.select('Resource/subject/Description/value/text()').extract()
      if not tags:
        tags_string = '[]'
      else:
        tags_string = '"' + '", "'.join(tags) + '"'

      ####################
      ##### Location ##### 
      ####################
      region           = item.select('Resource/spatial/Description/region/text()').extract()
      locality         = item.select('Resource/spatial/Description/locality/text()').extract()
      street_address   = item.select('Resource/spatial/Description/street-address/text()').extract()

      if region or locality or street_address:
        region         = processField(region)
        locality       = processField(locality)
        street_address = processField(street_address)
        locationTemp   = [street_address, locality, region]
        location       = ''

        # Handles comma location and attribute existence variability
        for item in locationTemp:
          if item:
            if location == '':
              location = location + item
            else:
              location = location + ', ' + item
        if location[location.__len__()-1] == ',':
          location = location[:-1]
      else:
        location = ''

      ##########################
      ######## Lat/Long ########
      ##########################
      # Find coordinates using Google Maps API
      lat = '' 
      lng = ''
      if location != '':
        key                = '&key=AIzaSyCGF2BwNPNckrbx6L2tQRATBcjKv0C3xCo'
        google_uri         = 'https://maps.googleapis.com/maps/api/geocode/json?address=' 
        location_encoded   = location.encode('utf8')
        location_url_ready = urllib.quote_plus(location_encoded, safe='')
        request_uri        = google_uri + location_url_ready + key 
        with contextlib.closing(urllib.urlopen(request_uri)) as response:
          data = json.load(response)
          if json.dumps(data['results']) != '[]':
            lat = json.dumps(data['results'][0]['geometry']['location']['lat'])
            lng = json.dumps(data['results'][0]['geometry']['location']['lng'])
          else:
            lat = 'null' 
            lng = 'null'

      ##########################
      ######## JSONify #########
      ##########################
      json_entry = ( '{"title": "' 
        + abstract + '", "uri": "' 
        + uri + '", "attribution_uri": "' 
        + source + '", "media_date_created": "' 
        + media_date_created + '", "media_creator_username": "' 
        + media_creator_username + '", "thumbnail_url": "' 
        + thumbnail_url + '", "media_geo_latitude": "' 
        + lat + '", "media_geo_longitude": "' 
        + lng + '", "location": "' 
        + location + '", "tags": [' 
        + tags_string + '], "archive": "' 
        + archive + '",  "media_type": "'
        + media_type + '", "layer_type": "'
        + layer_type + '", "child_items_count": 0, "published": 1}, '
      )

      #####################
      # Duplicate Checker #
      #####################
      # Check for duplicates only in the "final-..." file since that is the only 
      # file without a resumption token and thus could possibly contain duplicates.
      if not resumption_token and os.path.exists(dup_path):
        dup_list = open(dup_path, 'r').read()
        if unique_id not in dup_list:
          print 'not in dup'
          result.append(json_entry)
      else:
        result.append(json_entry)


    ###################
    # Save Duplicates #
    ###################
    # Save Item URI List
    with open(dup_path, 'w+r') as f:
      print '****** (OVER)WRITING DEDUP LIST ******'
      f.truncate() 
      for item in id_list:
        print>>f, item
      f.close() 

    ###########
    # If Done #
    ###########
    if resumption_token == []:
      print '****** DONE ******'
      nextFileLink = ""
      path = output_path + 'final-' + getDateString() + '.json'
      open(path, 'wb').write(''.join(result).encode('UTF-8'))
      removeEmptyFiles(output_path)

    ###############
    # Or Next Job #
    ###############
    else: 
      url          = self.template_url + category + '&resumptionToken='
      nextFileLink = url + resumption_token[0].encode('ascii')
      path         = output_path + resumption_token[0].encode('ascii') + '.json'

      open(path, 'wb').write(''.join(result).encode('UTF-8'))
      yield Request(nextFileLink, callback = self.parse)
