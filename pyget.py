#!/usr/bin/python3
''' pyget.py: A simple script for adding torrents from rss feeds.'''
__author__      = "Jack Reitano"
__license__     = "GPL"
__version__     = "0.1"
__maintainer__  = "Jack Reitano"

# Import libraries
import os # Expand user and check files 
import json # Dump and load json config file
import urllib.parse # Encode string for URL
import requests # Get XML file
from xml.etree import ElementTree # Parse XML
from datetime import datetime,timedelta # Compare published date to current date
import argparse # Parse arguments for clearing cache and dry run

# Initialize parser
parser = argparse.ArgumentParser(description='pyget.py: A simple script for adding torrents from rss feeds.')
parser.add_argument('-c', '--clear', action='store_true', dest='clear', help='Clear cache')
parser.add_argument('-d', '--dry', action='store_true', dest='dry', help='Dry run')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
args = parser.parse_args()

# Set up cache file
cache_file = os.path.expanduser('~/.cache/pyget.cache')
if not os.path.exists(cache_file):
    open(cache_file, 'a').close()

# If -c flag is given, clear the cache file
if args.clear:
    open(cache_file, 'w').close()
# If -d flag is given, don't connect to the torrent client and don't download anything
if args.dry:
    print("DRY RUN - Nothing will be downloaded")

# Set up config file
config_file = os.path.expanduser("~/.config/pyget.json")
# Check if config exists
if os.path.exists(config_file):
    # If it does, load it as config
    print("Config found in", config_file)
    with open(config_file, 'r') as f:
        config = json.load(f)
else:
    # Otherwise, create it and quit
    print("Config not found, creating in", config_file)
    config = {
        "client": "transmission",
        "feeds": [
            {
            "url": "https://nyaa.si/?page=rss&u=subsplease&q=720p+-batch",
            "directory": "/mnt/media2/Videos/Anime",
            "days": 30,
            "shows": {
                "Made in Abyss": "Season 02",
                "Yofukashi no Uta": "Season 01"
                },
            },
            {
            "url": "https://nyaa.si/?page=rss&u=Erai-raws&q=720p+-batch",
            "directory": "/mnt/media2/Videos/Anime",
            "days": 30,
            "shows": {
                "Isekai Ojisan": "Season 01"
                },
            }
        ]
    }
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)
    print("Default config created. Please edit before running again.")
    quit()

# Initialize torrent client
if args.dry:
    print("Skipping torrent client connection")
elif config['client'] == "transmission":
    from transmission_rpc import Client # Add torrent to transmission
    try:
        c = Client()
    except:
        print("Transmission daemon is not running")
        quit()
elif config['client'] == "deluge":
    from deluge_client import DelugeRPCClient # Add torrent to deluge
    import base64 # Encode torrent file for deluge
    try:
        from deluge_client import LocalDelugeRPCClient
        c = LocalDelugeRPCClient()
        c.connect()
    except:
        print("Deluged is not running")
        quit()
else: 
    print("Invalid/missing torrent client")

# Iterate through feeds
for feed in config['feeds']:
    # Get the base url for the feed
    base_url = feed['url']
    # Iterate through shows
    for show,season in feed['shows'].items():
        # Get the show URL
        parts = urllib.parse.urlparse(base_url)                             # Split the URL into parts
        query_dict = dict(urllib.parse.parse_qsl(parts.query))              # Get the querystring and convert to dictionary
        try:
            query_dict['q'] += " " + show.lower()                           # Append the show name to the search query
        except:
            query_dict['q'] = show.lower()                                  # or create a new search query if one doesn't exist
        parts = parts._replace(query=urllib.parse.urlencode(query_dict))    # Replace the querystring with the new one
        show_url = urllib.parse.urlunparse(parts)                           # Re-assemble the URL
        # Get the XML file
        xml_file = requests.get(show_url)
        # Convert XML to ElementTree object
        try:
            root = ElementTree.fromstring(xml_file.content)
        except:
            print("Could not parse XML, skipping feed.")
            continue
        count = 0
        # Parse XML
        for type_tag in root.findall('./channel/item'):
            # Get title from xml
            title = type_tag.find("title").text
            # Get url from xml
            torrent_url = type_tag.find("link").text
            # Get date from XML and convert to datetime object
            date = datetime.strptime(type_tag.find("pubDate").text, '%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=None)
            # Skip if older than configured time in days or ignore if time set to 0
            if (datetime.now() - date) > timedelta(days=int(feed['days'])) and int(feed['days']) != 0:
                continue
            if args.dry:
                # Print that the file was found
                print("Found", title)
            else:
                # Skip if file already in cache
                with open(cache_file) as f:
                    if title in f.read():
                        continue
                try:
                    # Transmission is simple and nice
                    if config['client'] == "transmission":
                        c.add_torrent(torrent_url, download_dir = feed['directory'] + "/" + show + "/" + season)
                    # Deluge is annoying
                    elif config['client'] == "deluge":
                        # Set download directory
                        opts={"download_location": feed['directory'] + "/" + show + "/" + season}
                        # Get the torrent file
                        torrent_file = requests.get(torrent_url)
                        # Encode the contents of the file
                        filedump = base64.b64encode(torrent_file.content)
                        c.call('core.add_torrent_file', "test", filedump, opts)
                    # Print that the file was added
                    # print("Added", title)
                    # Append name to cache file
                    with open(cache_file, 'a') as f:
                        f.write(title + '\n')
                    count = count+1
                except:
                    # This shouldn't happen, but the code will break if it does.
                    print("Torrent already added")
        if count > 0 or args.verbose:
            print(show + ":", count, "episodes added.")





