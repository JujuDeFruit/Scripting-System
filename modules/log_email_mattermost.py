# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 20:54:54 2020

@author: Julien
"""
# pylint: disable=R0201

import os
import logging
from datetime import datetime
from modules.mattermost import Mattermost
from modules.e_mail import EMail


class LogEmailMattermost:
    """
    Log class to manage log, e-mail content and mattermost notification content.

    Attributes
    ----------
    error_nb: int
        Number of errors occured while processing.
    warning_nb: int
        Number of warnings occured while processing.
    mattermost: Mattermost
        Object manages mattermost notification.
    email: EMail
        Object manage e-mails.
    send_notification: string
        Precise in each condition mattermost notification has to be send.
    send_emails: string
        Precise if e-mails have to be send.

    Methods
    -------
    info(current_action, message=None):
        Add info type to all logs, such as log.log, notification and e-mail content.
    warning(current_action, message=None):
        Create warning to be printed only in log file and e-mail recap.
    error(current_action, message=None):
        Add error type to all logs, such as log.log, notification and e-mail content.
    critical(current_action, message=None):
        Add critical type to log file only.
    get_logfile():
        Get log filename, useful to attach log to e-mail.
    send_all():
        Send e-mail and mattermost notification.

    """

    def __init__(self, email_config=None, notification=None):
        """
        Initialize log, e-mail content and notification content.

        Parameters
        ----------
        email_config: dict, optional
            object containning all data needed to send e-mail properly such as addresses ...
            Default is None.
        notification: string (enum type), optional
            Always, never or error to know when send mattermost notification.
            Default is None.

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
        )

        self.mattermost = None
        self.send_notification = None

        if notification is not None:
            # Get status to know if script has to send mattermost
            # notification or not
            self.send_notification = notification
            # Initialize mattermost notification.
            self.mattermost = Mattermost(self)
            if notification not in ("always", "error", "never"):
                self.send_notification = "always"
                self.warning(
                    "JSON read",
                    "Notifications keyword format not supported. Default value is always.",
                )

        self.email = None
        self.send_emails = None

        if email_config is not None:
            # Initialize e-mail object.
            self.email = EMail(email_config, self)
            # If an error occured in the constructor of e-mail,
            # then affect None to this variable to prevent default.
            if self.email.critical_nb > 0:
                self.email = None
                return

            try:
                self.send_emails = email_config["send-emails"].lower()
                if self.send_emails not in ("yes", "y", "no", "n"):
                    self.send_emails = "yes"
                    self.warning(
                        "JSON read",
                        "Sending email format not supported. Default value is Yes.",
                    )

            except KeyError as err:
                self.warning(
                    "Getting email config",
                    "Missing keyword '"
                    + err.args[0]
                    + "' in e-mail bracket in config file. \
To be sure to have all keywords, please regenerate config file template.",
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
            logging.info("%s: %s", current_action, message)
        else:
            logging.info('Task: "%s" went smoothly.', current_action)

        if self.mattermost is not None:
            self.mattermost.info(current_action)

        now = datetime.now().strftime("%H:%M:%S")
        if self.email is not None:
            if message is not None:
                self.email.add_content("INFO", current_action + ": " + message, now)
            else:
                self.email.add_content(
                    "INFO", '"' + current_action + '" occured properly.', now
                )

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
            logging.warning("%s: %s", current_action, message)
        else:
            logging.warning('Task: "%s" raised a warning.', current_action)

        now = datetime.now().strftime("%H:%M:%S")
        if self.email is not None:
            if message is not None:
                self.email.add_content("WARNING", current_action + ": " + message, now)
            else:
                self.email.add_content(
                    "WARNING", '"' + current_action + '" raised a warning.', now
                )

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
            logging.error("%s: %s", current_action, message)
        else:
            logging.error('Task: "%s" failed.', current_action)

        if self.mattermost is not None:
            self.mattermost.error(current_action)

        now = datetime.now().strftime("%H:%M:%S")
        if self.email is not None:
            if message is not None:
                self.email.add_content("ERROR", current_action + ": " + message, now)
            else:
                self.email.add_content(
                    "ERROR", '"' + current_action + '" did not occured properly.', now
                )

    def critical(self, current_action, message=None):
        """
        Add critical type to log file.

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

        if message is not None:
            logging.critical("%s: %s", current_action, message)
        else:
            logging.critical('Task: "%s" failed.', current_action)

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
            os.path.basename(logging.getLoggerClass().root.handlers[0].baseFilename)
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

        if self.mattermost is not None and self.send_notification is not None:
            if (
                    self.send_notification == "always"
                    or self.send_notification == "error"
                    and self.error_nb > 0):
                self.mattermost.send_mattermost_notification()

        if self.send_emails is not None and self.email is not None:
            if self.send_emails in ("yes", "y"):
                self.email.send_email()

        if self.error_nb > 0 and self.warning_nb > 0:
            msg = (
                "Not done with "
                + str(self.error_nb)
                + " errors and "
                + str(self.warning_nb)
                + " warnings."
            )
        elif self.error_nb > 0:
            msg = "Not done with " + str(self.error_nb) + " errors."
        elif self.warning_nb > 0:
            msg = "Done with " + str(self.warning_nb) + " warnings."
        else:
            msg = "Done"

        if self.error_nb > 0:
            logging.error(msg)
        else:
            logging.info(msg)
