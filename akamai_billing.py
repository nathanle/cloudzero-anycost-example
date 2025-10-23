
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

headers = {
    "accept": "application/json",
    "authorization": "Bearer {}".format(token)
}
url = "https://api.linode.com/{}/account/invoices".format(apiversion)

response = requests.get(url, headers=headers)
data = response.json()
df = pd.DataFrame(data['data'])
df['date'] = pd.to_datetime(df['date'])
cutoff_date = datetime.now() - pd.Timedelta(days=30)

print(df)
records_last_30_days = df[df['date'] > cutoff_date]
print(records_last_30_days)
