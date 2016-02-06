from scrapy.spider import BaseSpider
from scrapy.selector import XmlXPathSelector
from scrapy.http import Request

# this script uses the scrapy framework: http://scrapy.org/

# from xmlscrape.items import XmlscrapeItem

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

    for item in items:
      media_creator_username = 'Kahoku Simpo Publishing Co.'
      # print "**********creator*************: ", creator

      title = item.select('Resource/title/text()').extract() # seems to be the same for everything ... so i'm using abstract instead which seems to change
      abstract = item.select('Resource/abstract/text()').extract()
      # print "*****************abstract ", abstract[0]
      # print "**********titel*************: ", title[0]

      ####################
      ####### URI ######## 
      ####################
      uri = item.select('Resource/screen/Image/@rdf:about').extract()
      attribution_uri = uri
      if not uri:
        uri = ''
      else:
        uri[0] = ''
      # print "**********uri*************: ", uri[0]
      # print "**********attribution_uri*************: ", attribution_uri[0]

      ####################
      ####### Tags ####### 
      ####################
      tags = item.select('Resource/subject/Description/value/text()').extract()
      # print "**********tags*************: ", tags[0]
      tags_string = '"' + '", "'.join(tags) + '"'


      ####################
      #### Thumbnail ##### 
      ####################
      thumbnail_url = item.select('Resource/thumbnail/Image/@rdf:about').extract()
      # print "**********thumbnail*************: ", thumbnail

      ####################
      ##### Location ##### 
      ####################
      region = item.select('Resource/spatial/Description/region/text()').extract()
      locality = item.select('Resource/spatial/Description/locality/text()').extract()
      street_address = item.select('Resource/spatial/Description/street-address/text()').extract()

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

      print "**********location*************: ", location


      json_entry = '{"title": "' + abstract[0] + '", "uri": "' 
      # print "*********json_entry*******", json_entry
      # + uri[0] + '", "attribution_uri": "' 
      # + uri[0] + '", "media_creator_username": "' 
      # + media_creator_username + '", "thumbnail_url": "' 
      # + thumbnail_url[0] + "location": "' 
      # + location + '", "tags": [' 
      # + tags_string + '], "archive":"Yahoo! Japan", "media_type": "Image", "layer_type": "Image", "child_items_count":0, "published":1}, '

      jsons.append(json_entry)

    resumptionToken = x.select('//resumptionToken/text()').extract()
    if resumptionToken == []:
      nextFileLink = ''
      open('last.txt', 'wb').write(''.join(jsons).encode("UTF-8"))
    else:
      nextFileLink = "http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=" + resumptionToken[0].encode('ascii')
      # OLD nextFileLink = "http://search.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&resumptionToken=" + resumptionToken[0].encode('ascii')
      open(resumptionToken[0].encode('ascii') + '.txt', 'wb').write(''.join(jsons).encode("UTF-8"))
    yield Request(nextFileLink, callback = self.parse)
