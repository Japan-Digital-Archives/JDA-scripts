# Instructions for the Kahoku Shimpo API
*These instructions assume you are running python 2.7 on a unix os.*

## Setup
1. Install Scrapy 0.18. To get this version do the following:
 1. `git clone git://github.com/scrapy/scrapy.git`
 2. `cd scrapy`
 3. `git checkout 0.18`
 4. `sudo python setup.py install`
 
 *The docs for this can be found [here](https://doc.scrapy.org/en/0.18/intro/tutorial.html) in case modifications need to be made.*
2. Setup `PATH` variable
Make sure to change the `PATH` variables in `kahoku_spider.py`, `helpers.py`, and `combine.py` and to suit your environment.

3. Google Maps API
Google Maps is used to populate the `lat`/`long` coordinates. Right now, a free API key is being used that is rate limited. *YOU WILL NEED TO UPLOAD A NEW API KEY THAT IS NOT RATE LIMITED IN ORDER TO DOWNLOAD FILES CONTINUOUSLY.* IF you do not do this, `lat`/`long` will silently be assigned `null`.


## Manual Run 
Here is a run through of typical use. Since some of these feeds contain lots of data (especially `image`), you'll probably want to run these manually the first time to watch for exceptions.

### Spider
The spider takes an argument `TYPE`: `image`, `document`, `movie`, or `other`. 
```
$ scrapy runspider kahoku_spider.py -a cat=[TYPE]
```
This call will populate the `output/[TYPE]_output` folder with scraped files, their title set to the date. This call will also generate `.resumptionToken`, `.dupList`, and `../.category` files which it uses to persists progress and such. **To reset things while debugging you will need to delete all three of these files.**

### Combine Files
Once the spider has finished processing files, over multiple sessions, the resulting files can be combined and formatted into a single file `final-[DATE].json`.
```bash
$ python combine.py -l other
```
Again, it takes commmand line arguments that match its type.


## Cron Jobs
Following these instructions should leave you with a single, consolidated JSON file in each respective output directory, along with any downloaded images if applicable. 

Start the crontab with:
```
$ crontab -e
``` 

Setup the scrapers with:
```
0 * 1 1-12 * scrapy runspider [YOUR PATH]kahoku_spider.py -a cat=image
0 * 1 1-12 * scrapy runspider [YOUR PATH]kahoku_spider.py -a cat=document
0 * 1 1-12 * scrapy runspider [YOUR PATH]kahoku_spider.py -a cat=movie
0 * 1 1-12 * scrapy runspider [YOUR PATH]kahoku_spider.py -a cat=other
```

Setup the combiners with:
```
0 * 3 1-12 * [YOUR PATH] python combine.py -l image
0 * 3 1-12 * [YOUR PATH] python combine.py -l document
0 * 3 1-12 * [YOUR PATH] python combine.py -l movie
0 * 3 1-12 * [YOUR PATH] python combine.py -l other
```

This setup would consolidate the files two days after they have been scraped, which should allow enough time for the scraper to finish pulling down all the necessary new data. This is quite conservative and could be tweaked. I don't have any record of whether Kahoku adds new data on a schedule.


## Background Information

### Item Types
The Kahoku API can be configured to return 1 of 4 different data types, `IMAGE`, `DOCUMENT`, `MOVIE`, and `OTHER`, using the url structure below.
```
verb=ListRecords&metadataPrefix=sdn&set=IMAGE
```

### Resumption Tokens
A request will often yield too many documents for a single response. If more than one response is needed to provide all the items, a `resumptionToken` is provided as continuation url param like so:
```
http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=5xum7v4o7-1B1JcK6WfGFg
```
Importantly, these resumption tokens act as unique identifiers for requests previously made (and thus items processed and downloaded). Each time a request is made, the resumptionToken is stored in the `output/[TYPE]_output/.previous_resumption_token` file (untracked). When another request is made, the scrapper will pick up where it last left off. **Thus, to start scrapping from the beginning of the archive, erase `output/[TYPE]_output/.previous_resumption_token`.**

When the scrapper reaches the last of the requests' items the response no longer includes a `resumptionToken` and will instead create a file called `final-[datetime].json`. Unfortunately, because the that response yields no unique identifier, files scraped from the last call need to be de-duplicated.

### De-duplication
The final response page is not given a `resumptionToken`. I have assumed that only this page's items can change, namely, that new items can be added over time. As such, the files in `final-[datetime].json` need to be de-duped. The final page's item ID's are stored in `.dup_list`. 

If a scrape yields empty files, they are deleted automatically. 

### Why Use Resumption Tokens as placeholders?
The Kahoku API (included in repo) exposes `from`, `to`, and `until`-date filtering url params which would at first glance seem to make for a better route, but unfortuantely these are limited to only `date_modified`, as opposed to date_uploaded, which the resumption token provides incidentally. 

### Images
Items contain both a higher resolution image and thumbnail image. Following Asahi precedent, the higher resolution image is downloaded for manual upload to S3 and the `uri` is linked to that future location on S3 by its ID. As with Asahi, this could be automated easily.

### Misc. Quirks
- The same `title` attribute is often found for many items. I found the `abstract` attribute to be more unique, though it is often just an empty string. Thus, I default to that attribute and use `title` as a backup.

- Both the `attribution_uri` and `uri` are populated using the same source field: `Resource/screen/Image/@rdf:about`, in instances where no other uri existed. This is another Asahi precedent I am following blindly.

- Both `layer_type` and `media_type` follow a similar precedent and should probably be overwritten. 
