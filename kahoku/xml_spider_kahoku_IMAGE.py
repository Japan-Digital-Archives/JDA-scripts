#################################################
# This script is for scraping the IMAGE contents of the 
# Kahoku Shimpo Disaster Archive. Run it with
# '$ scrapy runspider xml_spider_kahoku_IMAGE.py'
#################################################

from scrapy.spider import BaseSpider
from scrapy.selector import XmlXPathSelector
from scrapy.http import Request
import urllib, json, contextlib, os

class XmlSpider(BaseSpider):

  #################
  # setup scraper #
  #################
  name = "xmlscrape"
  allowed_domains = ["kahoku-archive.shinrokuden.irides.tohoku.ac.jp"]

  #################
  # set scrap url #
  #################
  # select which type of record to grab
  # start_url = "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE"
  start_url = "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=Iaeoy4eQF_Msh6Q_Sv_dnA"
  blank_start_url = "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE"
  start_urls = []

  ######################
  # continue scraping? #
  ######################
  # set key from file
  tokenFileExists = os.path.exists('lastToken')
  lastFileExists = os.path.exists('last.json')
  if tokenFileExists and not lastFileExists:
    print 'pre-existing'
    myFile = open('lastToken', 'r')
    priorResumptionToken = myFile.read()
    start_url = blank_start_url + "&resumptionToken=" + priorResumptionToken
    print priorResumptionToken, 'prior resumption token'
  else:
    print 'not pre-existing'
  start_urls.append(start_url)

  ###########
  # helpers #
  ###########
  def handleNull(self, field):
    if not field:
      field = ''
    else:
      field = field[0]
    return field

  #########
  # parse #
  #########
  def parse(self, response):
    print 'begin parse'
    x = XmlXPathSelector(response)
    x.remove_namespaces()
    x.register_namespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    items = []
    items = x.select('//record/metadata/RDF')

    jsons = []
    nextFileLink = ''
    uriList = []
    OUTPUT_PATH = '/Users/horak/Dropbox/JDA/JDA-scripts/kahoku/feed/'

    print 'begin parse 2'

    ####################################
    # record resumption token as prior #
    ####################################
    resumptionToken = x.select('//resumptionToken/text()').extract()

    # replace lastToken, whether it exists or not, with new token
    if resumptionToken:
      with open('lastToken', 'w+r') as f:
        print 'writing or replaceing token'
        f.truncate()
        f.write(resumptionToken[0])
        f.close() 

    ###################
    # parse xml items #
    ###################
    for item in items:
      print 'item'
      ######################
      # media_date_created #
      ######################
      media_date_created = item.select('Resource/created/text()').extract()
      media_date_created = self.handleNull(media_date_created)
      #print media_date_created

      #################
      # response_date #
      #################
      response_date = item.select('Resource/responseDate/text()').extract()
      response_date = self.handleNull(response_date)

      ####################
      ##### creator ######
      ##### archive ######
      #### media_type ####
      #### layer_type ####
      ####################
      media_creator_username = 'Kahoku Shimpo Publishing Co.'
      archive = "Kahoku Shimpo Disasters Archive"
      media_type = "Image"
      layer_type = "Image" 

      ####################
      ###### abstract ####
      ####################
      # title = item.select('Resource/title/text()').extract() # seems to be the same for everything ... so i'm using abstract instead which seems to change
      abstract = item.select('Resource/abstract/text()').extract()
      abstract = self.handleNull(abstract)
      abstract = abstract.replace("\r\n", "")
      # print "*****************abstract ", abstract

      ####################
      ####### URI ######## 
      # is image and is  #
      # set equal to att #
      # uri.. convention #
      ####################
      uri = item.select('Resource/screen/Image/@rdf:about').extract()
      uri = self.handleNull(uri)
      uriList.append(uri)
      # print "**********uri*************: ", uri

      ####################
      ###### source ###### 
      ####################
      source = item.select('Resource/@rdf:about').extract()
      source = self.handleNull(source)
      # print "**********source*************: ", source

      ####################
      ####### Tags ####### 
      ####################
      tags = item.select('Resource/subject/Description/value/text()').extract()
      if not tags:
        tags_string = '[]'
      else:
        tags_string = '"' + '", "'.join(tags) + '"'
      # print "********tags_string**********: ", tags_string

      ####################
      #### Thumbnail ##### 
      ####################
      thumbnail_url = item.select('Resource/thumbnail/Image/@rdf:about').extract()
      thumbnail_url = self.handleNull(thumbnail_url)
      # print "**********thumbnail*************: ", thumbnail_url

      ####################
      ##### Location ##### 
      ####################
      region = item.select('Resource/spatial/Description/region/text()').extract()
      locality = item.select('Resource/spatial/Description/locality/text()').extract()
      street_address = item.select('Resource/spatial/Description/street-address/text()').extract()
      if region or locality or street_address:
        region = self.handleNull(region)
        locality = self.handleNull(locality)
        street_address = self.handleNull(street_address)
        locationTemp = [street_address, locality, region]
        location = ''

        # This handles comma location and existence issues
        for item in locationTemp:
          if item:
            if location is '':
              location = location + item
            else:
              location = location + ", " + item
        if location[location.__len__()-1] is ',':
          location = location[:-1]
        # print "**********location*************: ", location
      else:
        location = ''
        # print "**********location*************: ", location

      ##########################
      ######## Lat/Long ########
      # GEOCODE using location # 
      # information and google # 
      # maps API.              #
      # Made using Alex H's    #
      # account for expediency.#
      ##########################
      lat = '' 
      lng = ''
      if location != '':
        KEY = '&key=AIzaSyCGF2BwNPNckrbx6L2tQRATBcjKv0C3xCo'
        GOOGLE_URI = 'https://maps.googleapis.com/maps/api/geocode/json?address=' 
        location_encoded = location.encode('utf8')
        location_url_ready = urllib.quote_plus(location_encoded, safe='')
        request_uri = GOOGLE_URI + location_url_ready + KEY
        with contextlib.closing(urllib.urlopen(request_uri)) as response:
          data = json.load(response)
          if json.dumps(data['results']) != '[]':
            lat = json.dumps(data['results'][0]['geometry']['location']['lat'])
            lng = json.dumps(data['results'][0]['geometry']['location']['lng'])
          else:
            lat = 'null' 
            lng = 'null'

      json_entry = ( '{"title": "' 
        + abstract + '", "uri": "' 
        + uri + '", "attribution_uri": "' 
        + uri + '", "media_date_created": "' 
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

    ##########################
    # cotinue with next file #
    ##########################
    if resumptionToken == []:
      # REMOVE lastTOken file
      print 'last'
      nextFileLink = ""
      newJsons = []
      open('last.json', 'wb').write(''.join(jsons).encode("UTF-8"))
    else: 
      print 'onto next file'
      nextFileLink = "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=" + resumptionToken[0].encode('ascii')
      open(OUTPUT_PATH + resumptionToken[0].encode('ascii') + '.json', 'wb').write(''.join(jsons).encode("UTF-8"))
      yield Request(nextFileLink, callback = self.parse)
