# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 12:11:28 2020

@author: Julien
"""
# pylint: disable=R0902

import datetime
import os
import pysftp


class SFTPServer:

    """
    Class to manage all operations done to send file to sftp server.

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
    send_to_sftp_server(tgz_name_):
        Send tgz file to sftp server.
    archival_check():
        Check and remove old tgz files depending on the time to save files.
    check_file_ack(tgz_name_):
        Check if sftp server has tgz file.

    """

    def __init__(self, sftp_server_infos, logging_, is_date_ok_):
        """
        Contructor of the SFTPServer class

        Parameters
        ----------
        sftp_server_infos: dict
            contains all server infos such as ip address, username ...
        logging_: logging object
            object to manage log file
        is_date_ok_: boolean
            True if the last modification date of the file is today, else False

        Return
        ------

        """

        self.logging = logging_
        self.time_to_save = sftp_server_infos["time-to-save"]
        self.ip_sftp = sftp_server_infos["ip"]
        self.user = sftp_server_infos["user"]
        self.pswd = sftp_server_infos["password"]
        self.content = ""
        self.email_content = ""
        self.is_date_ok = is_date_ok_

        # Initialize connection to sftp server
        try:
            self.sftp = pysftp.Connection(
                self.ip_sftp, username=self.user, password=self.pswd
            )
            self.logging.info(
                "Connection established with sftp server @" + self.ip_sftp
            )
            self.content += "| SFTP connection | :white_check_mark: OK |\n"

        except pysftp.ConnectionException:
            self.logging.error(
                "Connection error occured while connecting to sftp server."
            )
            self.content += "| SFTP connection | :exclamation: Error |\n"

        except pysftp.AuthenticationException:
            self.logging.error(
                "Authentication error occured while connecting to sftp server."
            )
            self.content += "| SFTP connection | :exclamation: Error |\n"

        except pysftp.HostKeysException:
            self.logging.error(
                "Loading host keys error occured while connecting to sftp server."
            )
            self.content += "| SFTP connection | :exclamation: Error |\n"

        except pysftp.SSHException:
            self.logging.error("SSH error occured while connecting to sftp server.")
            self.content += "| SFTP connection | :exclamation: Error |\n"

    def send_to_sftp_server(self, tgz_name_):
        """
        Send tgz file to sftp server.

        Parameter
        ---------
        tgz_name_: string
            name of tar.gz file to send to server.

        Return
        ------

        """

        try:
            # upload file to /data/guest/upload on remote
            self.sftp.put(tgz_name_)
            os.remove(tgz_name_)

        except (IOError, OSError) as err:
            if err is OSError:
                self.logging.error("Local path does not exists.")
            else:
                self.logging.error("Remote path does not exists.")
            self.content += "| SFTP connection | :exclamation: Error |\n"

        finally:
            self.sftp.close()

    def archival_check(self):
        """
        Check and remove old tgz files depending on the time to save files.

        Parameters
        ----------

        Return
        ------
        bool:
            True if an error occured, else False.

        """

        try:
            if self.sftp is not None:
                files = self.sftp.listdir(".")
                dead_line = (
                    datetime.datetime.today()
                    - datetime.timedelta(days=self.time_to_save)
                ).date()
                for file in files:
                    date = datetime.datetime.strptime(
                        file.replace(".tgz", ""), "%Y%d%m"
                    ).date()
                    if date < dead_line:
                        self.sftp.remove(file)
                self.content += "| SFTP archival | :white_check_mark: OK |\n"

        except IOError:
            self.logging.error("Remote path does not exist.")
            self.content += "| Archival | :exclamation: Error |\n"
            return True

        finally:
            if not self.is_date_ok:
                self.sftp.close()
        return False

    def check_file_ack(self, tgz_name_):
        """
        Check if sftp server has tgz file.

        Parameters
        ----------
        tgz_name_: string
            tar.gz filename to check ack on sftp server.

        Return
        ------
        bool:
            True if an error occured, else False.
        """

        with pysftp.Connection(
                self.ip_sftp, username=self.user, password=self.pswd
        ) as sftp:
            files = sftp.listdir()
            for file in files:
                if file == tgz_name_:
                    self.logging.info(
                        "Ack : Tar file sent to sftp server "
                        + self.ip_sftp
                        + " on user "
                        + self.user
                    )
                    self.content += "| ACK | :white_check_mark: OK |\n"
                    return True
        self.logging.error("Error occured while getting Ack")
        self.content += "| ACK | :exclamation: Error |\n"
        return False

    def __del__(self):
        """
        Destructor. Close sftp connection if this one is still opened.

        Parameters
        ----------

        """

        if self.sftp is not None:
            self.sftp.close()
