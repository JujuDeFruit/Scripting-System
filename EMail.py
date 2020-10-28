# -*- coding: utf-8 -*-
"""
    Email managing

    @author: Julien Raynal 
"""

from email_validator import validate_email
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

import json
import logging

class EMail():
    
    """
        Constructor to build the mail instance
    """
    def __init__(self, json, logging_, emailContent_):
        
        self.logging = logging_;
        
        auth_ = json['auth'];                                   # Authentification of sender email.
        logFileAttached_ = json['log-file-attached'].lower();   # Choice of user to attach or not log file.
        title_ = json['title'];                                 # Subject of the mail.
        dest_ = json['dest'];                                   # Array of all destination emails.
        self.ip = json['server']['ip'];                         # Get the mail external server IP.
        self.content = "";
        
        try:
            self.port = int(json['server']['port']);            # Try to cast port value from JSON to int.
        except ValueError:
            self.port = 465;
            self.logging.warning("Email server port format not supported. Default value is 465.");  # If value is not supported, default port value is 465.
            
        if auth_['email'] == "":
            self.logging.warning("Blank at the sending email identifier in the conf file : example@ex.com. Email(s) not sent.");   
            self.content += "| Email | :exclamation: Error |\n";
        if auth_['password'] == "":
            self.logging.warning("Blank at the sending email password in the conf file. Email(s) not sent.");
            self.content += "| Email | :exclamation: Error |\n";
        # If user did not input a correct format for attachment.
        if not (logFileAttached_ == "yes" or  logFileAttached_ == "no" or  logFileAttached_ == "y" or  logFileAttached_ == "n"):
            self.logging.warning("Uncorrect value for attached log in conf file. Yes by default");
            logFileAttached_ = 'yes';
        if title_ == "":
            self.logging.warning("No title for email, \'Scripting System rapport\' by default");
            title_ = "Scripting System rapport";    # Default e-mail object.
        if len(dest_) == 0:
            self.logging.warning("No destination emails !");
        else:
            for email in dest_:
                if not validate_email(email):
                    self.logging.warning(email + " is not valid !");
                    dest_.remove(email);
        
        self.auth = auth_;
        self.logFileAttached = logFileAttached_;
        self.title = title_;
        self.dest = dest_;
        self.contentMail = emailContent_;
    
    """
        Attach log file to MIME message if user decided it. 
    """
    def attachment(self, msg_):
        # If user wrote 'Yes' or 'Y' to attach file to e-mail.
        if self.logFileAttached == "yes" or self.logFileAttached == 'y':
            try:
                with open('log.log', 'rb') as attachment:
                    # instance of MIMEBase and named as p 
                    p = MIMEBase('application', 'octet-stream') 
                                  
                    # To change the payload into encoded form 
                    p.set_payload((attachment).read());
                                  
                    # encode into base64 
                    encoders.encode_base64(p); 
                    
                    # Change mail header to dispose attachment
                    p.add_header('Content-Disposition', "attachment; filename= log.log"); 
                    
                    # attach the instance 'p' to instance 'msg' 
                    msg_.attach(p);
                    self.logging.info("Attachment is OK.")
                    self.content += "| Attachment | :white_check_mark: OK |\n";
                    
            except IOError:
                self.logging.warning("I/O error occured during mail attachment loading. No attachment send with mails.");
                self.content += "| Attachment | :exclamation: Error |\n";
            except Exception:
                self.logging.warning("Unknown error occured during mail attachment loading. No attachment send with mails.");
                self.content += "| Attachment | :exclamation: Error |\n";
        
        return msg_;
    
    """
        Log-in to e-mail account and send e-mail to all valid e-mails destinations.
    """
    def loginAndSend(self):
        try:
            # Log-in to the sender e-mail. 
            self.server.login(self.auth['email'], self.auth['password']);  
            
            # Create a MIME message that will be send. Use MIME type to attach log file if needed.
            msg = MIMEMultipart();
            msg['Subject'] = self.title;        # Subject of the send e-mail. 
            msg.attach(MIMEText(self.content, 'plain'));#self.contentMail;       # Add text content to the mail.
            msg = self.attachment(msg);         # Attach log file to message if needed.
            # Convert the MIME message into string to send it as a string to all destination e-mails.
            self.server.sendmail(self.auth['email'], self.dest, msg.as_string());
            
            # Close the server connection after using resources.
            self.server.quit();
            
            self.logging.info("Emails send.");
            self.content += "| Sending e-mails | :white_check_mark: OK |\n";
        except Exception:
            self.logging.warning("Unknown error occured while logging-in to your mail account. Email(s) not sent.");
            self.content += "| Sending e-mails | :exclamation: Error |\n";

    """
        Create a secure connection to SMTP server to send e-mails from external server.
    """
    def emailServerSMTP(self):
        # Create a secure SSL context
        context = ssl.create_default_context();
        try: 
            # Open secure connection with SMTP server to send e-mails
            self.server = smtplib.SMTP_SSL(self.ip, port = self.port, context = context);
            # Log to e-mail account and send e-mails to destinations
            self.loginAndSend();
        except Exception:
            self.logging.warning("Unknown error occured while connecting to mail server. Email(s) not sent.");
            self.content += "| Sending e-mails | :exclamation: Error |\n";
            
    """
        Create a connection ton internal e-mail server of PC and send e-mails through it.
        Server configured with "hMailServer", domain : "localhost.com", password : "35279155".
        Account is "admin@localhost.com" and password is "admin".
    """
    def internalServer(self):
        #context = ssl.create_default_context();
        with smtplib.SMTP('localhost') as server:
            server.login("admin@localhost.com", "admin");  
            msg = MIMEMultipart();
            msg['Subject'] = "Object";
            server.sendmail("admin@localhost.com", ["raynaljulien70@gmail.com"], msg.as_string());
    
    """
        If IP origin is empty, then send mail with internal server.
    """
    def send(self):
        if self.ip != "":
            self.emailServerSMTP();
        else:
            self.internalServer();
            
if __name__ == "__main__":
    
    logging.basicConfig(#filename = log_,                                    # Log file
                        level = logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',     # Log file writting format
                        datefmt='%d/%m/%Y %I:%M:%S %p', 
                        force = True);
    
    with open('conf.txt', 'r') as json_config:
        data = json.load(json_config);
        #data['email']['server']['ip'] = '';
        email = EMail(data['email'], logging, "");
    email.send();