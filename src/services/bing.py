import src 
from typing import Optional
from pathlib import PosixPath
from datetime import datetime
import pandas as pd 

logger = src.logger_util("bing")

def bing_report(
    client_file: str,
    folder_path: PosixPath,
    api_name: Optional[str] = "gmail",
    api_version: Optional[str] = "v1",
    scopes: Optional[str] = ["https://mail.google.com/"],
) -> None:

    service = src.create_service(client_file, api_name, api_version, scopes)
    gmail = src.Gmail(service, "me")

    gs = src.Sheets(
        log_sheet_name="Processed Data Log",
        secrets_file='env/token.json',
        auth_method="service_account",
    )
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info("getting bing report from gmail")
    emails = gmail.get_emails(query="label:data---new-card-bing")
    # save report to csv
    if emails:
        logger.info(f"bing report started {len(emails)} to parse")
        emails_dict = {}
        for email in emails:

            dt = pd.to_datetime(gmail.get_date(message_id=email["id"]), unit="ms")
            logger.info(f'email recieved on {dt}')
            attach = gmail.get_attachment_id(email["id"])
            emails_dict[attach] =  dt
            logger.info(f"parsing email {email['id']}")
            id_ = email["id"]

            if attach:
                gmail.change_labels(
                    email["id"],
                    label_ids=["Label_463380810507496833"],
                    remove_labels=["Label_5804416855963730919"],
                )
        attachment = max(emails_dict, key=emails_dict.get)

        if attachment:
            logger.info(f"parsing attachment {attachment[1]}")
            attach = gmail.get_attachment(email["id"], attachment[0])
            file = gmail.save_attachment(attach, folder_path.joinpath(attachment[1]))
            dataframe = gmail.read_bing_report(file)
            gs.post_data_to_gsheets(
                dataframe=dataframe,
                workbook_name="CARD Socials",
                worksheet_name="BING",
                start_time=start_time,
            )
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            gs.post_log_to_gsheets(
                report="Bing",
                start_time=start_time,
                end_time=end_time,
                message=f"Success - ID {id_} - recieved on {max(emails_dict.values())}",
            )
            logger.info("bing report posted to gsheets")
        else:
            logger.info("no attachment found")
            gs.post_log_to_gsheets(
                report="Bing",
                start_time=start_time,
                end_time="",
                message=f"No attachment found for {id_}",
            )
            # should this label be dif?
            gmail.change_labels(
                email["id"],
                label_ids=["Label_463380810507496833"],
                remove_labels=["Label_5804416855963730919"],
            )
    else:
        logger.info("No emails found")
        gs.post_log_to_gsheets(
            report="Bing",
            start_time=start_time,
            end_time="",
            message="No emails found for label:data---new-card-bing",
        )
