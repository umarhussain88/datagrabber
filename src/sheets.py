from dataclasses import dataclass
from typing import Dict, Optional
import gspread 
import pandas as pd 
from gspread.exceptions import WorksheetNotFound
from src.logger import logger_util

#create gsheets logger
logger = logger_util('gsheets')

#http://localhost:8080/?state=HG7hC4ymNeBHvpzuH9M0yKYnD3SxfZ&code=4/0AX4XfWg_khisVBDaGieeXaCyBbTK_a1NZNKGw0sm0cJS_MFMBkRR3C2jKKbzqcR8REWwkg&scope=https://mail.google.com/
@dataclass
class Sheets:

    secrets_file : str
    log_sheet_name: str
    auth_user: Optional[str] = None
    auth_method : Optional[str] = 'oauth' 


    #post init method
    def __post_init__(self):
        if 'oauth' in self.auth_method:
            object.__setattr__(self,'service', gspread.oauth(credentials_filename=self.secrets_file,
                                authorized_user_filename=self.auth_user) )
        elif 'service_account' in self.auth_method:
            object.__setattr__(self,'service', gspread.service_account() )
    

    #get kajabi urls from ghseet
    def get_kajabi_urls(self) -> Dict[str,str]:
        sh = self.service.open('Kajabi Source URLs')
        ws = sh.worksheet('Sheet1')
        df = pd.DataFrame(ws.get_all_records())

        keys = df.loc[df["Status"].eq("Active"), 
                            ["Sheet Name", "final_url", "reportKey"]
                     ].set_index("Sheet Name").to_dict(orient="index")
        return keys 
    
    
    def post_data_to_gsheets(self, dataframe : pd.DataFrame, 
                             start_time : str, 
                             workbook_name : str, worksheet_name : str) -> None:
        sh = self.service.open(workbook_name)

        #need to make sure fields are json serializable
        dataframe[dataframe.select_dtypes("datetime").columns] = (
         dataframe.select_dtypes("datetime")
         .apply(lambda x: x.dt.strftime("%Y-%m-%d:%H:%M:%S"))
         .fillna("")
        )

        try:
            current_ws = sh.worksheet(worksheet_name)
            current_cols = current_ws.get_all_values()[0]
            current_cols = [col for col in current_cols if col != '']

            if len(current_cols) == len(dataframe.columns):
                current_ws.clear()
                current_ws.update([current_cols] + dataframe.fillna('').values.tolist())
            else:
                self.post_log_to_gsheets(worksheet_name,start_time, '', 'Columns not matching')
        except WorksheetNotFound:
            logger.error(f'Worksheet not found - {worksheet_name}')
            self.post_log_to_gsheets(report=worksheet_name, start_time=start_time, message=f'Error - Worksheet not found with name {worksheet_name}')


    def post_log_to_gsheets(self, report : str, start_time : str, message : str,
                            end_time : Optional[str] = pd.Timestamp('now')) -> None:
        sh = self.service.open(self.log_sheet_name)
        ws = sh.get_worksheet(0)
        ws.append_row([report, start_time, end_time, message])


    def clear_log_sheet(self) -> None:
        sh = self.service.open(self.log_sheet_name)
        ws = sh.get_worksheet(0)

        df = pd.DataFrame({"end": pd.to_datetime(ws.col_values(3)[1:])})
        delta = pd.Timestamp('now') - df["end"].min()
        logger.info(f'Delta {delta}')

        if delta.days > 30:
            logger.info('Clearing log sheet as delta threshold reached')
            ws.clear()
            ws.append_row(['Report','Start Time','End Time','Message'])


    def read_excel_from_gdrive(self, file_id : str, sheet_name : str) -> pd.DataFrame:
        sh = self.service.open_by_key(file_id)
        ws = sh.worksheet(sheet_name)
        df = pd.DataFrame(ws.get_all_records())
        return df
        
