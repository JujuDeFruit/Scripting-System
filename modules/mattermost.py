# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 17:48:18 2020

Mattermost notification managing

@author: Julien Raynal
"""

# pylint: disable=R0903
# pylint: disable=W0612

import requests


class Mattermost:
    """
    A class to interact with mattermost TSE server.

    Attributes
    ----------
    log_email_matt : LogEmailMattermost
        Object to manage all logs, log file, e-mail and mattermost notification.
    hooks : string
        url to send notification
    mattermost_content: dict
        content of the notification

    Methods
    -------
    info(task):
        Add a well progress task to notification.
    error(task):
        Add a well progress task to notification.
    format_data():
        Set data to mattermost format to be send as an array.
    send_mattermost_notification():
        send notification to mattermost TSE server.

    """

    def __init__(self, logs):
        """
        Constructor. Initialize all attributes.

        Parameters
        ----------
        logs: log object
            Object to manage all logs, log file, e-mail and mattermost notification.

        Returns
        -------
        None.

        """

        self.log_email_matt = logs

        self.hooks = (
            "https://chat.telecomste.fr/" + "hooks/" + "otnp6d3trpf3peo1gdinzq77gh"
        )

        # Initialize mattermost notification content.
        self.mattermost_content = {
            "tasks": [
                " Progress             ",
                ":-------------------------------",  # 30 dashes
            ],
            "state": [" State              ", ":-------------------"],
        }

    def info(self, task):
        """
        Add a well progress task to notification.

        Parameters
        ----------
        task : string
            Task to add to mattermost notification.

        Returns
        -------
        None.

        """

        max_size = len(self.mattermost_content["tasks"][1])
        for i in range(max_size - len(task) + 1):
            # Add the difference of spaces between max size and task size.
            task += " "
        # Add the task to tasks array
        self.mattermost_content["tasks"].append(task)
        # Add the state to states array
        self.mattermost_content["state"].append(" :white_check_mark: ")

    def error(self, task):
        """
        Add a well progress task to notification.

        Parameters
        ----------
        task : string
            Task to add to mattermost notification.

        Returns
        -------
        None.

        """

        max_size = len(self.mattermost_content["tasks"][1])
        for i in range(max_size - len(task) + 1):
            # Add the difference of spaces between max size and task size.
            task += " "
        # Add the task to tasks array
        self.mattermost_content["tasks"].append(task)
        # Add the state to states array
        self.mattermost_content["state"].append(" :no_entry:         ")

    def format_data(self):
        """
        Set data to mattermost format to be send as an array.

        Parameters
        ----------

        Returns
        -------
        formatted_data: string
            String of formatted data.

        """

        formatted_data = ""

        # Spaces are already accounted when tasks are added.
        for i in range(len(self.mattermost_content["tasks"])):
            formatted_data += (
                "|"
                + self.mattermost_content["tasks"][i]
                + "|"
                + self.mattermost_content["state"][i]
                + "|\n"
            )
        return formatted_data

    def send_mattermost_notification(self):
        """
        Send notification.

        Parameters
        ----------

        Returns
        -------
        None.

        """

        # Format data to be prepared to be sent.
        formatted_data = self.format_data()

        payload = {
            "icon_url": "https://www.mattermost.org/wp-content/uploads/2016/04/icon.png",
            "text": formatted_data,
        }

        try:
            # Post request on Mattermost TSE server
            req = requests.post(self.hooks, json=payload)
            # Raise error if request was not accepted.
            req.raise_for_status()

        except requests.exceptions.ConnectionError:
            self.log_email_matt.warning(
                "Mattermost notification",
                "Notification not sent. Connection error, please check\
your mattermost chat is still runinng.",
            )

        except requests.exceptions.HTTPError as err:
            self.log_email_matt.warning(
                "Mattermost notification",
                "Notification not sent. HTTP error code: " + err.args[0],
            )

        except requests.exceptions.Timeout:
            self.log_email_matt.warning(
                "Mattermost notification",
                "Notification not sent. Timeout, please retry.",
            )

        except requests.exceptions.RequestException:
            self.log_email_matt.warning("Mattermost notification", "Unknown error.")
