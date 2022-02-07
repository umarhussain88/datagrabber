from pathlib import Path
import warnings
# ignore simple warnings
warnings.filterwarnings("ignore")
from src import iso_date_folder, logger_util, Sheets, bing_report, kajabi_reports
from sys import argv


CLIENT_FILE = "sekrut"  # add your file here.
API_NAME = "gmail"
API_VERSION = "v1"
SCOPES = ["https://mail.google.com/"]

gs = Sheets(
    log_sheet_name="Processed Data Log",
    secrets_file=None,
    auth_method="service_account",
)

logger = logger_util("main")
folder_path = iso_date_folder(Path(__file__).parent.joinpath("reports"))


if __name__ == "__main__":
    acceptable_arguments = ['bing', 'kajabi']
    #check if arg is in acceptable_arguments
    if len(argv) > 1 and argv[1] in acceptable_arguments:
        logger.info(f'running report for {argv[1]}')
        if argv[1] == 'bing':
            bing_report(
                client_file=CLIENT_FILE,
                folder_path=folder_path,
                api_name=API_NAME,
                api_version=API_VERSION,
                scopes=SCOPES,
            )
        elif argv[1] == 'kajabi':
            kajabi_reports()



