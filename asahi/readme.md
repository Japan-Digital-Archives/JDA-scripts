# Subscribing and processing the Asahi RSS feed

A. Open crontab with
```
$ crontab -e
```

B. Start a cron job that curls the Asahi RSS feed using `subscribeToFeed` every 5 minutes. This is the interval on which the RSS feed is refreshed. In my experience Asahi only publishes around 5-20 items per month so this is overkill and could be adjusted
```
*/5 * * * * #!/bin/bash /var/www/alex/asahi_rss_test/subscribeToFeed
```

C. Start another cron job that processes the resulting `*.xml` feed, converting it to individual `*.json` items. This can be run hourly to clear out duplicates. 
```
0 * * * * /var/www/alex/asahi_rss_test/jsonifyFeed.py
```
