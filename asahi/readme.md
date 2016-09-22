# Instructions on subscribing to Asahi RSS feed and converting feed results to json

1. Open crontab
```
$ crontab -e
```

2. Start a cron job that curls the Asahi RSS feed using `subscribeToFeed` every 5 minutes. This is the interval overwhich the RSS feed is refreshed. In my experience Asahi only publishes around 5-20 items per month so this is overkill and could be adjusted.
```
*/5 * * * * #!/bin/bash /var/www/alex/asahi_rss_test/subscribeToFeed
```

3. Start another cron job that runs processes the resulting `*.xml` converting them to individual `*.json`. This can be run once a day to clear out duplicates.
```
*/5 * * * * /var/www/alex/asahi_rss_test/jsonifyFeed.py
