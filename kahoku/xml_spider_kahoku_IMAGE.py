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

  ###############
  # Blank Paths #
  ###############
  path        = '/Users/horak/JDA-scripts/kahoku/output/'
  output_path = ''
  dup_path    = ''
  token_path  = ''

  ######################
  # Customimze Scraper #
  ######################
  def __init__(self, category='', *a, **kw):
    super(XmlSpider, self).__init__(*a, **kw)

    # Use category to setup scrape type (document, image, ...) 
    category     = category
    self.output_path  = self.path + category + '_output/'
    self.dup_path     = self.output_path + 'dup_list'
    self.token_path   = self.output_path + 'previous_resumption_token'

    # Create URL to scrape
    TEMPLATE_URL = 'http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set='
    url          = TEMPLATE_URL + category

    # Add resumption token if appropriate 
    tokenFileExists = os.path.exists(self.token_path)
    finalFileExists = glob.glob(self.output_path + 'final*')
    if tokenFileExists and not finalFileExists:
      token = open(self.token_path, 'r').read()
      url   = url + '&resumptionToken=' + token
      print '****** RESUMING WITH TOKEN: ' + token + ' ******' 

    self.start_urls[0] = url

  ################
  # Scraper Init #
  ################
  # This is a dummy start_urls variable which will be overwriten in __init__
  name            = 'xmlscrape'
  allowed_domains = ['kahoku-archive.shinrokuden.irides.tohoku.ac.jp']
  start_urls      = ['http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=P6EcZPbntF6_UERMqo0iRQ']

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
    items        = []
    items        = x.select('//record/metadata/RDF')
    jsons        = []
    id_list      = []
    nextFileLink = ''
    resumption_token = x.select('//resumptionToken/text()').extract()
    saveResumptionToken(resumption_token, self.token_path)

    ###############
    # Parse Items #
    ###############
    print '****** PARSING FILE... ******'
    for item in items:

      ######################
      # media_date_created #
      ######################
      media_date_created = item.select('Resource/created/text()').extract()
      media_date_created = handleNull(media_date_created)

      #################
      # response_date #
      #################
      response_date = item.select('Resource/responseDate/text()').extract()
      response_date = handleNull(response_date)

      ####################
      ##### creator ######
      ##### archive ######
      #### media_type ####
      #### layer_type ####
      ####################
      media_creator_username = 'Kahoku Shimpo Publishing Co.'
      archive                = 'Kahoku Shimpo Disasters Archive'
      media_type             = 'Image'
      layer_type             = 'Image' 

      ##################
      #### abstract ####
      ##### title ######
      ##################
      # Abstract tends to be more unique, though not always present. Title is often repetitive but more consistently filled.
      abstract = item.select('Resource/abstract/text()').extract()
      title    = item.select('Resource/title/text()').extract()
      title    = handleNull(title)
      abstract = handleNull(abstract)
      abstract = abstract.replace('\r\n', '')
      if not abstract:
        abstract = title

      ###################
      #### unique_id ##### 
      ###################
      # Used for de-duping
      unique_id = item.select('Resource/identifier/text()').extract()
      unique_id = str(unique_id[0])
      id_list.append(unique_id)

      ####################
      ####### URI ######## 
      ####################
      # Download image if it has not already been downloaded
      uri = item.select('Resource/screen/Image/@rdf:about').extract()
      downloaded = os.path.exists(self.output_path + unique_id + '.jpg')
      if uri and not downloaded:
        uri = uri[0]
        urllib.urlretrieve(uri, self.output_path + unique_id + '.jpg')
        uri = 'https://s3.amazonaws.com/JDA-Files/' + unique_id
      else:
        uri = handleNull(uri)

      ####################
      #### Thumbnail ##### 
      ####################
      thumbnail_url = item.select('Resource/thumbnail/Image/@rdf:about').extract()
      thumbnail_url = handleNull(thumbnail_url)

      ####################
      ###### source ###### 
      ####################
      source = item.select('Resource/@rdf:about').extract()
      source = handleNull(source)

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
        region         = handleNull(region)
        locality       = handleNull(locality)
        street_address = handleNull(street_address)
        locationTemp   = [street_address, locality, region]
        location       = ''

        # Handles comma location and attribute existence variability
        for item in locationTemp:
          if item:
            if location is '':
              location = location + item
            else:
              location = location + ', ' + item
        if location[location.__len__()-1] is ',':
          location = location[:-1]
      else:
        location = ''

      ##########################
      ######## Lat/Long ########
      ##########################
      # Uses Google Maps
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
      # file without a resumption token.
      if not resumption_token and os.path.exists(self.dup_path):
        dup_list = open(self.dup_path, 'r').read()
        if unique_id not in dup_list:
          jsons.append(json_entry)
      else:
        jsons.append(json_entry)


    ######################
    # Save Item URI List #
    ######################
    # Used for checking duplicates,
    # will overwrite itself.
    with open(self.dup_path, 'w+r') as f:
      print '****** (OVER)WRITING DEDUP LIST ******'
      f.truncate() 
      for item in id_list:
        print>>f, item
      f.close() 

    #########
    # Done? #
    #########
    if resumption_token == []:
      nextFileLink = ""
      open(self.output_path + 'final-' + getDateString() + '.json', 'wb').write(''.join(jsons).encode('UTF-8'))
      #removeEmptyFiles(self.output_path)
    else: # Or next job...
      nextFileLink = 'http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=' + resumption_token[0].encode('ascii')
      open(self.output_path + resumption_token[0].encode('ascii') + '.json', 'wb').write(''.join(jsons).encode('UTF-8'))
      yield Request(nextFileLink, callback = self.parse)
