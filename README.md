# pyget
A simple script for adding torrents from rss feeds. Since there's an item limit to RSS feeds, the script creates a feed for each show. It's slower, but it mitigates the limitation by giving more relevant results. This can help if you're trying to start downloading something a few weeks into a season.

## Configuration
Pyget uses a json file for easy and flexible configuration. Running the script for the first time will create ~/.config/pyget.json.

```
{
    "client": ...
    "feeds": [
        {
            "url": feed url,
            "path": path to create show/season folder in,
            "age": Max age of items to use from feed (in days),
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
I tried to use as few python dependencies as possible and instead used subprocess for communicating with the torrent client. All you should need is the system package `transmission-cli`, which is included with transmission on most linux distros. 

## Installation
You can install all relevant files with the makefile using `make install`. It's not enabled by default, and I recommend running the script manually to make sure your configuration is correct. Once you've verified that it's working, you can use `systemctl --user daemon-reload && systemctl --user enable --now pyget.timer` to enable the timer.
