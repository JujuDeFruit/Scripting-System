# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 17:48:18 2020

@author: Julien Raynal
"""

import requests

class Mattermost:
    
    def __init__(self, text_, logging_):
        self.payload = { "icon_url": "https://www.mattermost.org/wp-content/uploads/2016/04/icon.png", "text": text_ };
        self.logging = logging_;
        
        url = "https://chat.telecomste.fr/";
        API_key = "otnp6d3trpf3peo1gdinzq77gh";
        self.hooks = url + "hooks/" + API_key;

    def sendMattermostNotification(self):
        try:
            req = requests.post(self.hooks, json=self.payload);
            print(req.status_code);
            if req.status_code != 200:
                raise Exception();
        except Exception:
            self.logging.warning("Error occured during mattermost notification sending.Notification not sent.") 
    