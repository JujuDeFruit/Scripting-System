# -*- coding: utf-8 -*-
"""
    Email managing

    @author: Julien Raynal 
"""

import logging
from email_validator import validate_email
import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

class EMail():
    
    """
        Constructor to build the mail instance
    """
    def __init__(self, json):
        
        auth_ = json['auth'];
        logFileAttached_ = json['log-file-attached'].lower(); 
        title_ = json['title'];
        dest_ = json['dest'];
        self.ip = json['server']['ip'];
        
        try:
            self.port = int(json['server']['port']);
        except ValueError:
            self.port = 465;
            logging.warning("Email server port format not supported. Default value is 465.");
            
        if auth_['email'] == "":
            logging.warning("Blank at the sending email identifier in the conf file : example@ex.com. Email(s) not sent.");   
            return;
        if auth_['password'] == "":
            logging.warning("Blank at the sending email password in the conf file. Email(s) not sent.");
            return;
        if not (logFileAttached_ == "yes" or  logFileAttached_ == "no" or  logFileAttached_ == "y" or  logFileAttached_ == "n"):
            logging.warning("Uncorrect value for attached log in conf file. Yes by default");
            logFileAttached_ = 'yes';
        if title_ == "":
            logging.warning("No title for email, \'Scripting System rapport\' by default");
            title_ = "Scripting System rapport";
        if len(dest_) == 0:
            logging.warning("No destination emails !");
        else:
            for email in dest_:
                if not validate_email(email):
                    logging.warning(email + " is not valid !");
                    dest_.remove(email);
        
        self.auth = auth_;
        self.logFileAttached = logFileAttached_;
        self.title = title_;
        self.dest = dest_;
        self.content = "";
        
        logging.basicConfig(#filename = "log.log", 
                        level = logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%d/%m/%Y %I:%M:%S %p', 
                        force = True);
        
    def getDomainName(self):
        return self.auth['email'].split("@")[-1].rsplit('.', 1)[0];
    
    def attachment(self, msg_):
        if self.logFileAttached == "yes" or self.logFileAttached == 'y':
            try:
                with open('log.log', 'rb') as attachment:
                    # instance of MIMEBase and named as p 
                    p = MIMEBase('application', 'octet-stream') 
                                  
                    # To change the payload into encoded form 
                    p.set_payload((attachment).read());
                                  
                    # encode into base64 
                    encoders.encode_base64(p); 
                    p.add_header('Content-Disposition', "attachment; filename= log.log"); 
                    
                    # attach the instance 'p' to instance 'msg' 
                    msg_.attach(p)
            except IOError:
                logging.warning("I/O error occured during mail attachment loading. No attachment send with mails.");
            except Exception:
                logging.warning("Unknown error occured during mail attachment loading. No attachment send with mails.");
        return msg_;
    
    def loginAndSend(self):
        try:
            self.server.login(self.auth['email'], self.auth['password']);     
                    
            msg = MIMEMultipart();
            msg['Subject'] = self.title;          
            msg = self.attachment(msg);
            self.server.sendmail(self.auth['email'], self.dest, msg.as_string());
            self.server.quit();
            logging.info("Emails send.");
            
        except smtplib.SMTPAuthenticationError:
            logging.warning("Email authentification error. Incorrect email and/or password. Email(s) not sent.");
        except smtplib.SMTPNotSupportedError:
            logging.warning("Authentification not supported by server. Please change domain name on your email. Email(s) not sent.");
        except smtplib.SMTPException:
            logging.warning("Error occured while logging-in to your mail account. Email(s) not sent.");
        except Exception:
            logging.warning("Unknown error occured while logging-in to your mail account. Email(s) not sent.");

    def emailServerSMTP(self):
        # Create a secure SSL context
        context = ssl.create_default_context();
        try: 
            self.server = smtplib.SMTP_SSL(self.ip, port = self.port, context = context)                 
            self.loginAndSend();
        except smtplib.SMTPServerDisconnected:
            logging.warning("Mail server unexpectly disconnected. Email(s) not sent.");
        except smtplib.SMTPResponseException as err:
            logging.warning("Mail server returned unknown error code " + str(err.smtp_code) + " : " + err.smtp_error + ". Email(s) not sent.");
        except smtplib.SMTPRecipientsRefused as err:
            logging.warning("Some recipient adresses are not accepted by mail server. Email(s) not sent.");
            for rec in err.recipients:
                logging.warning(rec + " not accepted by mail server, error code " + rec.smtp_code + " : " + rec.smtp_error + ".");
        except Exception:
            logging.warning("Unknown error occured while connecting to mail server. Email(s) not sent."); 
    
    #TODO
    def internalServer(self):
        pass;
    
def sendEmails(conf_):     
    with open(conf_, 'r') as json_config:
        data = json.load(json_config); 
        send = data['send-emails'].lower();
        
        if send == "no" or send == "n":
            return;
        
        email = EMail(data['email']);  
        
        if email.auth['email'] == "" or email.auth['password'] == "":
            return;
        
        if email.ip != "":
            email.emailServerSMTP();
        else:
            email.internalServer();
                
if __name__ == "__main__":
    sendEmails("conf.txt");