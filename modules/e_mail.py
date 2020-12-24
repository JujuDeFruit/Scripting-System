# -*- coding: utf-8 -*-
"""
    E-mail managing

    @author: Julien Raynal
"""
# pylint: disable=E0611
# pylint: disable=E0401
# pylint: disable=R0902

import re
import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from email_validator import validate_email


class EMail:
    """
    Class to manage e-mail.

    Attributes
    ----------
    server: object
        Secured connection to server.
    email_content: array of strings
        Content of sent e-mail. Each line of array is a new line in e-mail.
    critical_nb: int
        Number of critical occured while processing. It is like a boolean,
        on the ground program quit when encounter at least on critical.
    log_email_matt : LogEmailMattermost
        Object to interact with all logs.
    ip_server : string
        E-mail server IP.
    port: int
        Port used for connection to server.
    auth : dict
        Get identification to server (username & password)
    log_file_attached : string
        Information to know if user wants log file attached to email or not
    title: string
        E-mail title
    dest: array of strings
        All e-mail addresses to send e-mail.

    Methods
    -------
    login():
        Log-in server.
    login_and_send():
        Log-in server and send e-mail to all destination e-mail addresses.
    smtp_server():
        Send e-mail via smtp server.
    internal_server():
        Send e-mail via internal server.
    add_content(message_type, message, time):
        Add string content to e-mail content.
    attachment(msg):
        Attach log file to e-mail.
    format_data():
        Format e-mail content data to be prepared to be sent.
    send_email():
        Send e-mail by choosing internal or smtp server.

    """

    def __init__(self, json_, log):

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
        self.email_content = []

        self.critical_nb = 0

        # Get log object
        self.log_email_matt = log

        try:
            # Authentification of sender email.
            auth_ = json_["auth"]
            # Choice of user to attach or not log file.
            log_file_attached_ = json_["log-file-attached"].lower()
            # Subject of the mail.
            title_ = json_["title"]
            # Array of all destination emails.
            dest_ = json_["dest"]

            port_ = json_["server"]["port"]

            # Get the mail external server IP.
            self.ip_server = json_["server"]["ip"]

        except json.JSONDecodeError:
            self.log_email_matt.warning(
                "Getting email config",
                "E-mail config need correct values. There must be \
compilation errors in e-mail section in config file."
            )
            self.critical_nb += 1
            return

        except KeyError as err:
            self.log_email_matt.warning(
                "Getting email config",
                "Missing keyword '"
                + err.args[0]
                + "' in e-mail bracket in config file. \
To be sure to have all keywords, please regenerate config file template.",
            )
            self.critical_nb += 1
            return

        if (
                not re.fullmatch(r"(\d{1,3}.){3}\d{1,3}", self.ip_server)
                and self.ip_server.split(".")[0] != "smtp"
                ):
            self.ip_server = ""

        try:
            # Try to cast port value from JSON to int.
            self.port = int(port_)
        except ValueError:
            self.port = 465
            # If value is not supported, default port value is 465.
            self.log_email_matt.warning(
                "Getting email config",
                "Email server port format not supported. Default value is 465.",
            )

        if auth_["email"] == "":
            self.log_email_matt.warning(
                "Getting email config",
                "Blank at the sending email identifier in the conf file : \
example@ex.com. Email(s) not sent.",
            )

        if auth_["password"] == "":
            self.log_email_matt.warning(
                "Getting email config",
                "Blank at the sending email password in the conf file. \
Email(s) not sent.",
            )

        # If user did not input a correct format for attachment.
        if log_file_attached_ not in ("yes", "no", "y", "n"):
            log_file_attached_ = "yes"
            self.log_email_matt.warning(
                "Getting email config",
                "Uncorrect value for attached log in conf file. Yes by default",
            )

        if title_ == "":
            # Default e-mail object.
            title_ = "Scripting System rapport"
            self.log_email_matt.warning(
                "Getting email config",
                "No title for email, 'Scripting System rapport' by default",
            )

        if len(dest_) == 0:
            self.log_email_matt.warning(
                "Getting email config", "No destination emails !"
            )
        else:
            for email_dest in dest_:
                if not validate_email(email_dest):
                    self.log_email_matt.warning(
                        "Getting email config", email_dest + " is not valid !"
                    )
                    dest_.remove(email_dest)

        # Affect all values
        self.auth = auth_
        self.log_file_attached = log_file_attached_
        self.title = title_
        self.dest = dest_

    def login(self):
        """
        Log-in mail server.

        Parameters
        ----------

        Returns
        -------
        None.

        """
        try:
            # Log-in to the sender e-mail.
            self.server.login(self.auth["email"], self.auth["password"])

        except smtplib.SMTPAuthenticationError:
            self.log_email_matt.warning(
                "Logging-in email server",
                "The server did not accept the username/password combination. \
E-mails not sent.",
            )

        except smtplib.SMTPNotSupportedError:
            self.log_email_matt.warning(
                "Logging-in email server",
                "The AUTH command is not supported by the server. \
E-mails not sent.",
            )

        # Another error
        except smtplib.SMTPException:
            self.log_email_matt.warning(
                "Logging-in email server",
                "Unknown error occured while logging-in to your mail account. \
E-mail(s) not sent.",
            )

    def login_and_send(self):
        """
        Log-in to e-mail account and send e-mail to all valid e-mails destinations.

        Parameters
        ----------

        Returns
        -------
        None.

        """

        try:
            # Log-in e-mail server.
            self.login()

            # Create a MIME message that will be send. Use MIME type to attach log file if needed.
            msg = MIMEMultipart()

            # Subject of the send e-mail.
            msg["Subject"] = self.title

            # Add text content to the mail.
            msg.attach(MIMEText(self.format_data(), "plain"))

            # Attach log file to message if needed.
            msg = self.attachment(msg)

            # Convert the MIME message into string to send it as a string
            # to all destination e-mails.
            self.server.sendmail(self.auth["email"], self.dest, msg.as_string())

            self.log_email_matt.info("Sending e-mails")

        except smtplib.SMTPRecipientsRefused:
            self.log_email_matt.warning(
                "Sending e-mails",
                "All recipients were refused. Nobody got the mail. \
E-mail(s) not sent.",
            )

        except smtplib.SMTPSenderRefused:
            self.log_email_matt.warning(
                "Sending e-mails",
                "The server did not accept the sending address(es). \
E-mail(s) not sent.",
            )

        except smtplib.SMTPDataError:
            self.log_email_matt.warning(
                "Sending e-mails",
                "The server replied with an unexpected error code \
(other than a refusal of a recipient).E-mail(s) not sent.",
            )

        # Another error
        except smtplib.SMTPException:
            self.log_email_matt.warning(
                "Sending e-mails",
                "Unknown error occured while sending e-mails. \
Email(s) not sent.",
            )

        finally:
            # Close the server connection after using resources.
            if self.server is not None:
                self.server.quit()

    def smtp_server(self):
        """
        Create a secure connection to SMTP server to send e-mails from external server.

        Parameters
        ----------

        Returns
        -------
        None.

        """

        # Create a secure SSL context
        context = ssl.create_default_context()

        try:
            # Open secure connection with SMTP server to send e-mails
            self.server = smtplib.SMTP_SSL(
                self.ip_server, port=self.port, context=context
            )

        except TimeoutError:
            self.log_email_matt.warning(
                "E-mail server connection",
                "Timeout error, check e-mail server is not down. E-mails not sent.",
            )

        if self.server is not None:
            # Log to e-mail account and send e-mails to destinations
            self.login_and_send()

    def internal_server(self):
        """
        Create a connection ton internal e-mail server of PC and send e-mails through it.
        Server configured with "hMailServer", domain : "localhost.com", password : "35279155".
        Account is "admin@localhost.com" and password is "admin".

        Parameters
        ----------

        Returns
        -------
        None.

        """

        try:
            # context = ssl.create_default_context()
            with smtplib.SMTP("localhost") as server:
                server.login("admin", "admin")
                msg = MIMEMultipart()
                msg["Subject"] = "Object"
                server.sendmail(
                    "script@localhost.com", ["raynaljulien70@gmail.com"], msg.as_string()
                )
        except Exception:
            pass

    def add_content(self, message_type, message, time):
        """
        Add content to e-mail corps.

        Parameters
        ----------
        message_type : string
            INFO, ERROR ...
        message : string
            Message to print.
        time: string (format %H:%M:%S)
            Time info occured.

        Returns
        -------
        None.

        """
        self.email_content.append(time + " - " + message_type + ": " + message)

    def attachment(self, msg):
        """
        Attach log file to MIME message if user decided it.

        Parameter
        ---------
        msg: message object
            Message to attach file

        Return
        ------
        msg: message object
            Message with or not attached file

        """
        # If user wrote 'Yes' or 'Y' to attach file to e-mail.
        if self.log_file_attached in ("yes", "y"):
            try:
                # Get log filename. If this one change, no need to change its name there.
                log_filename = self.log_email_matt.get_logfile()

                # instance of MIMEBase and named as mime_instance
                mime_instance = MIMEBase("application", "octet-stream")

                with open(log_filename, "rb") as attachment:

                    # To change the payload into encoded form
                    mime_instance.set_payload(attachment.read())

                    # encode into base64
                    encoders.encode_base64(mime_instance)

                    # Change mail header to dispose attachment
                    mime_instance.add_header(
                        "Content-Disposition", "attachment; filename= " + log_filename
                    )

                    # attach the instance 'mime_instance' to instance 'msg'
                    msg.attach(mime_instance)

                    self.log_email_matt.info("Attachment")

            # Catching opening file exception.
            except EnvironmentError:
                self.log_email_matt.warning(
                    "Attachment",
                    "Unknown error occured during mail attachment loading. \
No attachment send with e-mails.",
                )

        return msg

    def format_data(self):
        """
        Format data to be sent via e-mail.

        Parameters
        ----------

        Returns
        -------
        formatted_data: string
            formatted data ready to be sent.

        """

        formatted_data = ""
        for line in self.email_content:
            formatted_data += line + "\n"
        return formatted_data

    def send_email(self):
        """
        If IP origin is empty, then send mail with internal server.

        Parameters
        ----------

        Returns
        -------
        None.

        """

        if self.ip_server != "":
            self.smtp_server()
        else:
            self.internal_server()
