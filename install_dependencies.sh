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
