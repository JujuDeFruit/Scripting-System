# -*- coding: utf-8 -*-
"""
    -- Web Server --

    @author : Julien Raynal 

"""

import http.server
import socketserver
import os
import threading
import psutil
import atexit

PORT = 8000;

def launch():
    handler_object = http.server.SimpleHTTPRequestHandler;
    try:
        myServer = socketserver.TCPServer(("", PORT), handler_object);
        print("http://localhost:" + str(PORT) + " | OK");
        myServer.serve_forever();
    except Exception:
        print("Error launching server web !");
        raise Exception();
        
def launchWebServerAsAService():
    download_thread = threading.Thread(target=launch, name="launcher");
    download_thread.start(); # Launch web server as a service.
    os.system("python3 -m http.server " + str(PORT));
    
def stopWebServer():
    pidList = psutil.net_connections();
    if len(pidList) == 0: 
        return;
    pid = [];
    for connection in pidList:
        if connection.laddr[1] == PORT and (connection.status == "ESTABLISHED" or connection.status == "LISTEN"):
            pid.append(connection.pid);
    for p in pid:
        os.system("taskkill /F /PID " + str(p));
        
if __name__ == "__main__":
    launchWebServerAsAService();
    atexit.register(stopWebServer);