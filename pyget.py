#!/usr/bin/python3 -u
"""
Newer, more modular python script for fetching torrents from rss feeds.
Author: thnikk
"""
import urllib.parse as up
from xml.etree import ElementTree as et
from datetime import datetime, timedelta
import concurrent.futures
import subprocess
import argparse
import json
import sys
import os
import requests

# Initialize parser
parser = argparse.ArgumentParser(
    description='pyget.py: A script for adding torrents from rss feeds.')
parser.add_argument('-i', action='store_true', help='Ignore blacklist')
parser.add_argument('-d', action='store_true', help='Dry run')
args = parser.parse_args()

pool = concurrent.futures.ThreadPoolExecutor()

default_config = {
    "client": {
        "host": "10.0.0.29",
        "port": "9091"
    },
    "feeds": [
        {
            "url": "https://nyaa.si/?page=rss",
            "path": "~/Videos/Anime",
            "age": 30,
            "common": "subsplease 720p -batch",
            "shows": {
                "Sousou no Frieren": "Season 01",
            }
        }
    ]
}


def load_config(path, default):
    """ Load or create json config with default """
    # Set up config file
    config_path = os.path.expanduser(path)
    # Check if config exists
    if os.path.exists(config_path):
        # If it does, load it as config
        print("Config found in", config_path)
        with open(config_path, 'r', encoding='utf-8') as config_file:
            return json.load(config_file)
    else:
        print("Config not found, creating in", config_path)
        with open(config_path, "w", encoding='utf-8') as config_file:
            json.dump(default, config_file, indent=4)
        print("Default config created. Please edit "
              f"{config_path} before running again.")
        sys.exit(0)


def add_torrents(client, path, url, age, blacklist):
    """ Get torrent files from rss feed """
    xml = requests.get(url, timeout=3)
    root = et.fromstring(xml.content)
    for tag in root.findall('./channel/item'):
        # Get torrent URL
        link = tag.find('link').text
        # Get torrent title
        title = tag.find('title').text
        # Get date
        date = datetime.strptime(
            tag.find("pubDate").text, '%a, %d %b %Y %H:%M:%S %z'
        ).replace(tzinfo=None)
        # If it's younger than specified age
        if (datetime.now() - date) < timedelta(days=age):
            if title not in blacklist or args.i:
                print(f"Downloading {title}")
                if args.d:
                    # Add it to transmission
                    subprocess.run(
                        ["transmission-remote",
                            f"{client}",
                            "-w", f"{path}",
                            "-a", f"{link}",
                         ],
                        check=False,
                        capture_output=True
                    )


config = load_config("~/.config/pyget.json", default_config)

# Generate torrent list with list comprehension
torrent_list = [torrent.split("  ")[-1].strip() for torrent in subprocess.run(
    ["transmission-remote",
     f"{config['client']['host']}:{config['client']['port']}", "-l"],
    check=True, capture_output=True).stdout.decode('utf-8').splitlines()]

# Iterate through feeds
for feed in config['feeds']:
    # Get base URL
    URL = feed['url']
    # Iterate through shows in feed
    for show, season in feed['shows'].items():
        # Split url into parts with urllib
        parts = up.urlparse(URL)
        # Get query dictionary
        query_dict = dict(up.parse_qsl(parts.query))
        # Append query to querystring
        query_dict['q'] = f"{show.lower()} {feed['common'].lower()}"
        # Add querystring to URL
        parts = parts._replace(query=up.urlencode(query_dict))
        # Get torrents for show
        pool.submit(
            add_torrents,
            f"{config['client']['host']}:{config['client']['port']}",
            f"{os.path.expanduser(feed['path'])}/{show}/{season}",
            up.urlunparse(parts),
            feed['age'],
            torrent_list
        )
pool.shutdown(wait=True)
