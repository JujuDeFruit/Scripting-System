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
    "zip": "",
    "file": "",
    "time-to-save": "1",
    "sftp": {"ip": "", "user": "", "password": ""},
    "email": {
        "send-emails": "yes",
        "auth": {"email": "", "password": ""},
        "server": {"ip": "", "port": ""},
        "log-file-attached": "yes",
        "title": "",
        "dest": [],
    },
    "notification": "error",
}

if os.path.exists("config.json"):
    os.remove("config.json")

try:
    with open("config.json", "w") as config:
        json.dump(data, config, indent="\t")
except EnvironmentError:
    log = LogEmailMattermost()
    log.error("Generating config file")
