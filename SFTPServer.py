# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 12:11:28 2020

@author: Julien
"""
import datetime;
import os;
import pysftp;

class SFTPServer():
    
    """
        Contructor of the SFTPServer class
    """
    def __init__(self, sftpServerInfos, logging_, isDateOK_):
        self.logging = logging_;
        self.timeToSave = sftpServerInfos['timeToSave'];
        self.ip = sftpServerInfos['ip'];
        self.user = sftpServerInfos['user'];
        self.pswd = sftpServerInfos['password'];
        self.content = "";
        self.emailContent = "";
        self.isDateOK = isDateOK_;
        
        try:
            self.sftp = pysftp.Connection(self.ip, username = self.user, password = self.pswd);
            self.logging.info("Connection established with sftp server @" + self.ip);
            self.content += "| SFTP connection | :white_check_mark: OK |\n";
        except Exception:
            self.logging.error("Unknown error occured while connecting to sftp server");
            self.content += "| SFTP connection | :exclamation: Error |\n";
        
    """
        Initialize connection to sftp server and send tgz file 
    """
    def sendToSftpServer(self, tgzName_):
        try:
            # upload file to /data/guest/upload on remote
            self.sftp.put(tgzName_)              
            os.remove(tgzName_);
        except Exception:
            self.logging.error("Unknown error occured while sending tgz file to sftp server");
            self.content += "| SFTP connection | :exclamation: Error |\n";
        finally:
            self.sftp.close();
                
    """
        Check and remove old tgz files depending on the time to save files
    """
    def archivalCheck(self):
        try:
            files = self.sftp.listdir('.');
            deadLine = (datetime.datetime.today() - datetime.timedelta(days = self.timeToSave)).date();
            for file in files:
                date = datetime.datetime.strptime(file.replace('.tgz', ''), '%Y%d%m').date();
                if date < deadLine:
                    self.sftp.remove(file);
            self.content += "| SFTP archival | :white_check_mark: OK |\n";
        except Exception:
            self.logging.error("Remote path does not exist in archval function.");
            self.content += "| Archival | :exclamation: Error |\n";
            return True;
        finally:
            if not self.isDateOK:
                self.sftp.close();
        return False;
            
    """
        Check if sftp server has tgz file
    """
    def checkFileAck(self, tgzName_):
        with pysftp.Connection(self.ip, username = self.user, password = self.pswd) as sftp:
            files = sftp.listdir();
            for file in files:
                if file == tgzName_:
                    self.logging.info("Ack : Tar file sent to sftp server " + self.ip + " on user " + self.user);
                    self.content += "| ACK | :white_check_mark: OK |\n";
                    return True;
        self.logging.error("Error occured while getting Ack");
        self.content += "| ACK | :exclamation: Error |\n";
        return False;