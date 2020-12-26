# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 17:18:02 2020

-- Configuration file template generator --

@author: Julien
"""
import os
import json
from modules.log_email_mattermost import LogEmailMattermost

data = {
    "zip": "my_zip",
    "file": "dumpfile",
    "time-to-save": "1",
    "sftp": {
        "ip": "my_sftp_ip",
        "user": "my_sftp_user",
        "password": "my_sftp_password",
    },
    "email": {
        "send-emails": "yes",
        "auth": {"email": "exemple@exemple.com", "password": "my_password_for_mail"},
        "server": {"ip": "smtp.mail.yahoo.com", "port": "465"},
        "log-file-attached": "yes",
        "title": "My Daily report",
        "dest": ["first@email.com", "second@email.com"],
    },
    "notification": "never",
}


if os.path.exists("config.json"):
    os.remove("config.json")

try:
    with open("config.json", "w") as config:
        json.dump(data, config, indent="\t")
except EnvironmentError:
    log = LogEmailMattermost()
    log.error("Generating config file")
