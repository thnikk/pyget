# pyget
A simple script for adding torrents from rss feeds.

## Daemonizing

### Using a cronjob
This is easier but could make debugging harder. All you need to do is run `crontab -e` and add the line:

`*/10 * * * * /path/to/pyget.py`

Replace /path/to/pyget.py with the path of your executable and */10 will run the script every 10 minutes.

### Using systemd and a timer
Create `~/.config/systemd/user/pyget.service` with the contents:

```
[Unit]
Description=Add torrents from RSS
[Service]
ExecStart=/path/to/pyget.py
[Install]
WantedBy=default.target
```

You also need to create a timer file `~/.config/systemd/user/pyget.timer` with the contets:

```
[Unit]
Description=Run pyget.py every 10 minutes

[Timer]
OnCalendar=*:0/10
Persistent=true

[Install]
WantedBy=timers.target
```

Now you need to reload systemd with `systemctl --user daemon-reload` and then you can enable the timer with `systemctl --user enable --now pyget.timer` 