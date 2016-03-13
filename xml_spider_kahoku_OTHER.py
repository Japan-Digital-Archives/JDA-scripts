#################################################
# This script is for scraping the OTHER contents of the 
# Kahoku Shimpo Disaster Archive. These are all images
# though so I'm still keeping the "image" lalbe. Run it with
# '$ scrapy runspider xml_spider_kahoku_OTHER.py'
#################################################


from scrapy.spider import BaseSpider
from scrapy.selector import XmlXPathSelector
from scrapy.http import Request

class XmlSpider(BaseSpider):
  name = "xmlscrape"
  allowed_domains = ["kahoku-archive.shinrokuden.irides.tohoku.ac.jp"]
  start_urls = [ 
  "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE" 
  ]

  def handleNull(self, field):
    if not field:
      field = ''
    else:
      field = field[0]
    return field

  def parse(self, response):
    x = XmlXPathSelector(response)
    x.remove_namespaces()
    x.register_namespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    items = []
    items = x.select('//record/metadata/RDF')

    jsons = []
    num = 0

    for item in items:
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
      # media_date_created
      ####################
      media_date_created = item.select('Resource/created/text()').extract()
      media_date_created = self.handleNull(media_date_created)
      # print media_date_created

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
      ####################
      uri = item.select('Resource/screen/Image/@rdf:about').extract()
      uri = self.handleNull(uri)
      # print "**********uri*************: ", uri

      ####################
      ##### Att URI ###### 
      ####################
      attribution_uri = item.select('Resource/@rdf:about').extract()
      attribution_uri = self.handleNull(attribution_uri)
      # print "**********attribution_uri*************: ", attribution_uri

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
      # maps API               #
      # made using Alex H's    #
      # account for expediency #
      ##########################
      if location != '':
        KEY = '&key=AIzaSyCGF2BwNPNckrbx6L2tQRATBcjKv0C3xCo'
        GOOGLE_URI = 'https://maps.googleapis.com/maps/api/geocode/json?address=' 
        location_encoded = location.encode('utf8')
        location_url_ready = urllib.quote_plus(location_encoded, safe='')
        request_uri = GOOGLE_URI + location_url_ready + KEY
        with contextlib.closing(urllib.urlopen(request_uri)) as response:
          data = json.load(response)
          if data != '':
            lat = json.dumps(data['results'][0]['geometry']['location']['lat'])
            lng = json.dumps(data['results'][0]['geometry']['location']['lng'])
          else:
            lat = 'null' 
            ln = 'null'

      json_entry = ( '{"title": "' 
        + abstract + '", "uri": "' 
        + uri + '", "attribution_uri": "' 
        + attribution_uri + '", "media_date_created": "' 
        + media_date_created + '", "media_creator_username": "' 
        + media_creator_username + '", "thumbnail_url": "' 
        + thumbnail_url + '", "lat": "' 
        + media_geo_latitude + '", "lng: "' 
        + media_geo_longitude + '", "location": "' 
        + location + '", "tags": [' 
        + tags_string + '], "archive": "' 
        + archive + '",  "media_type": "'
        + media_type + '", "layer_type": "'
        + layer_type + '", "child_items_count": 0, "published": 1}, '
      )

      # print json_entry
      jsons.append(json_entry)

    resumptionToken = x.select('//resumptionToken/text()').extract()
    nextFileLink = ''
    if resumptionToken == []:
      open('last.json', 'wb').write(''.join(jsons).encode("UTF-8"))
    else:
      nextFileLink = "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=" + resumptionToken[0].encode('ascii')
      open(resumptionToken[0].encode('ascii') + '.json', 'wb').write(''.join(jsons).encode("UTF-8"))
    yield Request(nextFileLink, callback = self.parse)
