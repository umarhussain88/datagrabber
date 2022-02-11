import base64
import io
from dataclasses import dataclass
from typing import Optional
from pathlib import Path 


from googleapiclient.http import MediaIoBaseDownload
import pandas as pd 

from .google_utils import create_service
from src.logger import logger_util

# to do
#add a logger
#use gspread api to move data into gspread
#start productionisation the code 
##

logger = logger_util('gmail')

@dataclass
class Gmail:

    service: str = None
    user_id: str = 'me'


    #get emails from inbox
    def get_emails(self, query=''):
        # https://developers.google.com/gmail/api/v1/reference/users/messages/list
        response = self.service.users().messages().list(userId=self.user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = self.service.users().messages().list(userId=self.user_id, q=query, pageToken=page_token).execute()
            messages.extend(response['messages'])
        return messages


    #get Rfc822msgid
    def get_rfc822msgid(self,  message_id):
        # https://developers.google.com/gmail/api/v1/reference/users/messages/get
        message = self.service.users().messages().get(userId=self.user_id, id=message_id, format='raw').execute()
        return message['raw']

    #get attachment id 
    def get_attachment_id(self,  message_id):
        # https://developers.google.com/gmail/api/v1/reference/users/messages/get
        message = self.service.users().messages().get(userId=self.user_id, id=message_id).execute()
        if 'payload' in message and 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['filename']:
                    return part['body']['attachmentId'], part['filename']
        return None


    #get attachment from email 
    def get_attachment(self,  message_id, attachment_id):
        # https://developers.google.com/gmail/api/v1/reference/users/messages/attachments/get
        attachment = self.service.users().messages().attachments().get(userId=self.user_id, messageId=message_id, id=attachment_id).execute()
        return attachment

    #save attachment to file
    def save_attachment(self,attachment, filename):
        fh = io.BytesIO()
        data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
        fh.write(data)
        fh.seek(0)
        with open(filename, 'wb') as f:
            f.write(fh.read())
        fh.close()
        return filename


    #get email body
    def get_email_body(self,  message_id):
        # https://developers.google.com/gmail/api/v1/reference/users/messages/get
        message = self.service.users().messages().get(userId=self.user_id, id=message_id).execute()
        return message

    #get current labels
    def get_labels(self ):
        # https://developers.google.com/gmail/api/v1/reference/users/labels/list
        labels = self.service.users().labels().list(userId=self.user_id).execute()
        return labels

    #change labels of email
    def change_labels(self,  message_id, label_ids, remove_labels):
        # https://developers.google.com/gmail/api/v1/reference/users/messages/modify
        message = self.service.users().messages().modify(userId=self.user_id, id=message_id,
                                         body={'removeLabelIds': ['UNREAD', 'INBOX'] + remove_labels,
                                                'addLabelIds': label_ids}).execute()
        return message

    # get date of email
    def get_date(self,  message_id):
        # https://developers.google.com/gmail/api/v1/reference/users/messages/get
        message = self.service.users().messages().get(userId=self.user_id, id=message_id).execute()
        return message['internalDate']

    def read_bing_report(self, file_path : str):

        if not Path(file_path).exists():
            raise(FileNotFoundError(f'{file_path} not found'))
            logger.error(f'{file_path} not found')
        else:
            df = pd.read_excel(file_path, header=None,engine='openpyxl')
            #get start row
            start_row = df.isna().sum(axis=1).ne(0).idxmin()
            df = pd.read_excel(file_path, skiprows=start_row, skipfooter=1,engine='openpyxl')
            return df 

    def get_all_labels(self):
        labels = self.service.users().labels().list(userId=self.user_id).execute()
        return labels

    def save_labels_to_csv(self,labels):
        df = pd.DataFrame(labels['labels'])
        df.to_csv('labels.csv',index=False)

