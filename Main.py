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
import os, sys
import json
#import EMail
import Mattermost
import SFTPServer
import traceback

class ScriptingSystem():   

    """
        Constructor : initialize all variables needed from source to destination
    """
    def __init__(self, port_, config_, log_ ):
        self.PORT = port_;
        self.config = config_;
        self.log = log_;
        self.tgzName = datetime.datetime.now().date().strftime('%Y%d%m') + ".tgz";
        self.content = "#### Activity results\n<!channel> please review activity.\n| Activity   | Result state |\n|:-----------|:-------------|\n";
        
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
        pswd_ = "";
        timeToSave_ = "";
        notification_ = "";
        try:
            with open(self.config, 'r') as json_config:
                data = json.load(json_config);
                USER_ZIP = data['zip'];
                USER_DUMP = data['file'];
                ip_ = data['sftp']['ip'];
                user_ = data['sftp']['user'];
                pswd_ = data['sftp']['password'];
                notification_ = data['notification'];
                try:
                    timeToSave_ = int(data['time-to-save']);
                except ValueError:
                    timeToSave_ = 10;
                    logging.warning("Time to save value format is not supported. Default value is 10 days.");
        except Exception:
            logging.error("Unknow error occured while conf.txt is getting decoded");
            self.content += "| JSON read | :exclamation: Error |\n";
            #raise Exception();
        
        if USER_DUMP == "": 
            logging.error('File name must not be blank in \'conf.txt\'.');
            self.content += "| JSON read | :exclamation: Error |\n";
            #raise Exception();
        if USER_ZIP == "":
            logging.error('Zip name must not be blank in \'conf.txt\'.');
            self.content += "| JSON read | :exclamation: Error |\n";
            #raise Exception();
        if ip_ == "":
            logging.error('SFTP server ip must not be blank in \'conf.txt\'.');
            self.content += "| JSON read | :exclamation: Error |\n";
            #raise Exception();
        if user_ == "":
            logging.error('SFTP server user must not be blank in \'conf.txt\'.');
            self.content += "| JSON read | :exclamation: Error |\n";
            #raise Exception();
        if pswd_ == "":
            logging.error('SFTP server password must not be blank in \'conf.txt\'.');
            self.content += "| JSON read | :exclamation: Error |\n";
            #raise Exception();
        if notification_ != "always" and notification_ != "never" and notification_ != "error":
            notification_ = "always";
            logging.warning('Notifications keyword format not supported. Default value is always.');
            self.content += "| JSON read | :exclamation: Error |\n";
            
        if USER_DUMP.find('.sql') == -1:
            USER_DUMP = USER_DUMP + '.sql';
        if USER_ZIP.find('.zip') == -1:
            USER_ZIP = USER_ZIP + '.zip';
            
                
        #self.mail = EMail(data['email']);
        self.zipName = USER_ZIP;
        self.fileName = USER_DUMP; 
        self.ip = ip_;
        self.user = user_;
        self.pswd = pswd_;
        self.timeToSave = timeToSave_;
        self.notification = notification_;
        
        self.content += "| JSON read | :white_check_mark: OK |\n";

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
            self.content += "| Request zip | :white_check_mark: OK |\n";
        except e.ResponseError:
            logging.error("Error 404 : zip file not found " + url);
            self.content += "| Request zip | :exclamation: Error |\n";
            #raise e.ResponseError();
        except Exception:
            logging.error("Unknown error while requesting zip on localhost");
            self.content += "| Request zip | :exclamation: Error |\n";
            #raise Exception();
    
    """
        Get last modified date of a specific file (name) and zip (zf_)
    """
    def getDate(self):
        self.zipHasFile();
        infos = self.zf.infolist();
        i = 0;
        fileDate_ = "";
        for i in range(len(infos)):
            if infos[i].filename == self.fileName:
                fileDate_ = datetime.datetime(*infos[i].date_time[0:3]);
        return fileDate_.date();
    
    """
        Extract zip
    """
    def extractZip(self):
        try:
            self.zf.extractall();
            logging.info("Zip extracted");
            self.content += "| Extract zip | :white_check_mark: OK |\n";
        except Exception:
            logging.error("Error occured while zip get extracted");
            self.content += "| Extract zip | :exclamation: Error |\n";
            #raise Exception();
        finally:
            self.zf.close();
        
    """
        Check if file zip contains file
    """
    def zipHasFile(self):      
        for info in self.zf.infolist():
            if info.filename == self.fileName:
                return;
        logging.error(self.zipName + " does not contain " + self.fileName);
        #raise FileNotFoundError();
    
    """
        Compress file to .tgz
    """
    def compressToTgz(self):
        try:
            err = os.system("tar -czf \"" + os.getcwd() + "\\" + self.tgzName + "\" \"" + self.fileName + "\"");
            if err != 0:
                raise Exception();
            self.content += "| Compress zip | :white_check_mark: OK |\n";
            os.remove(self.fileName);
        except Exception:
            logging.error("Fail to compress (.tgz) " + "\"" + self.fileName + "\" file. TGZ file not created.");
            self.content += "| Compress zip | :exclamation: OK |\n";
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
        logging.warning("The file has the same date than now.");
    else:
        script.compressToTgz();
        
        """
            SFTP server area
        """
        sftpOptions = {"ip": script.ip, 
                       "user": script.user, 
                       "password": script.pswd, 
                       "timeToSave": script.timeToSave };
        
        sftp = SFTPServer.SFTPServer(sftpOptions, script.content, logging);
        sftp.sendToSftpServer(script.tgzName);
        
        payload = { 
            "icon_url": "https://www.mattermost.org/wp-content/uploads/2016/04/icon.png",
            "text": sftp.content 
            };
        
        #TODO - récupérer si des erreurs ont été commises
        if script.notification == "always" or (script.notification == "error" and error == True):
            with open("test.txt", "w") as t:
                t.write(sftp.content);
            #Mattermost.sendMattermostNotification(payload, logging);
        
        if os.path.exists(script.tgzName):
            os.remove(script.tgzName);

if __name__ == "__main__":
    main();