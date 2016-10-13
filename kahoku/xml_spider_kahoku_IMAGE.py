#!/usr/bin/env python

###########
# Imports #
###########
from scrapy.spider import BaseSpider
from scrapy.selector import XmlXPathSelector
from scrapy.http import Request
import urllib, json, contextlib, os, glob

class XmlSpider(BaseSpider):


  #################
  # Setup Scraper #
  #################
  name            = "xmlscrape"
  allowed_domains = ["kahoku-archive.shinrokuden.irides.tohoku.ac.jp"]
  start_url       = "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=P6EcZPbntF6_UERMqo0iRQ"
  blank_start_url = "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE"
  start_urls      = []

  # Will return URL with resumption token if possible
  def getResumptionUrl(start_url, blank_start_url, start_urls):
    tokenFileExists = os.path.exists('previous_resumption_token')
    finalFileExists  = glob.glob('final*')

    if tokenFileExists and not finalFileExists:
      token = open('previous_resumption_token', 'r').read()
      start_url = blank_start_url + "&resumptionToken=" + token
      print '****** RESUMING WITH TOKEN: ' + token + ' ******'

    start_urls.append(start_url)

  getResumptionUrl(start_url, blank_start_url, start_urls) 


  ##############
  # Parse Feed #
  ##############
  def parse(self, response):

    ###########
    # Helpers #
    ###########
    def getSavedResumptionToken():
      token = open('previous_resumption_token', 'r').read()
      return token

    def handleNull(field):
      if not field:
        field = ''
      else:
        field = field[0]
      return field

    def saveResumptionToken(token):
      if token:
        with open('previous_resumption_token', 'w+r') as f:
          print '****** (OVER)WRITING RESUMPTION TOKEN: ' + token[0] + ' ******'
          f.truncate()
          f.write(token[0])
          f.close() 
      else:
        print '****** NO RESUMPTION TOKEN: FINAL RESPONSE PAGE ******'

    #########
    # Setup #
    #########
    x = XmlXPathSelector(response)
    x.remove_namespaces()
    x.register_namespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    items        = []
    items        = x.select('//record/metadata/RDF')
    jsons        = []
    idList       = []
    nextFileLink = ''
    output_path  = '/Users/horak/Dropbox/JDA/JDA-scripts/kahoku/feed/'
    resumption_token = x.select('//resumptionToken/text()').extract()
    saveResumptionToken(resumption_token)

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
      archive                = "Kahoku Shimpo Disasters Archive"
      media_type             = "Image"
      layer_type             = "Image" 

      ##################
      #### abstract ####
      ##### title ######
      ##################
      # Abstract tends to be more unique, though not always present. Title is often repetitive but more consistently filled.
      abstract = item.select('Resource/abstract/text()').extract()
      title    = item.select('Resource/title/text()').extract()
      title    = handleNull(title)
      abstract = handleNull(abstract)
      abstract = abstract.replace("\r\n", "")
      if not abstract:
        abstract = title

      ####################
      ####### URI ######## 
      ####################
      uri = item.select('Resource/screen/Image/@rdf:about').extract()
      uri = handleNull(uri)

      ###################
      #### uniqueId ##### 
      ###################
      # Used for de-duping
      uniqueId = item.select('Resource/identifier/text()').extract()
      idList.append(uniqueId)

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
      #### Thumbnail ##### 
      ####################
      thumbnail_url = item.select('Resource/thumbnail/Image/@rdf:about').extract()
      thumbnail_url = handleNull(thumbnail_url)

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
              location = location + ", " + item
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

      # print json_entry
      jsons.append(json_entry)

    #########
    # Done? #
    #########
    if resumption_token == []:
      nextFileLink = ""
      newJsons = []
      previous_resumption_token = getSavedResumptionToken()
      # if final exists:
        # for item in jsons
        # if item.uri i
      # De-dedup (jsons)
      # if list exists - compare(jsons)
      # then overwrite the list
      open(output_path + 'final-' + previous_resumption_token + '.json', 'wb').write(''.join(jsons).encode("UTF-8"))
    else: # Or next job...
      nextFileLink = "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=" + resumption_token[0].encode('ascii')
      open(output_path + resumption_token[0].encode('ascii') + '.json', 'wb').write(''.join(jsons).encode("UTF-8"))
      yield Request(nextFileLink, callback = self.parse)
