from scrapy.spider import BaseSpider
from scrapy.selector import XmlXPathSelector
from scrapy.http import Request

class XmlSpider(BaseSpider):
  name = "xmlscrape"
  allowed_domains = ["kahoku-archive.shinrokuden.irides.tohoku.ac.jp"]
    # "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE"
  start_urls = [
    "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=5WR5-HYweU6yQfHFWgiqTw"
  ]

  def handleNull(self, field):
    if not field:
      field = ''
    else:
      field = field[0]
    return field

  def parse(self, response):
    x = XmlXPathSelector(response)
    # y = XmlXPathSelector(response)
    # y.remove_namespaces()
    x.remove_namespaces()
    x.register_namespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    items = []
    items = x.select('//record/metadata/RDF')
    # itemsY = y.select('//record/header/@status')
    # print '**************** ', itemsY

    jsons = []
    num = 0

    # maybe the problem is just the number of item
    for item in items:
      ####################
      ##### creator ######
      ##### archive ######
      #### media_type ####
      #### layer_type ####
      ####################
      media_creator_username = 'Kahoku Simpo Publishing Co.'
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
      ####### URI ######## 
      ####################
      attribution_uri = item.select('Resource/@rdf:about').extract()
      attribution_uri = self.handleNull(attribution_uri)
      # print "**********attribution_uri*************: ", attribution_uri

      ####################
      ####### Tags ####### 
      ####################
      tags = item.select('Resource/subject/Description/value/text()').extract()
      tags = self.handleNull(tags)
      # print "**********tags*************: ", tags
      tags_string = '"' + '", "'.join(tags) + '"'

      ####################
      #### Thumbnail ##### 
      ####################
      thumbnail_url = item.select('Resource/thumbnail/Image/@rdf:about').extract()
      thumbnail_url = self.handleNull(thumbnail_url)
      print "**********thumbnail*************: ", thumbnail_url
      print '^ thumbnail before death'

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

      json_entry = ( '{"title": "' 
        + abstract + '", "uri": "' 
        + uri + '", "attribution_uri": "' 
        + attribution_uri + '", "media_creator_username": "' 
        + media_creator_username + '", "thumbnail_url": "' 
        + thumbnail_url + '", "location": "' 
        + location + '", "tags": [' 
        + tags_string + '], "archive": "' 
        + archive + '",  "media_type": "'
        + media_type + '", "layer_type": "'
        + layer_type + '", "child_items_count": 0, "published": 1}, '
      )

      # print json_entry
      jsons.append(json_entry)

    resumptionToken = x.select('//resumptionToken/text()').extract()
    if resumptionToken == []:
      nextFileLink = ''
      open('last.txt', 'wb').write(''.join(jsons).encode("UTF-8"))
    else:
      nextFileLink = "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=" + resumptionToken[0].encode('ascii')
      open(resumptionToken[0].encode('ascii') + '.txt', 'wb').write(''.join(jsons).encode("UTF-8"))
    yield Request(nextFileLink, callback = self.parse)
