# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 11:37:28 2020

@author: Julien
"""

#pylint: disable=R0902
#pylint: disable=R0915

import io
import zipfile
import datetime
import logging
import os
import json
import urllib3
from urllib3 import exceptions as e
from e_mail import EMail

class ScriptingSystem:

    """
    Class to launch whole program of scripting system.

    Attributes
    ----------
    config: string
        configuration filename
    port: int
        port used to connect to web server
    zfile: Zipfile object
        zip file object to manage zip
    tgz_name: string
        name of tar.gz file
    content: string
        Mattermost notification content
    email_content: string
        email corps content

    Methods
    -------
    get_configuration():
        Get configurations from config file and make sure that values are availables.
    request_zip():
        Make GET HTTP request to get zip file on web server.
    get_date():
        Get last modified date of a specific file (name) and zip (zfile).
    extract_zip():
        Extract zip.
    zip_has_file():
        Check if zip contains dump file.
    compress_to_tgz():
        Compress file to .tgz.

    """


    def __init__(self, port_, config_, log_):
        """
        initialize all variables needed from source to destination.

        Parameters
        ----------

        """

        # File name of the configuration
        self.config = config_

        # Port to connect to web server
        self.port = port_

        # Zip file object
        self.zfile = None

        # YYYYDDMM.tgz
        self.tgz_name = datetime.datetime.now().date().strftime("%Y%d%m") + ".tgz"

        # Email object
        self.email = None

        # Content of Mattermost notification
        self.content = "#### Activity results\n<!channel> please review activity.\n\
| Activity   | Result state |\n|:-----------|:-------------|\n"
        self.email_content = ""

        """ Initialise logging """
        logging.basicConfig(
            # Log file
            filename=log_,
            # This is an error log
            level=logging.ERROR,
            # Log file writting format
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%d/%m/%Y %I:%M:%S %p",
            force=True,
        )

        self.logging = logging

        # Initialize to none all needed variables.
        self.zip_name = None
        self.file_name = None
        self.ip_sftp = None
        self.user = None
        self.pswd = None
        self.time_to_save = None
        self.notification = None
        self.send = None


    def get_configuration(self):
        """
        Get configurations from config file and make sure that values are availables.

        Parameters
        ----------

        Return
        ------
        boolean:
            True if an error occured, else False.

        """
        user_zip = ""
        user_dump = ""
        ip_ = ""
        user_ = ""
        pswd_ = ""
        time_to_save_ = ""
        notification_ = ""

        try:
            # Try reading config file as a serialize data (JSON) to get specific parameters
            with open(self.config, "r") as json_config:
                data = json.load(json_config)
                user_zip = data["zip"]
                user_dump = data["file"]
                ip_ = data["sftp"]["ip"]
                user_ = data["sftp"]["user"]
                pswd_ = data["sftp"]["password"]
                notification_ = data["notification"]
                self.email = EMail(data["email"], logging, )
                send_ = data["send-emails"].lower()
                try:
                    time_to_save_ = int(data["time-to-save"])
                    # Cast to int
                except ValueError:
                    time_to_save_ = 10
                    logging.warning(
                        "Time to save value format is not supported. Default value is 10 days."
                    )
        except EnvironmentError:
            logging.error("Unknow error occured while conf.txt is getting decoded")
            # Add message to log file
            self.content += "| JSON read | :exclamation: Error |\n"
            # Add row to Mattermost notification
            self.email_content += "Error : JSON read.\n"

        if user_dump == "":
            logging.error("File name must not be blank in 'conf.txt'.")
            # Add message to log file
            self.content += "| JSON read | :exclamation: Error |\n"
            # Add row to Mattermost notification
            self.email_content += "Error : DUMP file in JSON must not be blank.\n"

        if user_zip == "":
            logging.error("Zip name must not be blank in 'conf.txt'.")
            self.content += "| JSON read | :exclamation: Error |\n"
            self.email_content += "Error : ZIP file in JSON must not be blank.\n"

        if ip_ == "":
            logging.error("SFTP server IP must not be blank in 'conf.txt'.")
            self.content += "| JSON read | :exclamation: Error |\n"
            self.email_content += "Error : SFTP server IP in JSON must not be blank.\n"

        if user_ == "":
            logging.error("SFTP server user must not be blank in 'conf.txt'.")
            self.content += "| JSON read | :exclamation: Error |\n"
            self.email_content += "Error : SFTP user in JSON must not be blank.\n"

        if pswd_ == "":
            logging.error("SFTP server password must not be blank in 'conf.txt'.")
            self.content += "| JSON read | :exclamation: Error |\n"
            self.email_content += "Error : SFTP password in JSON must not be blank.\n"

        if send_ not in ("yes", "y", "no", "n"):
            send_ = "yes"
            logging.warning("Sending email format not supported. Default value is Yes.")
            self.content += "| JSON read | :exclamation: Error |\n"
            self.email_content += "Warning : Send format in JSON not supported.\n"

        if notification_ not in ("always", "never", "error"):
            notification_ = "always"
            logging.warning(
                "Notifications keyword format not supported. Default value is always."
            )
            self.content += "| JSON read | :exclamation: Error |\n"
            self.email_content += (
                "Warning : Notification format in JSON not supported.\n"
            )

        if user_dump.find(".sql") == -1:
            user_dump = user_dump + ".sql"
        if user_zip.find(".zip") == -1:
            user_zip = user_zip + ".zip"

        self.zip_name = user_zip
        self.file_name = user_dump
        self.ip_sftp = ip_
        self.user = user_
        self.pswd = pswd_
        self.time_to_save = time_to_save_
        self.notification = notification_
        self.send = send_

        if self.content.find("Error") == -1:
            self.content += "| JSON read | :white_check_mark: OK |\n"
            self.email_content += "Info : JSON read OK.\n"
            return True
        return False


    def request_zip(self):
        """
        Make GET HTTP request to get zip file on web server.

        Parameters
        ----------

        Return
        ------
        boolean:
            True, if there was at least one error, else False.

        """

        # Create requester
        http = urllib3.PoolManager()
        req = ""
        try:
            url = "http://localhost:" + str(self.port) + "/" + self.zip_name
            req = http.request("GET", url)
            # Create request type 'GET' to get zip file on http server
            # Error on GET request => file not found
            if req.status == 404:
                raise e.ResponseError()
            self.zfile = zipfile.ZipFile(io.BytesIO(req.data), "r")
            # Decode zip from bytes
            self.content += "| Request zip | :white_check_mark: OK |\n"
            self.email_content += "Info : ZIP request on HTTP OK.\n"
            return False

        except e.HTTPError:
            logging.error("Error 404 : zip file not found %s", url)
            self.content += "| Request zip | :exclamation: Error |\n"
            self.email_content += "Error : ZIP request on HTTP.\n"
            return True


    def get_date(self):
        """
        Get last modified date of a specific file (name) and zip (zfile).

        Parameters
        ----------

        Return
        ------
        date:
            filename last modification date.

        """
        infos = self.zfile.infolist()
        i = 0
        file_date_ = None
        for i in enumerate(infos):
            if infos[i].filename == self.file_name:
                file_date_ = datetime.datetime(*infos[i].date_time[0:3])

        if file_date_ is not None:
            return file_date_.date()
        return None


    def extract_zip(self):
        """
        Extract zip.

        Parameters
        ----------

        Return
        ------
        error: boolean
            True if an error occured, else False.

        """
        error = False

        try:
            self.zfile.extractall()
            logging.info("Zip extracted")
            self.content += "| Extract zip | :white_check_mark: OK |\n"
            self.email_content += "Info : Extracting ZIP OK.\n"

        except zipfile.BadZipFile:
            logging.error("Bad zip file")
            self.content += "| Extract zip | :exclamation: Error |\n"
            self.email_content += "Error : Extracting ZIP.\n"
            error = True

        except zipfile.LargeZipFile:
            logging.error("ZIP file would require ZIP64 functionality but\
that has not been enabled.")
            self.content += "| Extract zip | :exclamation: Error |\n"
            self.email_content += "Error : Extracting ZIP.\n"
            error = True

        finally:
            self.zfile.close()

        return error


    def zip_has_file(self):
        """
        Check if zip contains dump file.

        Parameters
        ----------

        Return
        ------
        boolean:
            True if zip has file, else False.

        """

        for info in self.zfile.infolist():
            if info.filename == self.file_name:
                return True
        logging.critical("%s does not contain %s", self.zip_name, self.file_name)
        return False


    def compress_to_tgz(self):
        """
        Compress file to .tgz.

        Parameters
        ----------

        Return
        ------
        error: boolean
            If an error occured return True, else False.

        """

        error = False

        err = os.system(
            'tar -czf "'
            + os.getcwd()
            + "\\"
            + self.tgz_name
            + '" "'
            + self.file_name
            + '"'
        )
        if err != 0:
            logging.error(
                'Fail to compress (.tgz) "%s" file. TGZ file not created.',
                self.file_name
            )
            self.content += "| Compress zip | :exclamation: Error |\n"
            error = True
        # Delete file name
        if os.path.exists(self.file_name()):
            os.remove(self.file_name)
        return error
