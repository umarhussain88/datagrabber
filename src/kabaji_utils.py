import json
from ast import literal_eval
from typing import Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from src.logger import logger_util

logger = logger_util(__name__)


def get_login_details(path : Optional[str] = './env/kajabi_login.json') -> dict:

    if not Path(path).exists():
        raise FileNotFoundError(f'{path} not found')
        logger.error('path is not found')
    with open(path, 'r') as f:
        return json.load(f)


#create session & login to website
def create_session_and_login() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})

    r = s.get('https://app.kajabi.com/login')

    soup = BeautifulSoup(r.text, 'html.parser')

    token = soup.find('meta', attrs={'name': 'csrf-token'})['content']

    credentials = get_login_details()


    s.post('https://app.kajabi.com/login',
        data={'user[email]': credentials['login'] , 'user[password]': credentials['password'],
                'user[remember_me]' : 0, 'authenticity_token' :token} )
    return s 


# get validation token & download report.
def get_token_and_get_report(session : requests.Session, report_url : str, report_key, custom_params : Optional[tuple] = None) -> str:
    
    r = session.get(report_url)

    soup = BeautifulSoup(r.text, 'html.parser')

    token = literal_eval([x.strip().split('=') for x 
                            in soup.find('script', attrs={'type': 'text/javascript'}).text.split(';') 
                            if 'window.validationToken' in x][0][1].strip())


    headers = {
    'authority': 'app.kajabi.com',
    'sec-ch-ua': '" Not;A Brand";v="99", "Microsoft Edge";v="97", "Chromium";v="97"',
    'accept': 'application/json, text/plain, */*',
    'authorization': token,
    'sec-ch-ua-mobile': '?1',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Mobile Safari/537.36 Edg/97.0.1072.55',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer':  report_url,
    'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8',
}


    request_url, url_params = report_url.split('?')
    #this is needed for the request param.
    if report_key == 'product_progress':
        product_id = url_params.split('=')[1]
        report_url = f'https://app.kajabi.com/api/client/reports/{report_key}/{product_id}.csv'
    else:
        report_url = f'https://app.kajabi.com/api/client/reports/{report_key}.csv'

    # report_url = report_url.replace('admin/sites/158992', f'api/client/{report_key}')
    request_url += '?' + url_params


    params = [p for par in url_params.split('&') 
            for p in zip(par.split('=')[::1],par.split('=')[1::1])  
        ]

    #this is needed for the api call /api/client/reports/sales.csv?site_id=158992&start_date=2020-01-01&end_date=2022-01-23&frequency=day
    #would be nice if they just exposed this as an end point!


    if 'site_id' not in params:
        params = (('site_id', '158992'),) +  tuple(params)        
    if custom_params:
        params += (custom_params,)

    # report_url_sub = re.sub('\?.*','.csv', report_url)
    response = session.get(report_url, headers=headers, params=params)



    return response
 





#to do 
#create dictionary with record path of each report
#create function to read json and pass into gspread sheet

