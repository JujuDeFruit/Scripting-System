# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 20:54:54 2020

@author: Julien
"""

import os
import logging
from datetime import datetime
from mattermost import Mattermost
from e_mail import EMail


class LogEmailMattermost:
    """
    Log class to manage log, e-mail content and mattermost notification content.

    Attributes
    ----------

    Methods
    -------

    """

    def __init__(self, email_config, notification):
        """
        Initialize log, e-mail content and notification content.

        Parameters
        ----------
        email_config: dict
            object containning all data needed to send e-mail properly such as addresses ...
        notification: string (enum type)
            Always, never or error to know when send mattermost notification.

        Returns
        -------
        None.

        """

        self.error_nb = 0
        self.warning_nb = 0

        # Initialize logging object.
        logging.basicConfig(
            # Log file
            filename="log.log",
            # This is an info log
            level=logging.INFO,
            # Log file writting format
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%d/%m/%Y %I:%M:%S %p",
            force=True,
        )

        # Initialize mattermost notification.
        self.mattermost = Mattermost(self)

        # Initialize e-mail object.
        self.email = EMail(email_config, self)

        # Get status to know if script has to send mattermost 
        # notification or not
        self.send_notification = notification
        if notification not in ("always", "error", "never"):
            self.send_notification = "always"
            self.warning(
                "JSON read",
                "Notifications keyword format not supported. Default value is always."
            )

        self.send_emails = email_config["send-emails"].lower()
        if email_config["send-emails"].lower() not in ("yes", "y", "no", "n"):
            self.send_emails = "yes"
            self.warning(
                "JSON read",
                "Sending email format not supported. Default value is Yes."
                )


    def info(self, current_action, message=None):
        """
        Add info type to all logs, such as log.log, notification and e-mail content.

        Parameters
        ----------
        current_action: string
            Action appears in recap file such as "JSON read", "send file" ...
        message: string, optional
            Add specific message.  The default is None.

        Returns
        -------
        None.

        """

        if message is not None:
            logging.info(current_action + ": " + message)
        else:
            logging.info("Task: \"" + current_action + "\" went smoothly.")

        self.mattermost.info(current_action)

        now = datetime.now().strftime("%H:%M:%S")
        if message is not None:
            self.email.add_content("INFO", message, now)
        else:
            self.email.add_content("INFO", '\"' + current_action + "\" occured properly.", now)


    def warning(self, current_action, message=None):
        """
        Create warning to be printed only in log file and e-mail recap.

        Parameters
        ----------
        current_action: string
            Action appears in recap file such as "JSON read", "send file" ...
        message : string
            Add specific message.  The default is None.

        Returns
        -------
        None.

        """

        self.warning_nb += 1

        if message is not None:
            logging.warning(current_action + ": " + message)
        else:
            logging.warning("Task: \"" + current_action + "\" raised a warning.")

        now = datetime.now().strftime("%H:%M:%S")
        if message is not None:
             self.email.add_content("WARNING", message, now)
        else:
            self.email.add_content("WARNING", '\"' + current_action + "\" raised a warning.", now)


    def error(self, current_action, message=None):
        """
        Add error type to all logs, such as log.log, notification and e-mail content.

        Parameters
        ----------
        current_action : string
            Action appears in recap file such as "JSON read", "send file" ...
        message : string, optional
            Add specific message. The default is None.

        Returns
        -------
        None.

        """

        self.error_nb += 1

        if message is not None:
            logging.error(current_action + ": " + message)
        else:
            logging.error("Task: \"" + current_action + "\" failed.")

        self.mattermost.error(current_action)

        now = datetime.now().strftime("%H:%M:%S")
        if message is not None:
            self.email.add_content("ERROR", message, now)
        else:
            self.email.add_content("ERROR", '\"' + current_action + "\" did not occured properly.", now)


    def get_logfile(self):
        """
        Get log filename, useful to attach log to e-mail.

        Parameters
        ----------

        Returns
        -------
        log_name :string
            Name of the current log file.

        """

        return str(
            os.path.basename(
                logging.getLoggerClass().root.handlers[0].baseFilename
                )
            )

    def send_all(self):
        """
        Send e-mail and mattermost notification.

        Parameters
        ----------
        None.

        Returns
        -------
        None.

        """

        msg = "Done"
        if self.error_nb > 0 and self.warning_nb > 0:
            msg = "Not done with " + str(self.error_nb) + " errors and " + str(self.warning_nb) + " warnings."
        if self.error_nb > 0:
            msg = "Not done with " + str(self.error_nb) + " errors."
        if self.warning_nb > 0:
            msg = "Done with " + str(self.warning_nb) + " warnings."

        logging.info(msg)

        if self.send_notification == "always" or self.send_notification == "error" and self.error_nb > 0:
            self.mattermost.send_mattermost_notification()

        if self.send_emails in ("yes", "y"):
            self.email.send_email()
