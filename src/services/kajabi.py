from pathlib import Path
# from src.sheets import Sheets
# from src.kabaji_utils import create_session_and_login, get_token_and_get_report
# from src.logger import logger_util
# from src import iso_date_folder
import src

import pandas as pd
from datetime import datetime
from io import StringIO
import re
from time import sleep


logger = src.logger_util("kajabi")

gs = src.Sheets(
    log_sheet_name="Processed Data Log",
    secrets_file=None,
    auth_method="service_account",
)


def kajabi_reports():
    logger.info("Starting program... \nfetching Kajabi reports.")
    kajabi_reports = gs.get_kajabi_urls()
    logger.info("Urls grabbed from google sheets")

    session = src.create_session_and_login()
    logger.info("Session created and logged in")

    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("Folder path created")

    # clear log sheet
    logger.info("calling clear log func sheet cleared")
    gs.clear_log_sheet()
    # add headers to log sheet

    # catch and log any error:
    try:
        for key, value in kajabi_reports.items():
            custom_params = ("csv_type", "offers") if key == "Net Revenue" else None
            response = src.get_token_and_get_report(
                session,
                value["final_url"],
                value["reportKey"],
                custom_params=custom_params,
            )
            logger.info("token and report grabbed")
            if response.status_code == 404:
                logger.info("Report not found - 404 error.")
                gs.post_log_to_gsheets(
                    report=key,
                    start_time=start_time,
                    end_time="",
                    message="Error - 404",
                )
            else:
                df = pd.read_csv(StringIO(response.text))
                name = (
                    value["final_url"].split("=")[1] + "_"
                    if value["reportKey"] == "product_progress"
                    else ""
                )

                filename = f"{key}.csv"
                logger.info(f"Report grabbed - {filename}")

                gs.post_data_to_gsheets(
                    dataframe=df,
                    workbook_name="KAJABI",
                    worksheet_name=key,
                    start_time=start_time,
                )
                end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                gs.post_log_to_gsheets(
                    report=key,
                    start_time=start_time,
                    end_time=end_time,
                    message="Success",
                )
            sleep(2.5)
    except Exception as e:
        gs.post_log_to_gsheets(
            report=key, start_time=start_time, end_time="", message=str(e)
        )
