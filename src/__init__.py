from pathlib import Path 
from datetime import datetime

#create iso date folders to store reports
def iso_date_folder(path : Path) -> None:
    

    if not path.exists():
        path.mkdir(parents=True)
    
    dt = datetime.now().strftime('%Y-%m-%d')

    iso_date_folder = path.joinpath(dt)
    if not iso_date_folder.exists():
        iso_date_folder.mkdir()
    
    return iso_date_folder
    
