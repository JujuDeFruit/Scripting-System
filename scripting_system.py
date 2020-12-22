# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 11:37:28 2020

@author: Julien
"""

#pylint: disable=R0902
#pylint: disable=R0915

import io
import string
import zipfile
import datetime
import os
import json
import urllib3
from log_email_mattermost import LogEmailMattermost

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


    def __init__(self, port_, config_):
        """
        Initialize all variables needed from source to destination.

        Parameters
        ----------

        """

        # File name of the configuration
        self.config = config_

        # Port to connect to web server
        self.port = port_

        # YYYYDDMM.tgz
        self.tgz_name = datetime.datetime.now().date().strftime("%Y%d%m") + ".tgz"

        # Initialize to none all needed variables.

        # Zip file object
        self.zfile = None
        # Zip name on web server.
        self.zip_name = None
        self.file_name = None
        self.ip_sftp = None
        self.user = None
        self.pswd = None
        self.time_to_save = None
        self.send = None
        self.log_email_matt = None


    def get_configuration(self):
        """
        Get configurations from config file and make sure that values are availables.

        Parameters
        ----------

        Returns
        -------
        None.

        """
        user_zip = None
        user_dump = None
        ip_ = None
        user_ = None
        pswd_ = None
        time_to_save_ = None

        try:
            # Try reading config file as a serialize data (JSON) to get specific parameters
            with open(self.config, "r") as json_config:
                data = json.load(json_config)
                user_zip = data["zip"]
                user_dump = data["file"]
                ip_ = data["sftp"]["ip"]
                user_ = data["sftp"]["user"]
                pswd_ = data["sftp"]["password"]

                # Initialize logging object to manage logs, mattermost notification and e-mails.
                # Set notification value (always, never or error)
                self.log_email_matt = LogEmailMattermost(data['email'], data["notification"])

                try:
                    # Cast to int
                    time_to_save_ = int(data["time-to-save"])

                except ValueError:
                    time_to_save_ = 10
                    self.log_email_matt.warning(
                        "JSON read",
                        "Time to save value format is not supported. Default value is 10 days."
                    )

        except EnvironmentError:
            self.log_email_matt.error("JSON read")

        # Check all entries and log infos.
        if user_dump == "":
            self.log_email_matt.error("JSON read", "File name must not be blank in 'conf.txt'.")

        if user_zip == "":
            self.log_email_matt.error("JSON read", "Zip name must not be blank in 'conf.txt'.")

        if ip_ == "":
            self.log_email_matt.error("JSON read", "SFTP server IP must not be blank in 'conf.txt'.")

        if user_ == "":
            self.log_email_matt.error("JSON read", "SFTP server user must not be blank in 'conf.txt'.")

        if pswd_ == "":
            self.log_email_matt.error("JSON read", "SFTP server password must not be blank in 'conf.txt'.")

        # Add extension if there are not.
        if user_dump.find(".sql") == -1:
            user_dump = user_dump + ".sql"
        if user_zip.find(".zip") == -1:
            user_zip = user_zip + ".zip"

        # Affect all values.
        self.zip_name = user_zip
        self.file_name = user_dump
        self.ip_sftp = ip_
        self.user = user_
        self.pswd = pswd_
        self.time_to_save = time_to_save_

        if not self.log_email_matt.error_nb > 0:
            self.log_email_matt.info('JSON read')


    def request_zip(self):
        """
        Make GET HTTP request to get zip file on web server.

        Parameters
        ----------

        Returns
        -------
        None.

        """

        # Create requester
        http = urllib3.PoolManager()
        req = None

        try:

            # Create request type 'GET' to get zip file on http server
            url = "http://localhost:" + str(self.port) + "/" + self.zip_name
            req = http.request("GET", url)

            # Decode zip from bytes
            self.zfile = zipfile.ZipFile(io.BytesIO(req.data), "r")

            self.log_email_matt.info("Request ZIP")

        except urllib3.exceptions.HTTPError:
            self.log_email_matt.error("Request ZIP", 'HTTP error, check zip file on web server.')

        except urllib3.exceptions.PoolError:
            self.log_email_matt.error("Request ZIP", "Connection error, check your IP destination address.")

        except urllib3.exceptions.ProtocolError:
            self.log_email_matt.error("Request ZIP", "Connection refused, check your IP destination address.")

        except urllib3.exceptions.RequestError:
            self.log_email_matt.error("Request ZIP", "Request error, check your IP destination address.")


        except urllib3.exceptions.TimeoutError:
            self.log_email_matt.error("Request ZIP", 'Max try reach, check destination IP and ZIP file on server.')


    def compare_date(self):
        """
        Get last modified date of file (name) and zip (zfile).

        Parameters
        ----------

        Returns
        -------
        boolean:
            Return if file date is not the same than before - file has been changed today

        """

        if self.zfile is not None:
            return

        infos = self.zfile.infolist()
        i = 0
        file_date = None
        for i in range(len(infos)):
            if infos[i].filename == self.file_name:
                file_date = datetime.datetime(*infos[i].date_time[0:3])

        if file_date is not None:
            same_date = file_date.date() == datetime.datetime.now().date()
            if same_date == True:
                self.log_email_matt.warning("Compare dates", "Modification dates are the same.")
            else:
                self.log_email_matt.info("Compare dates", "Modification dates are differents.")

        return same_date

        return False


    def extract_zip(self):
        """
        Extract zip.

        Parameters
        ----------

        Returns
        -------
        None.

        """

        if self.zfile is None:
            self.log_email_matt.error("ZIP extracted", "ZIP file does not exist.")
            return

        try:
                self.zfile.extractall()
                self.log_email_matt.info("ZIP extracted")

        except zipfile.BadZipFile:
            self.log_email_matt.error("ZIP extracted", "Bad ZIP file. ZIP file not extracted.")

        except zipfile.LargeZipFile:
            self.log_email_matt.error("ZIP extracted", "ZIP file would require ZIP64 functionality but\
that has not been enabled. ZIP file not extracted.")

        finally:
                self.zfile.close()


    def zip_has_file(self):
        """
        Check if zip contains dump file.

        Parameters
        ----------

        Returns
        -------
        boolean:
            True if zip has file, else False.

        """

        if self.zfile is not None:
            for info in self.zfile.infolist():
                if info.filename == self.file_name:
                    self.log_email_matt.info(
                        "ZIP has file",
                        self.zip_name + " contains " + self.file_name
                        )
                    return True
                self.log_email_matt.error(
                    "ZIP has file",
                    self.zip_name + " does not contain " + self.file_name
                    )
        else:
            # Raise all other errors, on the ground program will not process all other operations
            self.log_email_matt.error(
                "ZIP has file",
                self.zip_name + " does not contain " + self.file_name
                )
            self.log_email_matt.error(
                "Compress file",
                'Fail to compress (.tgz) ' + self.file_name + ' file. TGZ file not created.',
                )
            self.log_email_matt.error(
                "SFTP connection",
                "Connection not launch with SFTP server."
                )
            self.log_email_matt.error(
                "SFTP archival",
                "SFTP archival not done."
                )
            self.log_email_matt.error(
                "Send to SFTP",
                "Sending to SFTP server not done."
                )
            self.log_email_matt.error(
                "ACK",
                "Checking ACK not done."
                )
        return False


    def compress_to_tgz(self):
        """
        Compress file to .tgz.

        Parameters
        ----------

        Returns
        -------
        None.

        """

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
            self.log_email_matt.error(
                "Compress file",
                    'Fail to compress (.tgz) ' + self.file_name + ' file. TGZ file not created.',
                )
        # Delete file name
        if os.path.exists(self.file_name):
            os.remove(self.file_name)


    def clean(self, sftp):
        """
        Clean all the folder, by removing everything that has to be removed.

        Parmeters
        ---------
        sftp: sftp object
            client discussing with sftp server.

        Returns
        -------
        None.

        """

        if os.path.exists(self.tgz_name):
            os.remove(self.tgz_name)
        if os.path.exists(self.file_name):
            os.remove(self.file_name)

        sftp.close()