"""
    --- Main ---

    @author Julien Raynal

"""

import zipfile
import shutil
import tarfile
import gzip
import urllib3
from urllib3 import exceptions as e
import io
import datetime
import logging
import os
from pathlib import Path

PORT = 8000;
config = "conf.txt";
log = "log.log";

"""
    Get configurations from config file
"""
def getConfig():
    content = "";
    try:
        with open(config) as file:
            content = file.read().splitlines();
        logging.info("Config file read.");
    except FileNotFoundError:
        logging.error("Config file not found");
        raise FileNotFoundError();
    except IOError:
        logging.error('Error occured while reading \'conf.txt\'');
        raise IOError();
    except Exception:
        logging.error("Unknown exception");
        raise Exception();
    
    USER_ZIP = "";
    USER_DUMP = "";
    
    for line in content:
        if line.startswith("zip:"):
            USER_ZIP = line.replace('zip:', '');
        if line.startswith("file:"):
            USER_DUMP = line.replace('file:', '');
    
    if (USER_DUMP == "" or USER_ZIP == ""):
        logging.error('File and zip must not be blank in \'conf.txt\'');
        raise Exception();
    
    return (USER_ZIP + '.zip', USER_DUMP + '.sql');

"""
    Make GET HTTP request to get zip file on web server
"""
def requestZip(USER_INP_):
    http = urllib3.PoolManager();
    req = "";
    try:
        url = 'http://localhost:' + str(PORT) + '/' + USER_INP_;
        req = http.request('GET', url);
        if req.status == 404: 
            raise e.ResponseError();
        return req;
    except e.ResponseError:
        logging.error("Error 404 : zip file not found " + url);
        raise e.ResponseError();
    except Exception:
        logging.error("Unknown error while requesting zip on localhost");
        raise Exception();

"""
    Get last modified date of a specific file (name) and zip (zf_)
"""
def getDate(zf_, name):
    infos = zf_.infolist();
    i = 0;
    fileDate_ = "";
    for i in range(len(infos)):
        if infos[i].filename == name:
            fileDate_ = datetime.datetime(*infos[i].date_time[0:3]);
    if fileDate_ == "" :
        logging.error("Unknown exception while reading date of " + name + ' file');
        raise Exception();
    return fileDate_.date();

"""
    Extract zip
"""
def extractZip(zf_):
    zf_.extractall();
    zf_.close();
    logging.info("Zip extracted");
    
"""
    Check if file zip contains file
"""
def zipHasFile(z, name):
    for info in z.infolist():
        if info.filename == name:
            return True;
    return False;

"""
    Compress file to .tgz
"""
def compressToTgz(fileName_, tarName_):
    try:
        err = os.system("tar -czf \"" + os.getcwd() + "\\" + tarName_ + "\" \"" + fileName_ + "\"");
        if err != 0:
            raise Exception();
        os.remove(fileName_);
    except Exception:
        logging.error("Fail to compress (.tgz) " + "\"" + fileName_ + "\" file. TGZ file not created.")
        raise Exception();
    """try:
        tar_ = tarfile.open(name = tarName_, mode = 'w:gz');
        tar_.addfile(tar_.gettarinfo(name = fileName_));
        tar_.close();
        return tar_;
    except tarfile.CompressionError:
        logging.error("Compression to .tar.gz error");
        raise tarfile.CompressionError();
    except Exception:
        logging.error("Unknown error while compressing to .tgz");
        raise Exception();"""

def main() : 
    
    """ Initialise logging """
    logging.basicConfig(filename = log, 
                        level = logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%d/%m/%Y %I:%M:%S %p', 
                        force = True)
    
    (zipName, fileName) = getConfig();
        
    req = requestZip(zipName);

    zf = zipfile.ZipFile(io.BytesIO(req.data), 'r');            #Decode zip from bytes
    
    """
        Return exception if zip does not contain specific file
    """
    if not zipHasFile(zf, fileName):
        logging.error(zipName + " does not contain " + fileName);
        raise FileNotFoundError();
    
    extractZip(zf);

    if getDate(zf, fileName) == datetime.datetime.now().date():
        logging.warning("The file has the same date than now")
    
    tarName = datetime.datetime.now().date().strftime('%Y%d%m') + ".tgz";
    compressToTgz(fileName, tarName);
    
    logging.info("Done");

if __name__ == "__main__":
    main();