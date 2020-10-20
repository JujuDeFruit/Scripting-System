# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 17:48:18 2020

@author: Julien Raynal
"""

import requests

def sendMattermostNotification(payload_, logging_):
    
    url = "https://chat.telecomste.fr/";
    API_key = "otnp6d3trpf3peo1gdinzq77gh";
    hooks = url + "hooks/" + API_key;
 
    try:
        req = requests.post(hooks, json=payload_);
        print(req.status_code);
        if req.status_code != 200:
            raise Exception();
    except Exception:
        logging_.warning("Error occured during mattermost notification sending.Notification not sent.")
    