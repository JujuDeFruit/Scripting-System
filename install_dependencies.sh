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

# Create crontab and make archival automatic every day.
{ crontab -l -u $USER; echo "0 0 * * * cd $PWD; python3 main.py"; } | crontab -u $USER -

# Configure crontab to call main.py everyday at midnight.
# We suppose web server is launched 
# and we do not need to launch it manually.
# Each day at midnight (0 0) go to PWD (Scripting-System folder)
# and execute main.py. It is written in good crontab.

echo "Successfully crontab created in /var/spool/cron/crontabs."
echo "Logs for this crontab are in /var/log/syslog."
echo "To restart service, type sudo service cron restart/start."

# Launch cron service
sudo service cron start
