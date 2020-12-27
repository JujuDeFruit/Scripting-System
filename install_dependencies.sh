#!/bin/bash

# Check python 3 version, and be sure it is installed correctly. 
# On linux istribution, python is always pre-installed, 
# but it is to be sure.

python3 --version

# Install Pip if it is not installed yet.
# Pip is a dependencies manager. It simplifies libraries imports.
sudo apt-get install python3-pip

# Check pip is correctly installed.
python3 -m pip --version

# Now, install dependencies easily via pip.
# Pip is not added to environment path, 
# that is why we use python command to call pip module.

python3 -m pip install email_validator
python3 -m pip install pysftp
python3 -m pip install urllib3

# Configure rights on files
# Find all python, bash files and folders in this folder 
# and allow them just to be executed.
sudo find . -type f -iname "*.sh" -exec chmod 511 {} \;
sudo find . -type f -iname "*.py" -exec chmod 511 {} \;
sudo find . -type d ! -name "." -exec chmod 511 {} \;
# Config file can be change by anyone.
sudo find . -type f -iname "config.json" -exec chmod 777 {} \;
# Log file can be read only.
sudo find . -type f -iname "log.log" -exec chmod 744 {} \;

# Create crontab and make archival automatic every day.
# Configure crontab to call main.py everyday at midnight.
# We suppose web server is launched 
# and we do not need to launch it manually.
# Each day at 11 pm (0 23) go to PWD (Scripting-System folder)
# and execute main.py. 
{ crontab -l -u $USER; echo "0 23 * * * cd $PWD; python3 main.py"; } | crontab -u $USER -

# Check crontab was created.
if sudo test -f "/var/spool/cron/crontabs/$USER"
then
	echo "Successfully crontab created in /var/spool/cron/crontabs."
	echo "Logs for this crontab are in /var/log/syslog."
	echo "To restart service, type sudo service cron restart/start."

	# Launch cron service
	sudo service cron start
else
	echo "Error: Cron file not created. Please create it manually as described in users' doc annexes."
fi
