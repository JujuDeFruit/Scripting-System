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
import json
import EMail
import Mattermost
import SFTPServer

class ScriptingSystem():   

    """
        Constructor : initialize all variables needed from source to destination
    """
    def __init__(self, port_, config_, log_ ):
        self.PORT = port_;                                                          # Port to connect to web server
        self.config = config_;                                                      # File name of the configuration
        self.tgzName = datetime.datetime.now().date().strftime('%Y%d%m') + ".tgz";  # YYYYDDMM.tgz
        # Content of Mattermost notification
        self.content = "#### Activity results\n<!channel> please review activity.\n| Activity   | Result state |\n|:-----------|:-------------|\n";
        self.mailContent = ""
        
        """ Initialise logging """
        logging.basicConfig(filename = log_,                                    # Log file
                        level = logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',     # Log file writting format
                        datefmt='%d/%m/%Y %I:%M:%S %p', 
                        force = True);

    """
        Get configurations from config file and make sure that values are availables
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
            # Try reading config file as a serialize data (JSON) to get specific parameters
            with open(self.config, 'r') as json_config:
                data = json.load(json_config);
                USER_ZIP = data['zip'];
                USER_DUMP = data['file'];
                ip_ = data['sftp']['ip'];
                user_ = data['sftp']['user'];
                pswd_ = data['sftp']['password'];
                notification_ = data['notification'];
                self.email = EMail(data['email'], logging);
                send_ = data['send-emails'].lower();
                try:
                    timeToSave_ = int(data['time-to-save']);        # Cast to int
                except ValueError:
                    timeToSave_ = 10;
                    logging.warning("Time to save value format is not supported. Default value is 10 days.");
        except Exception:
            logging.error("Unknow error occured while conf.txt is getting decoded");    # Add message to log file
            self.content += "| JSON read | :exclamation: Error |\n";                    # Add row to Mattermost notification
            self.mailContent += "Error : JSON read.\n";
        
        if USER_DUMP == "": 
            logging.error('File name must not be blank in \'conf.txt\'.');              # Add message to log file
            self.content += "| JSON read | :exclamation: Error |\n";                    # Add row to Mattermost notification
            self.mailContent += "Error : DUMP file in JSON must not be blank.\n";
                    
        if USER_ZIP == "":
            logging.error('Zip name must not be blank in \'conf.txt\'.');
            self.content += "| JSON read | :exclamation: Error |\n";
            self.mailContent += "Error : ZIP file in JSON must not be blank.\n";
            
        if ip_ == "":
            logging.error('SFTP server IP must not be blank in \'conf.txt\'.');
            self.content += "| JSON read | :exclamation: Error |\n";
            self.mailContent += "Error : SFTP server IP in JSON must not be blank.\n";
            
        if user_ == "":
            logging.error('SFTP server user must not be blank in \'conf.txt\'.');
            self.content += "| JSON read | :exclamation: Error |\n";
            self.mailContent += "Error : SFTP user in JSON must not be blank.\n";
            
        if pswd_ == "":
            logging.error('SFTP server password must not be blank in \'conf.txt\'.');
            self.content += "| JSON read | :exclamation: Error |\n";
            self.mailContent += "Error : SFTP password in JSON must not be blank.\n";
            
        if send_ != "yes" and send_ != "y" and send_ != "no" and send_ != "n":
            send_ = "yes";
            logging.warning('Sending email format not supported. Default value is Yes.');
            self.content += "| JSON read | :exclamation: Error |\n";
            self.mailContent += "Warning : Send format in JSON not supported.\n";
            
        if notification_ != "always" and notification_ != "never" and notification_ != "error":
            notification_ = "always";
            logging.warning('Notifications keyword format not supported. Default value is always.');
            self.content += "| JSON read | :exclamation: Error |\n";
            self.mailContent += "Warning : Notification format in JSON not supported.\n";
            
        if USER_DUMP.find('.sql') == -1:
            USER_DUMP = USER_DUMP + '.sql';
        if USER_ZIP.find('.zip') == -1:
            USER_ZIP = USER_ZIP + '.zip';
            
        
        self.zipName = USER_ZIP;
        self.fileName = USER_DUMP; 
        self.ip = ip_;
        self.user = user_;
        self.pswd = pswd_;
        self.timeToSave = timeToSave_;
        self.notification = notification_;
        self.send = send_;
        
        if self.content.find('Error') == -1:
            self.content += "| JSON read | :white_check_mark: OK |\n";
            self.mailContent += "Info : JSON read OK.\n";
            return True;
        return False;

    """
        Make GET HTTP request to get zip file on web server
    """
    def requestZip(self):
        # Create requester
        http = urllib3.PoolManager();
        req = "";
        try:
            url = 'http://localhost:' + str(self.PORT) + '/' + self.zipName;            
            req = http.request('GET', url);     # Create request type 'GET' to get zip file on http server
            if req.status == 404:               # Error on GET request => file not found
                raise e.ResponseError();
            self.zf = zipfile.ZipFile(io.BytesIO(req.data), 'r');            # Decode zip from bytes
            self.content += "| Request zip | :white_check_mark: OK |\n";
            self.mailContent += "Info : ZIP request on HTTP OK.\n";
            return False;
        
        except e.ResponseError:
            logging.error("Error 404 : zip file not found " + url);
            self.content += "| Request zip | :exclamation: Error |\n";
            self.mailContent += "Error : ZIP request on HTTP.\n";
            return True;
        
        except Exception:
            logging.error("Unknown error while requesting zip on localhost");
            self.content += "| Request zip | :exclamation: Error |\n";
            self.mailContent += "Error : ZIP request on HTTP.\n";
            return True;
        
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
        return fileDate_.date();
    
    """
        Extract zip
    """
    def extractZip(self):
        error = False;
        try:
            self.zf.extractall();
            logging.info("Zip extracted");
            self.content += "| Extract zip | :white_check_mark: OK |\n";
            self.mailContent += "Info : Extracting ZIP OK.\n";
            
        except Exception:
            logging.error("Error occured while zip get extracted");
            self.content += "| Extract zip | :exclamation: Error |\n";
            self.mailContent += "Error : Extracting ZIP.\n";
            error = True;
            
        finally:
            self.zf.close();
            
        return error;
        
    """
        Check if file zip contains file
    """
    def zipHasFile(self):      
        for info in self.zf.infolist():
            if info.filename == self.fileName:                
                return True;
        logging.critical(self.zipName + " does not contain " + self.fileName);
        return False;
    
    """
        Compress file to .tgz
    """
    def compressToTgz(self):
        error = False;
        try:
            err = os.system("tar -czf \"" + os.getcwd() + "\\" + self.tgzName + "\" \"" + self.fileName + "\"");
            if err != 0:
                raise Exception();
            os.remove(self.fileName);   # Delete file name 
            
        except Exception:
            logging.error("Fail to compress (.tgz) " + "\"" + self.fileName + "\" file. TGZ file not created.");
            self.content += "| Compress zip | :exclamation: Error |\n";
            error = True;
        return error;

"""
    Main
