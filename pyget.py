#!/usr/bin/python3 -u
"""
Description: Pyget v3
Author: thnikk
"""
import os
import sys
import json
from subprocess import run, CalledProcessError
from datetime import datetime, timedelta
from xml.etree import ElementTree as et
import concurrent.futures
import requests


class Transmission():
    """ Transmission """
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.torrents = self.get_torrents()

    def add(self, url, path) -> None:
        """ Add torrents """
        run([
                "transmission-remote", f"{self.ip}:{self.port}", "-w",
                f"{path}", "-a", f"{url}",
            ], check=False, capture_output=True)

    def get_torrents(self) -> None:
        """ Get torrents in transmission """
        try:
            return [
                torrent.split("  ")[-1].strip() for torrent in run(
                    ["transmission-remote", f"{self.ip}:{self.port}", '-l'],
                    check=True, capture_output=True
                ).stdout.decode('utf-8').splitlines()]
        except CalledProcessError:
            print("Couldn't connect to daemon, exiting.", file=sys.stderr)
            sys.exit(1)


class Torrent():  # pylint: disable=too-few-public-methods
    """ Torrent """
    def __init__(self, url, title, date):
        self.url = url
        self.title = title
        self.date = date

    def old(self, age) -> bool:
        """ Check if torrent is within age limit """
        return (datetime.now() - self.date) < timedelta(days=age)


def get_config(path):
    """ Load config from path """
    try:
        with open(
            os.path.expanduser(path), 'r', encoding='utf-8'
        ) as file:
            return json.loads(file.read())
    except json.decoder.JSONDecodeError:
        print(
            "Couldn't decode json config, check for errors.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        with open(
            os.path.expanduser(path), 'w', encoding='utf-8'
        ) as file:
            file.write(json.dumps(
                {"client": {"host": "localhost", "port": "9091"},
                    "feeds": [
                        {
                            "enabled": False,
                            "url": "https://nyaa.si/?page=rss",
                            "path": "~/Videos/Anime",
                            "age": 30,
                            "uploader": "subsplease",
                            "common": "720p -batch",
                            "shows": {"Sousou no Frieren": "Season 01"}
                        },
                        {
                            "enabled": False,
                            "url": "https://torrentgalaxy.to/rss?user=29",
                            "path": "~/Videos/Shows",
                            "age": 30,
                            "filter": "720p",
                            "shows": {"Curb your Enthusiasm": "Season 12"}
                        }
                    ]}, indent=4))
        print(
            f"Default config created in {path}. "
            "Edit before running again to add shows.", file=sys.stderr)
        sys.exit(1)


def parse_xml(string):
    """ Parse xml from string into list """
    root = et.fromstring(string)
    output = []
    for tag in root.findall('./channel/item'):
        try:
            link = tag.find('link').text
            title = tag.find('title').text
            date = datetime.strptime(
                tag.find("pubDate").text, '%a, %d %b %Y %H:%M:%S %z'
            ).replace(tzinfo=None)
        except TypeError:
            continue
        output.append(Torrent(link, title, date))
    return output


def get_feed(feed, tr):
    """ Get individual feed """
    for show, season in feed['shows'].items():
        querystring = {"q": show.lower(), "u": ""}
        if 'uploader' in feed and 'common' in feed:
            for key, value in {"u": "uploader", "q": "common"}.items():
                try:
                    querystring[key] = " ".join(
                        [feed[value].lower(), querystring[key]])
                except KeyError:
                    pass
        xml = requests.get(feed['url'], params=querystring, timeout=3).content
        path = "/".join([feed['path'], show, season])
        torrents = parse_xml(xml)
        for torrent in torrents:
            if (
                torrent.title not in tr.torrents
                and torrent.old(feed['age'])
            ):
                if 'filter' in feed and feed['filter'] not in torrent.title:
                    continue
                print(f"Adding {torrent.title}")
                tr.add(torrent.url, path)


def main():
    """ Main function """
    config = get_config('~/.config/pyget.json')

    tr = Transmission(config['client']['host'], config['client']['port'])

    pool = concurrent.futures.ThreadPoolExecutor()

    for feed in config['feeds']:
        if 'enabled' in feed and feed['enabled']:
            pool.submit(get_feed, feed, tr)

    pool.shutdown(wait=True)


if __name__ == "__main__":
    main()
