# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 17:48:18 2020

@author: Julien Raynal
"""

#pylint: disable=R0903

import requests

class Mattermost:
    """
    A class to interact with mattermost TSE server.

    Attributes
    ----------
    payload: dict
        content of the notification
    logging : log object
        object to interact with log file
    hooks : string
        url to send notification

    Methods
    -------
    send_mattermost_notification():
        send notification to mattermost TSE server.

    """


    def __init__(self, text_, logging_):
        self.payload = {
            "icon_url": "https://www.mattermost.org/wp-content/uploads/2016/04/icon.png",
            "text": text_,
        }
        self.logging = logging_

        url = "https://chat.telecomste.fr/"
        api_key = "otnp6d3trpf3peo1gdinzq77gh"

        self.hooks = url + "hooks/" + api_key


    def send_mattermost_notification(self):
        """
        Send notification

        Parameters
        ----------

        """
        try:
            # Post request on Mattermost TSE server
            req = requests.post(self.hooks, json=self.payload)
            # Raise error if request was not accepted.
            req.raise_for_status()

        except requests.ConnectionError:

            self.logging.warning(
                "Error occured during mattermost notification sending. \
Notification not sent. Network error."
                )

        except requests.exceptions.HTTPError as err:
            self.logging.warning(
                "Error occured during mattermost notification sending. \
Notification not sent. " + err.args[0]
            )

        except requests.exceptions.Timeout:
            self.logging.warning(
                "Error occured during mattermost notification sending. \
Notification not sent. Timeout."
            )

        except requests.exceptions.RequestException:
            self.logging.warning(
                "Error occured during mattermost notification sending. \
Notification not sent. Unknown error."
            )
