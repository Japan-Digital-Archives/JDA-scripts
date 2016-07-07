from scrapy.spider import BaseSpider
from scrapy.selector import Selector
from scrapy.http import Request

# this script uses the scrapy framework: http://scrapy.org/

# i think this is scrapy 0.16 or close to that version
# you will need to rename this file to just xml_spider.py for this to work with scrapy

from xmlscrape.items import XmlscrapeItem

class XmlSpider(BaseSpider):
        name = "xmlscrape"
        allowed_domains = ["fukushima.archive-disasters.jp"]
        start_urls = [
                "http://fukushima.archive-disasters.jp/infolib/oai_repository/repository?verb=ListRecords&metadataPrefix=ndlkn"
        ]

        def parse(self, response):
                x = Selector(response)
                x.remove_namespaces()
                items = []
                items = x.xpath('//record/metadata/RDF')

                jsons = []

                for item in items:
				
					media_type = ""
					layer_type = ""

					# get ending of "alternative" title, which gives file extension
					file_ext = ""
					if not item.xpath('Resource/alternative/Description/value/text()').extract() == []:
						file_ext = item.xpath('Resource/alternative/Description/value/text()').extract()[0].split('.')[-1]
							
						# we don't want these	
						if file_ext == "cvs" or file_ext == "CVS" or file_ext == "xls" or file_ext == "XLS" or file_ext == "txt" or file_ext == "TXT":
							continue;
						if file_ext == "pdf" or file_ext == "PDF" or file_ext == "doc" or file_ext == "DOC" or file_ext == "docx" or file_ext == "DOCX" or file_ext == "rtf" or file_ext == "RTF":
							media_type = "Document"
							layer_type = file_ext.upper()
						if file_ext == "jpg" or file_ext == "JPG" or file_ext == "jpeg" or file_ext == "JPEG" or file_ext == "png" or file_ext == "PNG":
							media_type = "Image"
							layer_type = "Image"
						if file_ext == "mp3" or file_ext == "MP3" or file_ext == "wav" or file_ext == "WAV" or file_ext == "m4a" or file_ext == "M4A" or file_ext == "wma" or file_ext == "WMA":
							media_type = "Audio"
							layer_type = "Audio"
						if file_ext == "mp4" or file_ext == "MP4" or file_ext == "mpeg" or file_ext == "MPEG" or file_ext == "wmv" or file_ext == "WMV" or file_ext=="AVI" or file_ext == "avi":
							media_type = "Video"
							layer_type = "Video"
						

					# NDL link 
					format = item.xpath('Resource/materialType/@resource').extract()[0]
					if media_type == "" and layer_type == "":
						if format == "http://purl.org/dc/dcmitype/StillImage" or format == "http://ndl.go.jp/ndltype/Photograph":
							media_type = "Image"
							layer_type = "Image"
						if format == "http://purl.org/dc/dcmitype/MovingImage":
							media_type = "Video"
							layer_type = "Video"
						if format == "http://purl.org/dc/dcmitype/Sound":
							media_type = "Audio"
							layer_type = "Audio"
							
					#Still Nothing
					if media_type == "" and layer_type == "":
						if not item.xpath('Resource/accessURL/@resource').extract() == []:
							file_ext = item.xpath('Resource/accessURL/@resource').extract()[0].split('.')[-1]
							# we don't want these	
							if file_ext == "cvs" or file_ext == "CVS" or file_ext == "xls" or file_ext == "XLS" or file_ext == "txt" or file_ext == "TXT":
								continue;
							if file_ext == "pdf" or file_ext == "PDF" or file_ext == "doc" or file_ext == "DOC" or file_ext == "docx" or file_ext == "DOCX" or file_ext == "rtf" or file_ext == "RTF":
								media_type = "Document"
								layer_type = file_ext.upper()
							if file_ext == "jpg" or file_ext == "JPG" or file_ext == "jpeg" or file_ext == "JPEG" or file_ext == "png" or file_ext == "PNG":
								media_type = "Image"
								layer_type = "Image"
							if file_ext == "mp3" or file_ext == "MP3" or file_ext == "wav" or file_ext == "WAV" or file_ext == "m4a" or file_ext == "M4A" or file_ext == "wma" or file_ext == "WMA":
								media_type = "Audio"
								layer_type = "Audio"
							if file_ext == "mp4" or file_ext == "MP4" or file_ext == "mpeg" or file_ext == "MPEG" or file_ext == "wmv" or file_ext == "WMV" or file_ext=="AVI" or file_ext == "avi":
								media_type = "Video"
								layer_type = "Video"
							
					creator = item.xpath('Resource/publisher/Agent/name/text()').extract()
					title = item.xpath('Resource/title/Description/value/text()').extract()
					uri = item.xpath('Resource/@about').extract()
					attribution_uri = item.xpath('MetaResource/@about').extract()
					date_created = item.xpath('MetaResource/created/text()').extract()
					access_url = item.xpath('Resource/accessURL/@resource').extract()
					
					if media_type == "Image" or media_type == "Audio" or media_type == "Video" or media_type == "Document":
						if not access_url == []:
							uri = access_url
					
						
						
					if not date_created:
						media_date_created = "0000-00-00 00:00:00"
					else:
						date = date_created[0].split('T')[0]
						time = date_created[0].split('T')[1].split('+')[0]
						media_date_created = date + ' ' + time
			
					
					
					tags = item.xpath('Resource/subject/text()').extract()
					tags_string = ""
					new_tags = []
					for tag in tags:
						if tag == '\n':
							continue
						else:
							if len(tag.split(u'\u3001')) == 1:
								new_tags += tag.split(',')
							else:
								new_tags += tag.split(u'\u3001')
							
					
					tags_string = '"' + '", "'.join(new_tags) + '"'
					
					thumbnail = item.xpath('Resource/thumbnail/@resource').extract()
					locality = item.xpath('Resource/spatial/Description/label/text()').extract()

					if not locality:
						newloc = ''
					else:
						newloc = locality[0]

					if not thumbnail:
						newthumb = ''
					else:
						if thumbnail[0] == "http://fukushima.archive-disasters.jp/images/file_normal_icon.jpg":
							newthumb = ''
						else:
							newthumb = thumbnail[0]
						
					if not title:
						title = ''
					else:
						title = title[0]
					
					if not uri:
						uri = ''
					else:
						uri = uri[0]
						
					if not attribution_uri:
						attribution_uri = ''
					else:
						attribution_uri = attribution_uri[0]
					
					if not creator:
						creator = ""
					else:
						creator = creator[0]
					
					
					if newthumb == '':
						thumb = ''
					else:
						thumb = '", "thumbnail_url": "' + newthumb

					json_entry = '{"title": "' + title + '", "description": "", "uri": "' + uri + '", "attribution_uri": "' + attribution_uri + '", "media_creator_username": "' + creator + thumb + '", "location": "' + newloc + '", "media_date_created": "' + media_date_created + '", "tags": [' + tags_string + '], "archive":"Fukushima Disaster Archives", "media_type": "' + media_type + '", "layer_type": "' + layer_type + '", "child_items_count":0, "published":1}, '


					jsons.append(json_entry)
                        

                resumptionToken = x.xpath('//resumptionToken/text()').extract()
                if resumptionToken == []:
					print "FINISHED"
					nextFileLink = ''
					open('last.txt', 'wb').write(''.join(jsons).encode("UTF-8"))
                else:
					nextFileLink = "http://fukushima.archive-disasters.jp/infolib/oai_repository/repository?verb=ListRecords&resumptionToken=" + resumptionToken[0].encode('ascii')
					filename = resumptionToken[0].replace('!', '').replace(':','')
					open(filename.encode('ascii') + '.txt', 'wb').write(''.join(jsons).encode("UTF-8"))
                yield Request(nextFileLink, callback = self.parse)
