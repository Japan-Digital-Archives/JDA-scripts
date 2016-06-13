from scrapy.spider import BaseSpider
from scrapy.selector import XmlXPathSelector
from scrapy.http import Request

# this script uses the scrapy framework: http://scrapy.org/

# i think this is scrapy 0.16
# you will need to change the filename to just xml_spider.py to run scrapy properly

from xmlscrape.items import XmlscrapeItem

class XmlSpider(BaseSpider):
	name = "xmlscrape"
	allowed_domains = ["search.shinrokuden.irides.tohoku.ac.jp"]
	start_urls = [
		"http://search.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&resumptionToken=VR7A7-an-L6FdpPca6VV1Q"
	]

	def parse(self, response):
		x = XmlXPathSelector(response)
		x.remove_namespaces()
		x.register_namespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
		items = []
		items = x.select('//record/metadata/RDF')

		jsons = []

		for item in items:
			creator = item.select('MetaResource/creator/Agent/name/text()').extract()
			title = item.select('Resource/title/text()').extract()
			uri = item.select('Resource/screen/Image/@rdf:about').extract()
			tags = item.select('Resource/subject/Description/value/text()').extract()
			thumbnail = item.select('Resource/thumbnail/Image/@rdf:about').extract()
			lat = item.select('Resource/spatial/Description/lat/text()').extract()
			long = item.select('Resource/spatial/Description/long/text()').extract()
			locality = item.select('Resource/spatial/Description/locality/text()').extract()
			
			tags_string = '"' + '", "'.join(tags) + '"'
			
			if not lat:
				newlat = 'null'
			else:
				newlat = lat[0]

			if not long:
				newlong = 'null'
			else:
				newlong = long[0]

			if not locality:
				newloc = ''
			else:
				newloc = locality[0]
			
			
			
			json_entry = '{"title": "' + title[0] + '", "uri": "' + uri[0] + '", "attribution_uri": "' + uri[0] + '", "media_creator_username": "' + creator[0] + '", "thumbnail_url": "' + thumbnail[0] + '", "media_geo_latitude": ' + newlat + ', "media_geo_longitude": ' + newlong + ', "location": "' + newloc + '", "tags": [' + tags_string + '], "archive":"Yahoo! Japan", "media_type": "Image", "layer_type": "Image", "child_items_count":0, "published":1}, '
			
			
			jsons.append(json_entry)
			

		resumptionToken = x.select('//resumptionToken/text()').extract()
		if resumptionToken == []:
			nextFileLink = ''
			open('last.txt', 'wb').write(''.join(jsons).encode("UTF-8"))
		else:
			nextFileLink = "http://search.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&resumptionToken=" + resumptionToken[0].encode('ascii')
			open(resumptionToken[0].encode('ascii') + '.txt', 'wb').write(''.join(jsons).encode("UTF-8"))
		yield Request(nextFileLink, callback = self.parse)
