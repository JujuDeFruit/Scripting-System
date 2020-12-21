# -*- coding: utf-8 -*-
"""
    E-mail managing

    @author: Julien Raynal
"""
# pylint: disable=E0611
# pylint: disable=E0401
# pylint: disable=R0902

import json
import os
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from email_validator import validate_email


class EMail:
    """
    A class to represent a ssh connection.

    Attributes
    ----------
    server: object
        secured connection to server
    logging : log object
        object to interact with log file
    ip_server : string
        e-mail server IP.
    auth : dict
        get identification to server (username & password)
    log_file_attached : boolean
        information to know if user wants log file attached to email or not
    title:
        e-mail title
    content : string
        mail content
    dest: array of strings
        all e-mail addresses to send e-mail

    Methods
    -------
    attachment(msg):
        msg: message object
        attach log file to e-mail
    login_and_send():
        log-in server and send e-mail to all destination e-mail addresses
    email_server_smtp():
        send e-mail via smtp server
    internal_server():
        send e-mail via internal server
    send():
        send e-mail

    """

    def __init__(self, json_, logging_):

        """
        Constructor to build the mail instance

        Parameters
        ----------
        json_: dict
            Contains all e-mail parameters in config file.
        logging_: log object
            log object to write in log file.
        port: int
            Port used to connect to e-mail server.

        """

        self.server = None
        self.logging = logging_

        # Authentification of sender email.
        auth_ = json_["auth"]
        # Choice of user to attach or not log file.
        log_file_attached_ = json_["log-file-attached"].lower()
        # Subject of the mail.
        title_ = json_["title"]
        # Array of all destination emails.
        dest_ = json_["dest"]
        # Get the mail external server IP.
        self.ip_server = json_["server"]["ip"]
        self.content = ""

        try:
            # Try to cast port value from JSON to int.
            self.port = int(json_["server"]["port"])
        except ValueError:
            self.port = 465
            # If value is not supported, default port value is 465.
            self.logging.warning(
                "Email server port format not supported. \
Default value is 465."
            )

        if auth_["email"] == "":
            self.logging.warning(
                "Blank at the sending email \
identifier in the conf file : \
example@ex.com. Email(s) not sent."
            )
            self.content += "| Email | :exclamation: Error |\n"

        if auth_["password"] == "":
            self.logging.warning(
                "Blank at the sending email \
password in the conf file. Email(s) not sent."
            )
            self.content += "| Email | :exclamation: Error |\n"

        # If user did not input a correct format for attachment.
        if log_file_attached_ not in ("yes", "no", "y", "n"):
            self.logging.warning(
                "Uncorrect value for attached log in conf file. Yes by default"
            )
            log_file_attached_ = "yes"

        if title_ == "":
            self.logging.warning(
                "No title for email, 'Scripting System rapport' by default"
            )
            # Default e-mail object.
            title_ = "Scripting System rapport"

        if len(dest_) == 0:
            self.logging.warning("No destination emails !")
        else:
            for email_dest in dest_:
                if not validate_email(email_dest):
                    self.logging.warning(email_dest + " is not valid !")
                    dest_.remove(email_dest)

        self.auth = auth_
        self.log_file_attached = log_file_attached_
        self.title = title_
        self.dest = dest_
        # self.email_content = email_content_

    def attachment(self, msg_):
        """
        Attach log file to MIME message if user decided it.

        Parameter
        ---------
        msg_: message object
            Message to attach file

        Return
        ------
        msg_: message object
            Message with or not attached file

        """
        # If user wrote 'Yes' or 'Y' to attach file to e-mail.
        if self.log_file_attached == "yes" or self.log_file_attached == "y":
            try:
                log_filename = str(
                    os.path.basename(
                        logging.getLoggerClass().root.handlers[0].baseFilename
                    )
                )
                with open(log_filename, "rb") as attachment:
                    # instance of MIMEBase and named as mime_instance
                    mime_instance = MIMEBase("application", "octet-stream")

                    # To change the payload into encoded form
                    mime_instance.set_payload((attachment).read())

                    # encode into base64
                    encoders.encode_base64(mime_instance)

                    # Change mail header to dispose attachment
                    mime_instance.add_header(
                        "Content-Disposition", "attachment filename= " + log_filename
                    )

                    # attach the instance 'mime_instance' to instance 'msg'
                    msg_.attach(mime_instance)
                    self.logging.info("Attachment is OK.")
                    self.content += "| Attachment | :white_check_mark: OK |\n"

            except EnvironmentError:
                self.logging.warning(
                    "Unknown error occured during mail \
attachment loading. No attachment send with mails."
                )
                self.content += "| Attachment | :exclamation: Error |\n"

        return msg_

    def login_and_send(self):
        """
        Log-in to e-mail account and send e-mail to all valid e-mails destinations.

        Parameters
        ----------

        Return
        ------

        """

        try:
            # Log-in to the sender e-mail.
            self.server.login(self.auth["email"], self.auth["password"])

            # Create a MIME message that will be send. Use MIME type to attach log file if needed.
            msg = MIMEMultipart()
            # Subject of the send e-mail.
            msg["Subject"] = self.title
            # Add text content to the mail.
            msg.attach(MIMEText(self.content, "plain"))  # self.email_content
            # Attach log file to message if needed.
            msg = self.attachment(msg)
            # Convert the MIME message into string to send it as a string
            # to all destination e-mails.
            self.server.sendmail(self.auth["email"], self.dest, msg.as_string())

            # Close the server connection after using resources.
            self.server.quit()

            self.logging.info("Emails send.")
            self.content += "| Sending e-mails | :white_check_mark: OK |\n"

        # Auth error
        except smtplib.SMTPAuthenticationError:
            self.logging.warning(
                "The server did not accept the username/password combination."
            )
            self.content += "| Sending e-mails | :exclamation: Error |\n"

        except smtplib.SMTPRecipientsRefused:
            self.logging.warning("All recipients were refused. Nobody got the mail.")
            self.content += "| Sending e-mails | :exclamation: Error |\n"

        except smtplib.SMTPSenderRefused:
            self.logging.warning("The server didn’t accept the sending address.")
            self.content += "| Sending e-mails | :exclamation: Error |\n"

        except smtplib.SMTPDataError:
            self.logging.warning(
                "The server replied with an unexpected error code \
                    (other than a refusal of a recipient)."
            )
            self.content += "| Sending e-mails | :exclamation: Error |\n"

        # Another error
        except smtplib.SMTPException:
            self.logging.warning(
                "Unknown error occured while logging-in\
                                 to your mail account. Email(s) not sent."
            )
            self.content += "| Sending e-mails | :exclamation: Error |\n"

    def email_server_smtp(self):
        """
        Create a secure connection to SMTP server to send e-mails from external server.

        Parameters
        ----------

        Return
        ------

        """

        # Create a secure SSL context
        context = ssl.create_default_context()

        # Open secure connection with SMTP server to send e-mails
        self.server = smtplib.SMTP_SSL(self.ip_server, port=self.port, context=context)
        # Log to e-mail account and send e-mails to destinations
        self.login_and_send()

    def internal_server(self):
        """
        Create a connection ton internal e-mail server of PC and send e-mails through it.
        Server configured with "hMailServer", domain : "localhost.com", password : "35279155".
        Account is "admin@localhost.com" and password is "admin".

        Parameters
        ----------

        Return
        ------

        """

        # context = ssl.create_default_context()
        with smtplib.SMTP("localhost") as server:
            server.login("admin@localhost.com", "admin")
            msg = MIMEMultipart()
            msg["Subject"] = "Object"
            server.sendmail(
                "admin@localhost.com", ["raynaljulien70@gmail.com"], msg.as_string()
            )

    def send(self):
        """
        If IP origin is empty, then send mail with internal server.

        Parameters
        ----------

        Return
        ------

        """
        if self.ip_server != "":
            self.email_server_smtp()
        else:
            self.internal_server()


if __name__ == "__main__":

    with open("conf.txt", "r") as json_config:
        data = json.load(json_config)
        # data['email']['server']['ip'] = ''
        email = EMail(data["email"], logging, "")
    email.send()
