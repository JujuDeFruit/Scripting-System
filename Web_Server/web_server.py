# -*- coding: utf-8 -*-
"""
    -- Web Server --

    @author : Julien Raynal

"""

import http.server
import socketserver
import os
import threading
import atexit
import psutil

# Web server port.
WEB_SERVER_PORT = 8000

def launch():
    """
    Launch web server.

    Parameters
    ----------

    Return
    ------

    """

    handler_object = http.server.SimpleHTTPRequestHandler

    try:
        my_server = socketserver.TCPServer(("", WEB_SERVER_PORT), handler_object)
        print("http://localhost:" + str(WEB_SERVER_PORT) + " | OK")
        my_server.serve_forever()

    except Exception:
        print("Error launching server web !")
        raise Exception()


def launch_web_server_as_a_service():
    """
    Start web server as a service.

    Parameters
    ----------

    Return
    ------

    """

    download_thread = threading.Thread(target=launch, name="launcher")
    download_thread.start()
    # Launch web server as a service.
    os.system("python3 -m http.server " + str(WEB_SERVER_PORT))


def stop_web_server():
    """
    Stop web server, kill process.

    Parameters
    ----------

    Return
    ------

    """

    pid_list = psutil.net_connections()
    if len(pid_list) == 0:
        return
    pid = []
    for connection in pid_list:
        if (connection.laddr[1] == WEB_SERVER_PORT
                and connection.status in ("ESTABLISHED", "LISTEN")):
            pid.append(connection.pid)
    for process in pid:
        os.system("taskkill /F /PID " + str(process))


if __name__ == "__main__":
    launch_web_server_as_a_service()
    atexit.register(stop_web_server)
