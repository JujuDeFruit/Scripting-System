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
    log_email_matt: LogEmailMattermost
        Object to manage all logs.
    time_to_save: int
        Time in days to store data on server.
    ip_sftp: string
        IP of SFTP server.
    user: string
        Username of user to connect.
    pswd: string
        Password to connect to user.
    is_date_ok: boolean
        Comparison of last modification date of dump file and today.

    Methods
    -------
    connect(action):
        Connect to sftp server with ssh keys.
    send_to_sftp_server(tgz_name_):
        Send tgz file to sftp server.
    archival_check():
        Check and remove old tgz files depending on the time to save files.
    check_file_ack(tgz_name_):
        Check if sftp server has tgz file.
    close():
        Close sftp connection if this one is still opened.

    """

    def __init__(self, sftp_server_infos, logging, is_date_ok):
        """
        Contructor of the SFTPServer class

        Parameters
        ----------
        sftp_server_infos: dict
            contains all server infos such as ip address, username ...
        logging: logging object
            object to manage logs
        is_date_ok: boolean
            True if the last modification date of the file is today, else False

        Returns
        -------
        None.

        """

        self.log_email_matt = logging
        self.time_to_save = sftp_server_infos["time-to-save"]
        self.ip_sftp = sftp_server_infos["ip"]
        self.user = sftp_server_infos["user"]
        self.pswd = sftp_server_infos["password"]
        self.is_date_ok = is_date_ok

        self.sftp = None
        self.sftp = self.connect("SFTP connection")

    def connect(self, action):
        """
        Connect to sftp server by managing ssh keys.

        Parameters
        ----------
        action: string
            Current action written in logs (ACK or auth)

        Returns
        -------
        Sftp server object.

        """

        cnopts = None
        try:
            cnopts = pysftp.CnOpts(knownhosts=pysftp.known_hosts())

        except IOError:
            # Cannot find known_hosts at standard place
            self.log_email_matt.error(
                "SFTP connection",
                "Please be sure known_hosts file is under user/.ssh folder."
                )

        host_keys = None
        if cnopts is not None:
            if cnopts.hostkeys.lookup(self.ip_sftp) is None:
                # Load current known keys.
                host_keys = cnopts.hostkeys
                # Set parameter to accept connection
                cnopts.hostkeys = None

        # Initialize connection to sftp server
        try:
            sftp = pysftp.Connection(
                self.ip_sftp, username=self.user, password=self.pswd, cnopts=cnopts
            )

            # If a new host key has been detected add this one to known_hosts
            if host_keys != None:
                host_keys.add(self.ip_sftp, sftp.remote_server_key.get_name(), sftp.remote_server_key)
                host_keys.save(pysftp.known_hosts())

            self.log_email_matt.info(
                action,
                "Connection established with sftp server @" + self.ip_sftp,
            )
            return sftp

        except pysftp.ConnectionException:
            self.log_email_matt.error(
                action,
                "Connection error occured."
                )

        except pysftp.AuthenticationException:
            self.log_email_matt.error(
                action,
                "Authentication error occured."
            )

        except pysftp.HostKeysException:
            self.log_email_matt.error(
                action,
                "Loading host keys error occured."
            )

        except pysftp.SSHException:
            self.log_email_matt.error(
                action,
                "Unknow SSH error occured."
                )


    def send_to_sftp_server(self, tgz_name_):
        """
        Send tgz file to sftp server.

        Parameter
        ---------
        tgz_name_: string
            name of tar.gz file to send to server.

        Returns
        -------
        None.

        """

        try:
            if self.sftp is not None:
                # upload file to /data/guest/upload on remote
                with self.sftp.cd("TSE-INFORX"):
                    self.sftp.put(tgz_name_)
                os.remove(tgz_name_)
    
                self.log_email_matt.info("Send to SFTP")

        except (IOError, OSError) as err:
            if err is OSError:
                path = "Local"
            else:
                path = "Remote"
            self.log_email_matt.error("Send to SFTP", path + " path does not exists.")

        finally:
            if self.sftp is not None:
                self.close()

    def archival_check(self):
        """
        Check and remove old tgz files depending on the time to save files.

        Parameters
        ----------

        Returns
        -------
        None.

        """

        try:
            if self.sftp is not None:
                # Current directory.
                files = self.sftp.listdir("TSE-INFORX")
                dead_line = (
                    datetime.datetime.today()
                    - datetime.timedelta(days=self.time_to_save)
                ).date()
                for file in files:
                    try:
                        date = datetime.datetime.strptime(
                            file.replace(".tgz", ""), "%Y%d%m"
                            ).date()
                        if date < dead_line:
                            self.sftp.remove(file)
                        self.log_email_matt.info("SFTP archival")

                    except ValueError:
                        pass

            else:
                self.log_email_matt.error(
                    "SFTP archival", "Connection to sftp is not done."
                )
                self.log_email_matt.error(
                    "Send to SFTP", "Sending to SFTP server not done."
                )
                self.log_email_matt.error("ACK", "Checking ACK not done.")

        except IOError:
            self.log_email_matt.error("SFTP archival", "Remote path does not exist.")

        finally:
            if not self.is_date_ok and self.sftp is not None:
                self.log_email_matt.warning(
                    "Send to SFTP", 
                    "Sending to SFTP server not done because dates do not correspond."
                )
                self.log_email_matt.warning(
                    "ACK",
                    "Checking ACK not done because dates do not correspond."
                    )
                self.close()

    def check_file_ack(self, tgz_name_):
        """
        Check if sftp server has tgz file.

        Parameters
        ----------
        tgz_name_: string
            tar.gz filename to check ack on sftp server.

        Returns
        -------
        None.

        """

        sftp = None
        try:
            sftp = self.connect("ACK")
            with sftp.cd("TSE-INFORX"):
                files = sftp.listdir()
                for file in files:
                    if file == tgz_name_:
                        self.log_email_matt.info("ACK", "Tar file sent to sftp server.")
                        return
            self.log_email_matt.error("ACK", "Tar file is not on server.")
            sftp.close()

        except pysftp.ConnectionException:
            self.log_email_matt.error("ACK" "Connection error occured.")

        except pysftp.AuthenticationException:
            self.log_email_matt.error(
                "ACK", "Authentication error occured."
            )

        except pysftp.HostKeysException:
            self.log_email_matt.error(
                "ACK", "Loading host keys error occured."
            )

        except pysftp.SSHException:
            self.log_email_matt.error(
                "ACK",
                "Unknow SSH error occured."
                )

        except IOError:
            self.log_email_matt.error(
                "ACK",
                "Remote path does not exists."
                )

        finally:
            if sftp is not None:
                sftp.close()

    def close(self):
        """
        Close sftp connection if this one is still opened.

        Parameters
        ----------

        Returns
        -------
        None.

        """

        if self.sftp is not None:
            self.sftp.close()
