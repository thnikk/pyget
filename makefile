install:
	install -d ${HOME}/.local/bin/
	install -m 755 pyget.py ${HOME}/.local/bin/
	install -d ${HOME}/.config/systemd/user/
	install -m 644 pyget.service ${HOME}/.config/systemd/user/
	install -m 644 pyget.timer ${HOME}/.config/systemd/user/
