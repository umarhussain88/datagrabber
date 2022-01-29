from datetime import datetime
from io import StringIO
from pathlib import Path
from time import sleep
import re 
import warnings
#ignore simple warnings
warnings.filterwarnings('ignore')

import pandas as pd

from src import iso_date_folder
from src.gmail import Gmail, create_service
from src.kabaji_utils import create_session_and_login, get_token_and_get_report
from src.logger import logger_util
from src.sheets import Sheets

CLIENT_FILE = 'your_client_secret.json' # add your file here.
API_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ["https://mail.google.com/"]



service = create_service(CLIENT_FILE, API_NAME, API_VERSION, SCOPES)
gmail = Gmail(service, 'me')
gs = Sheets(log_sheet_name='Processed Data Log', secrets_file=CLIENT_FILE, auth_user='./env/authorized_user.json', auth_method='oauth')

logger = logger_util('main')


if __name__ == '__main__':
    logger.info('Starting program... \nfetching Kajabi reports.')
    kajabi_reports = gs.get_kajabi_urls()
    logger.info('Urls grabbed from google sheets')

    session = create_session_and_login()
    logger.info('Session created and logged in')

    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    folder_path = iso_date_folder(Path(__file__).parent.joinpath('reports'))
    logger.info('Folder path created')

    #clear log sheet
    gs.clear_log_sheet()
    logger.info('Log sheet cleared')
    #add headers to log sheet
    
    #catch and log any error:
    try:
        for key,value in kajabi_reports.items():
            custom_params = ('csv_type','offers') if key == 'Net Revenue' else None
            response = get_token_and_get_report(session, value['final_url'], value['reportKey'], custom_params=custom_params)
            logger.info('token and report grabbed')
            if response.status_code == 404:
                logger.info('Report not found - 404 error.')
                gs.post_log_to_gsheets(report=key, start_time=start_time, end_time='', message='Error - 404')
            else:
                df = pd.read_csv(StringIO(response.text))
                name = value['final_url'].split('=')[1] + '_' if value['reportKey'] == 'product_progress' else ''

                filename = f"{key}.csv"
                logger.info(f'Report grabbed and saved {filename}')
                #remove illegal characters from filename
                filename = re.sub(r'[^\w\-_\.]', '_', filename)
                file_path = folder_path.joinpath(filename)

                df.to_csv(file_path,index=False)
                gs.post_data_to_gsheets(dataframe=df, workbook_name='KAJABI', worksheet_name=key,
                                        start_time = start_time)
                end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                gs.post_log_to_gsheets(report=key, start_time=start_time, end_time=end_time, message='Success')
            sleep(2.5)
    except Exception as e:
        gs.post_log_to_gsheets(report=key, start_time=start_time, end_time='', message=str(e))

    

    logger.info('getting bing report from gmail')
    emails = gmail.get_emails(query='label:data---new-card-bing') 
    #save report to csv
    if emails:
        logger.info('bing report started')
        for email in emails:
            attachment = gmail.get_attachment_id( email['id'])
            logger.info(f"parsing email {email['id']}")
            id_ = email['id']
        if attachment:
            logger.info(f'parsing attachment {attachment[1]}')   
            attach = gmail.get_attachment(email['id'], attachment[0])
            file = gmail.save_attachment(attach, folder_path.joinpath(attachment[1]))
            dataframe = gmail.read_bing_report(file)
            gmail.change_labels(email['id'], label_ids=['Label_463380810507496833'],remove_labels=['Label_5804416855963730919'])

            gs.post_data_to_gsheets(dataframe=dataframe, workbook_name='CARD Socials', 
                                    worksheet_name='BING', start_time=start_time)
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            gs.post_log_to_gsheets(report='Bing', start_time=start_time, end_time=end_time, message=f'Success - ID {id_}')
            logger.info('bing report posted to gsheets')
        else:
            logger.info('no attachment found')
            gs.post_log_to_gsheets(report='Bing', start_time=start_time, end_time='', message=f'No attachment found for {id_}')
            #should this label be dif?
            gmail.change_labels(email['id'], label_ids=['Label_463380810507496833'], remove_labels=['Label_5804416855963730919'])
    else:
        logger.info('No emails found') 
        gs.post_log_to_gsheets(report='Bing', start_time=start_time, end_time='', message='No emails found for label:data---new-card-bing')
                
            

















# if __name__ == '__main__':
#     # labelsList = service.users().labels().list(userId='me').execute()
#     # print(labelsList)
#     emails = get_emails(service, user_id='me', query='from:knowi')
#     for email in emails:
#         attachment = get_attachment_id(service, 'me', email['id'])
#         if attachment:
#             get_attachment(service, 'me',email['id'], attachment[0])
        
#         change_labels(service, 'me', email['id'], ['Label_7860952478697144767'])


#     fb_emails = get_emails(service, user_id='me', query='from:facebook.com')

#     if fb_emails:
#         for email in fb_emails:
#             body = get_email_body(service, 'me', email['id'])
#             #get download url from body
#             url = (
#                  re.search("(?P<url>https?://[^\s]+source=email>)", str(body))
#                  .group("url")
#                  .split(">")[0]
#              )
#         # do something with url
    