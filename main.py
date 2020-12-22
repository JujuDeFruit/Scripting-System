"""
    --- Main ---

    @author Julien Raynal

"""

from scripting_system import ScriptingSystem
from sftp_server import SFTPServer

def main():
    """
    Main

    Parameters
    ----------

    Return
    ------

    """

    script = ScriptingSystem(8000, "config.json")

    script.get_configuration()

    script.request_zip()

    script.extract_zip()

    if script.zip_has_file():

        script.compress_to_tgz()

        # File date is not the same than before - file has been changed today
        is_date_ok = script.compare_date()

        # SFTP server area.
        sftp_options = {
            "ip": script.ip_sftp,
            "user": script.user,
            "password": script.pswd,
            "time-to-save": script.time_to_save,
            }

        sftp = SFTPServer(sftp_options, script.log_email_matt, is_date_ok)
        sftp.archival_check()

        if is_date_ok :
            sftp.send_to_sftp_server(script.tgz_name)
            sftp.check_file_ack(script.tgz_name)

    script.log_email_matt.send_all()
    script.clean(sftp)

if __name__ == "__main__":
    main()
