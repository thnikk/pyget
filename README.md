# pyget
A simple script for adding torrents from rss feeds. Since there's an item limit to RSS feeds, the script creates a feed for each show. It's slower, but it mitigates the limitation by giving more relevant results. This can help if you're trying to start downloading something a few weeks into a season.

## Configuration
Pyget uses a json file for easy and flexible configuration. Running the script for the first time will create ~/.config/pyget.json.

```
{
    "client": torrent client (deluge or transmission),
    "feeds": [
        {
            "url": feed url,
            "directory": path to create show/season folder in,
            "days": Max age of items in feed to pull from (0 to disable),
            "shows": {
                "Show name": Season (creates a subdirectory within the show folder),
            }
        },
        {
            Same as above for another feed url
        }
    ]
}

```

## Dependencies
To install dependencies, run:
`pip install -r requirements.txt`

## Daemonizing

Edit the default config and run the script manually before you daemonize it. Both methods below assume that pyget.py is in ~/.local/bin.  

### Using a cronjob
This is easier way but could make debugging harder. All you need to do is run `crontab -e` and add the line:

`*/10 * * * * $HOME/.local/bin/pyget.py`

*/10 will run the script every 10 minutes.

### Using systemd and a timer

The included service and timer files can be used to create a timed systemd service:

1) Copy them with `cp pyget.service ~/.config/systemd/user/` and `cp pyget.timer ~/.config/systemd/user/`
2) Reload systemd with `systemctl --user daemon-reload`
3) Enable the timer with `systemctl --user enable --now pyget.timer` 
