# Instructions for the Kahoku Shimpo API
These instructions assume you are running python 2.7 on a unix OS.  

## Setup Scrapy
1. Install Scrapy 0.18.
To get this version do the following:
a. `git clone git://github.com/scrapy/scrapy.git`
b. `cd scrapy`
c. `git checkout 0.18`
d. `sudo python setup.py install`

The docs for this can be found [here](https://doc.scrapy.org/en/0.18/intro/tutorial.html) in case modifications need to be made.

2. Setup `PATH` variable
Make sure to change the `PATH` variables in `kahoku_spider.py`, `helpers.py`, and `combine.py` and to suit your environment.


## Running it Manually 
Here is a run through of typical use. Since some of these feeds have massive amounts of information (especially `image`), you'll probably want to run these manually the first time.

### Spider
The spider takes an argument `TYPE`: `image`, `document`, `movie`, or `other`. 
```
$ scrapy runspider kahoku_spider.py -a cat=[TYPE]
```
This call will populate the `[TYPE]_output` folder with scraped files, their title set to the date. This call will also generate `.resumptionToken`, `.dupList`, and `../.category` files which it uses to persists progress and such.

### Combine Files
Once the spider has finished processing files, over multiple sessions, the resulting files can be combined and formatted into a single file formatted: `final-[DATE].json` with this call.
```
$ python combine.py -l other
```
Again, it takes commmand line arguments that match its type.


## Running it with Cron Jobs
They are also setup to be run automatically as well. Such as with a cron job. Following the instructions should leave you with a single, consolidated JSON file in each respective output directory, along with JPEGs if applicable. 

1. Start the crontab
```
$ crontab -e
``` 

2. Setup the scrapers
```
0 * 1 1-12 * scrapy runspider [YOUR PATH]kahoku_spider.py -a cat=image
0 * 1 1-12 * scrapy runspider [YOUR PATH]kahoku_spider.py -a cat=document
0 * 1 1-12 * scrapy runspider [YOUR PATH]kahoku_spider.py -a cat=movie
0 * 1 1-12 * scrapy runspider [YOUR PATH]kahoku_spider.py -a cat=other
```

3. Setup the combiners
This would combine the files two days after they have been scraped, which should allow for enough time for the scraper to finish pulling down all the necessary new data. This is quite conservative and could be tweaked. I don't have any record of if  Kahoku adds new data on a schedule.
```
0 * 3 1-12 * [YOUR PATH] python combine.py -l image
0 * 3 1-12 * [YOUR PATH] python combine.py -l document
0 * 3 1-12 * [YOUR PATH] python combine.py -l movie
0 * 3 1-12 * [YOUR PATH] python combine.py -l other
```


## Info
### Item Types
 The Kahoku API can be configured to return 1 of 4 different data types, `IMAGE`, `DOCUMENT`, `MOVIE`, and `OTHER`, using the url structure below.
```
verb=ListRecords&metadataPrefix=sdn&set=IMAGE
```

### Resumption Tokens
A request will often yield too many documents for a single response. If more than one response is needed to provide all the items, a `resumptionToken` is provided as continuation url param like so:
```
http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=Iaeoy4eQF_Msh6Q_Sv_dnA
```
Importantly, these resumption tokens act as unique identifiers for requests previously made (and thus items procssed and downloaded). Each time a request is made, the resumptionToken is stored in the `\previous_resumption_token` file (untracked). When another request is made, the scrapper will pickup where it last left off. **Thus, to start scrapping from the beginning of the archive, erase `\previous_resumption_token`.** A JSON response to the request is stored in `[resumption token will be here].json`

When the scrapper reaches the last of the requests' items the response no longer includes a `resumptionToken` and will instead create a file called `final-[datetime].json`. Unfortunately, because the that resposne yields no unique identifier, files put in last will need to be de-duplicated.

### De-deduping
The final response page is not given a `resumptionToken`. I have assumed that that page's items can change, namely, that new items can be added. As such, the files in `final-[datetime].json` are deduped. 

Empty files are cleared automatically.

### Why Resumption Tokens?
The Kahoku API exposes `from`, `to`, and `until`-date filtering url params which would at first glance seem to make for a better option, but unfortuantely these are limited to only `date_modified` (as far as I could tell). 

### Images
Asahi files contain both a higher res and thumbnail image. Following the Asahi precedent, the higher res image is downloaded for manual upload to S3 and the `uri` is linked to that future location on S3 by its ID. As with Asahi, this could be automated easily.

### Google Maps API
- Google Maps is used to convert the `location` into `lat`/`long` coordinates. Right now, a free API key is being used that is rate limited.

### Misc. Quirks
- The same `title` attribute is often found for many items. I found the `abstract` attribute to be more unique, though often just an empty string. Thus, I default to that attribute and use `title` as a backup.
- Both the `attribution_uri` and `uri` are populated using the same source field: `Resource/screen/Image/@rdf:about`. This is a precedent I am following blindly, unsure why.
