"""
    --- Main ---

    @author Julien Raynal

"""

from tkinter import *
import zipfile
import requests
import urllib3
from urllib3 import exceptions as e
import io
import datetime

PORT = 8000;

def askUserZipName():
    master = Tk();
    master.withdraw();
    USER_INP = ""
    while USER_INP == "":
        USER_INP = simpledialog.askstring(title="Test", prompt="File zip name :");
    return USER_INP;

def requestZip(USER_INP_):
    http = urllib3.PoolManager();
    req = "";
    try:
        url = 'http://localhost:' + str(PORT) + '/' + USER_INP_ + '.zip';
        req = http.request('GET', url);
        if req.status == 404: 
            raise e.ResponseError();
        return req;
    except e.ResponseError:
        print("Response error");
        raise e.ResponseError();
    except Exception:
        print("Exception");
        raise Exception();

def getDateFromZip(zf_):
    zipDateTuple_ = zf_.infolist()[0].date_time;          #Get date in a tuple
    zipDate_ = datetime.datetime(*zipDateTuple_[0:6]);    #Convert to date time
    return zipDate_;

def main() : 
    
    USER_INP = askUserZipName();
        
    req = requestZip(USER_INP);

    zf = zipfile.ZipFile(io.BytesIO(req.data), 'r');    #Decode zip from bytes
    zipDate = getDateFromZip(zf);
    print(zipDate);

if __name__ == "__main__":
    main();