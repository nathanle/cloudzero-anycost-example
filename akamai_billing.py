
import csv
import decimal
import getpass
import json
import sys
import os
import argparse
from datetime import datetime
import pandas as pd 

import requests

apiversion = os.environ.get("APIVERSION")
token = os.environ.get("TOKEN")

def get_invoivces():
    headers = {
        "accept": "application/json",
        "authorization": "Bearer {}".format(token)
    }
    url = "https://api.linode.com/{}/account/invoices".format(apiversion)

    response = requests.get(url, headers=headers)
    data = response.json()

    return data

def get_invoice_by_date(data, d):
    df = pd.DataFrame(data['data'])
    df.style.hide(axis='index')
    df['date'] = pd.to_datetime(df['date'])
    cutoff_date = datetime.now() - pd.Timedelta(days=d)
    records = df[df['date'] > cutoff_date]

    return records

data = get_invoivces()
r = get_invoice_by_date(data, 90)

#print(r)
print(r['id'].values.tolist())
