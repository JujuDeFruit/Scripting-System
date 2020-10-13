"""
    --- Main ---

    @author Julien Raynal

"""

import zipfile
import urllib3
from urllib3 import exceptions as e
import io
import datetime
import logging
import os
import pysftp
import json

class ScriptingSystem():   

    """
        Constructor : initialize all variables needed from source to destination
    """
    def __init__(self, port_, config_, log_ ):
        self.PORT = port_;
        self.config = config_;
        self.log = log_;
        self.zipName = "";
        self.fileName = "";
        self.tgzName = datetime.datetime.now().date().strftime('%Y%d%m') + ".tgz";
        """ Initialise logging """
        logging.basicConfig(filename = self.log, 
                        level = logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%d/%m/%Y %I:%M:%S %p', 
                        force = True);

    """
        Get configurations from config file
    """
    def getConfig(self):
        USER_ZIP = "";
        USER_DUMP = "";
        ip_ = "";
        user_ = "";
        pswd_= "";
        try:
            with open(self.config, 'r') as json_config:
                data = json.load(json_config);
                USER_ZIP = data['zip'];
                USER_DUMP = data['file'];
                ip_ = data['sftp']['ip'];
                user_ = data['sftp']['user'];
                pswd_ = data['sftp']['password'];
        except json.JSONDecodeError:
            logging.error("Error occured while conf.txt is getting decoded");
            raise json.JSONDecodeError();
        except Exception:
            logging.error("Unknow error occured while conf.txt is getting decoded")
            raise Exception();
        
        if USER_DUMP == "": 
            logging.error('File name must not be blank in \'conf.txt\'');
            raise Exception();
        if USER_ZIP == "":
            logging.error('Zip name must not be blank in \'conf.txt\'');
            raise Exception();
        if ip_ == "":
            logging.error('SFTP server ip must not be blank in \'conf.txt\'');
            raise Exception();
        if user_ == "":
            logging.error('SFTP server user must not be blank in \'conf.txt\'');
            raise Exception();
        if pswd_ == "":
            logging.error('SFTP server password must not be blank in \'conf.txt\'');
            raise Exception();
            
        if USER_DUMP.find('.sql') == -1:
            USER_DUMP = USER_DUMP + '.sql';
        if USER_ZIP.find('.zip') == -1:
            USER_ZIP = USER_ZIP + '.zip';
            
        self.zipName = USER_ZIP;
        self.fileName = USER_DUMP; 
        self.ip = ip_;
        self.user = user_;
        self.pswd = pswd_;

    """
        Make GET HTTP request to get zip file on web server
    """
    def requestZip(self):
        http = urllib3.PoolManager();
        req = "";
        try:
            url = 'http://localhost:' + str(self.PORT) + '/' + self.zipName;
            req = http.request('GET', url);
            if req.status == 404: 
                raise e.ResponseError();
            self.zf = zipfile.ZipFile(io.BytesIO(req.data), 'r');            # Decode zip from bytes
        except e.ResponseError:
            logging.error("Error 404 : zip file not found " + url);
            raise e.ResponseError();
        except Exception:
            logging.error("Unknown error while requesting zip on localhost");
            raise Exception();
    
    """
        Get last modified date of a specific file (name) and zip (zf_)
    """
    def getDate(self):
        infos = self.zf.infolist();
        i = 0;
        fileDate_ = "";
        for i in range(len(infos)):
            if infos[i].filename == self.fileName:
                fileDate_ = datetime.datetime(*infos[i].date_time[0:3]);
        if fileDate_ == "" :
            logging.error("Unknown exception while reading date of " + self.fileName + ' file');
            raise Exception();
        return fileDate_.date();
    
    """
        Extract zip
    """
    def extractZip(self):
        try:
            self.zf.extractall();
            self.zf.close();
            logging.info("Zip extracted");
        except Exception:
            logging.error("Error occured while zip get extracted");
            raise Exception();
        
    """
        Check if file zip contains file
    """
    def zipHasFile(self):      
        for info in self.zf.infolist():
            if info.filename == self.fileName:
                return;
        logging.error(self.zipName + " does not contain " + self.fileName);
        raise FileNotFoundError();
    
    """
        Compress file to .tgz
    """
    def compressToTgz(self):
        try:
            err = os.system("tar -czf \"" + os.getcwd() + "\\" + self.tgzName + "\" \"" + self.fileName + "\"");
            if err != 0:
                raise Exception();
            os.remove(self.fileName);
        except Exception:
            logging.error("Fail to compress (.tgz) " + "\"" + self.fileName + "\" file. TGZ file not created.")
            raise Exception();
    
    """
        Initialize connection to sftp server and send tgz file 
    """
    def sendToSftpServer(self):
        try:
            with pysftp.Connection(self.ip, username = self.user, password = self.pswd) as sftp:
                sftp.put(self.tgzName)              # upload file /data/guest/upload on remote
            logging.info("Tar file sent to sftp server " + self.ip + " on user " + self.user);
            os.remove(self.tgzName);
        except IOError:
            logging.error("Remote path does not exist");
            raise IOError();
        except OSError:
            logging.error("Local path does not exist");
            raise OSError();
        except Exception:
            logging.error("Unknown error occured while sending tgz file to sftp server");
            raise Exception();
    
    """
        Check if sftp server has tgz file
    """
    def checkFileAck(self):
        with pysftp.Connection(self.ip, username = self.user, password = self.pswd) as sftp:
            files = sftp.listdir();
            for file in files:
                if file == self.tgzName:
                    logging.info("Ack");
                    return;
        logging.error("Error occured while getting Ack");
        raise Exception();

"""
    Main
"""
def main() : 
    
    script = ScriptingSystem(8000, "conf.txt", "log.log");
     
    script.getConfig();
    
    script.requestZip();
    
    script.extractZip();

    if script.getDate() == datetime.datetime.now().date():
        logging.warning("The file has the same date than now");
        raise Exception();
    else:
        script.compressToTgz();
        script.sendToSftpServer();
        script.checkFileAck();    

if __name__ == "__main__":
    main();