"""
def main() : 
    
    error = False;
    
    script = ScriptingSystem(8000, "conf.txt", "log.log");
     
    error = script.getConfig();
    
    if not error:
        error = script.requestZip();
    
    if not error:
        error = script.extractZip();
    
    mattermost = Mattermost(script.content, logging);
    
    if not script.zipHasFile():
        mattermost.payload['text'] += "| Zip matches file | :exclamation: Error |\n";
    else :    
        mattermost.payload['text'] += "| Zip matches file | :white_check_mark: OK |\n";
        
        if not error: 
            error = script.compressToTgz();
        
        # File date is not the same than before - file has been changed today
        isDateOK = script.getDate() == datetime.datetime.now().date();
        
        """
            SFTP server area
        """
        sftpOptions = {"ip": script.ip, 
                       "user": script.user, 
                       "password": script.pswd, 
                       "timeToSave": script.timeToSave };
        
        sftp = SFTPServer.SFTPServer(sftpOptions, isDateOK);
        error = sftp.archivalCheck();
        
        if isDateOK and not error:
            sftp.sendToSftpServer(script.tgzName);
            sftp.checkFileAck(script.tgzName);
        mattermost.payload['text'] += sftp.content;
        
        
    """
        Mattermost notification area
    """
    if mattermost.payload['text'].find("Error") != -1:
        error = True;
    
    if script.notification == "always" or (script.notification == "error" and error):
        with open("test.txt", "w") as t:
            t.write(mattermost.payload['text']);
            #Mattermost.sendMattermostNotification(payload, logging);
        
    if script.send == "yes" or script.send == "y":
        script.email.send();
        
    logging.info("Done");

if __name__ == "__main__":
    main();