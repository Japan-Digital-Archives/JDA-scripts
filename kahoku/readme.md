# Instructions for the Kahoku Shimpo API

## Setup
To get started install...

## Item Types
 The Kahoku API can be configured to return 1 of 4 different data types, `IMAGE`, `DOCUMENT`, `MOVIE`, and `OTHER`, using the url structure below.
```
verb=ListRecords&metadataPrefix=sdn&set=IMAGE
```

## Resumption Tokens
A request will often yield too many documents for a single response. If more than one response is needed to provide all the items, a `resumptionToken` is provided as continuation url param like so:
```
http://kahoku-archive.shinrokuden.irides.tohoku.ac.jp/webapi/oaipmh?verb=ListRecords&metadataPrefix=sdn&set=IMAGE&resumptionToken=Iaeoy4eQF_Msh6Q_Sv_dnA
```
Importantly, these resumption tokens act as unique identifiers for requests previously made (and thus items procssed and downloaded). Each time a request is made, the resumptionToken is stored in the `\previous_resumption_token` file (untracked). When another request is made, the scrapper will pickup where it last left off. **Thus, to start scrapping from the beginning of the archive, erase `\previous_resumption_token`.** A JSON response to the request is stored in `[resumption token will be here].json`

When the scrapper reaches the last of the requests' items the response no longer includes a `resumptionToken` and will instead create a file called `final-[datetime].json`. Unfortunately, because the that resposne yields no unique identifier, files put in last will need to be de-duplicated.

## De-deduping
The final response page is not given a `resumptionToken`. I have assumed that that page's items can change, namely, that new items can be added. As such, the files in `final-[datetime].json` are deduped. 

Empty files are cleared automatically.

### Why Resumption Tokens?
The Kahoku API exposes `from`, `to`, and `until`-date filtering url params which would at first glance seem to make for a better option, but unfortuantely these are limited to only `date_modified` (as far as I could tell). 

## Images
Asahi files contain both a higher res and thumbnail image. Following the Asahi precedent, the higher res image is downloaded for manual upload to S3 and the `uri` is linked to that future location on S3 by its ID. As with Asahi, this could be automated easily.

## Google Maps API
- Google Maps is used to convert the `location` into `lat`/`long` coordinates. Right now, a free API key is being used that is rate limited. 

## Cron
- The cron is only run once a month considering how slowly new items are added.
```

``` 

## Misc. Quirks
- The same `title` attribute is often found for many items. I found the `abstract` attribute to be more unique, though often just an empty string. Thus, I default to that attribute and use `title` as a backup.
- Both the `attribution_uri` and `uri` are populated using the same source field: `Resource/screen/Image/@rdf:about`. This is a precedent I am following blindly, unsure why.
