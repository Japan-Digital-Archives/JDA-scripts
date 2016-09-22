# Subscribing and processing the Asahi RSS feed with cron jobs

### Open crontab
```
$ crontab -e
```

### Subscribe
Start a cron job that curls the Asahi RSS feed using `subscribeToFeed` every 5 minutes. This is the interval on which the RSS feed is refreshed. In my experience Asahi only publishes around 5-20 items per month so this is overkill and could be adjusted
```
*/5 * * * * /var/www/alex/asahi_rss_test/subscribeToFeed
```

### Process
Start another cron job that processes the resulting `*.xml` feed, converting it to individual `*.json` items. This can be run hourly to clear out duplicates. 
```
0 * * * * /var/www/alex/asahi_rss_test/jsonifyFeed.py
```

### Some Notes
- Both `jsonifyFeed.py` and `subscribeToFeed` expect the same `PATH` location, the included `feed/` directory. The `PATH` variable should be set in both files respectively. 
- `jsonifyFeed.py` will delete the `xml` files after processing them. 
- `jsonifyFeed.py` will download a `jpg` image into the `PATH` dir. The `thumbnail_uri` field already indicates their location on AWS's S3, but the images still need to uploaded. This could/should obviously be automated.
- `jsonifyFeed.py` uses an items asahi assigned id as a foreign key - so eliminating duplicates and file names.
