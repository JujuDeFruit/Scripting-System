"""
    --- Main ---

    @author Julien Raynal

"""

import datetime
import logging

from scripting_system import ScriptingSystem
from mattermost import Mattermost
from sftp_server import SFTPServer

def main():
    """
    Main

    Parameters
    ----------

    Return
    ------

    """

    error = False

    script = ScriptingSystem(8000, "conf.txt", "log.log")

    error = script.get_configuration()

    if not error:
        error = script.request_zip()

    if not error:
        error = script.extract_zip()

    mattermost = Mattermost(script.content, script.logging)

    if not script.zip_has_file():
        mattermost.payload["text"] += "| Zip matches file | :exclamation: Error |\n"
    else:
        mattermost.payload["text"] += "| Zip matches file | :white_check_mark: OK |\n"

        if not error:
            error = script.compress_to_tgz()

        # File date is not the same than before - file has been changed today
        is_date_ok = script.get_date() == datetime.datetime.now().date()

        # SFTP server area.
        sftp_options = {
            "ip": script.ip_sftp,
            "user": script.user,
            "password": script.pswd,
            "time-to-save": script.time_to_save,
        }

        sftp = SFTPServer(sftp_options, logging, is_date_ok)
        error = sftp.archival_check()

        if is_date_ok and not error:
            sftp.send_to_sftp_server(script.tgz_name)
            sftp.check_file_ack(script.tgz_name)
        mattermost.payload["text"] += sftp.content

    # Mattermost notification area
    if mattermost.payload["text"].find("Error") != -1:
        error = True

    if script.notification == "always" or (script.notification == "error" and error):
        with open("test.txt", "w") as test:
            test.write(mattermost.payload["text"])
            # Mattermost.sendMattermostNotification(payload, logging);

    if script.send == "yes" or script.send == "y":
        script.email.send()

    logging.info("Done")


if __name__ == "__main__":
    main()
