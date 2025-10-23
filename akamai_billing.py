
import csv
import decimal
import getpass
import json
import sys
import os
import argparse
from datetime import datetime
import pandas as pd 
pd.set_option('display.max_rows', None)

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

def get_invoice_detail(id):
    headers = {
        "accept": "application/json",
        "authorization": "Bearer {}".format(token)
    }
    url = "https://api.linode.com/{0}/account/invoices/{1}/items".format(apiversion, id)

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

def invoice_detail(data):
    df = pd.DataFrame(data['data'])
    df.style.hide(axis='index')

    return df 

def create_cbf_dataframe():
    df = pd.DataFrame(columns=['lineitem/type', '', ''])


def relabel_dataframe(df):
    df_new = df.drop(['unit_price', 'type'], axis=1)
    df_renamed = df_new.rename(columns={'label': 'resource/id', 'amount': 'lineitem/usage', 'quantity': 'usage/amount', 'tax': 'lineitem/tax', 'total': 'cost/cost', 'from': 'time/usage_start', 'to': 'time/usage_end', 'region': 'resource/region'})
    df.style.hide(axis='index')

    return df_renamed

def process_usage_data(usage_rows) -> list[dict[str, str]]:
    """Process usage data and return transformed CBF rows."""
    cbf_rows = []
    for index, usage in usage_rows.iterrows():
        if usage["resource/region"] == None:
            usage["resource/region"] = "None"
        cbf_rows.append({
            "lineitem/type": "Usage",
            "resource/id": usage["resource/id"],
            #"lineitem/usage": usage["lineitem/usage"],
            "usage/amount": str(usage["usage/amount"]),
            #"lineitem/tax": str(usage["lineitem/tax"]),
            "cost/cost": str(usage["cost/cost"]),
            "time/usage_start": usage["time/usage_start"],
            "time/usage_end": usage["time/usage_end"],
            "resource/region": usage["resource/region"],
        })
    return cbf_rows

def upload_to_anycost(cbf_rows: list[dict[str, str]]):
    """Upload CBF rows to an AnyCost Stream connection."""
    anycost_stream_connection_id = input("Enter your AnyCost Stream Connection ID: ")
    cloudzero_api_key = getpass.getpass("Enter your CloudZero API Key: ")

    response = requests.post(
        f"https://api.cloudzero.com/v2/connections/billing/anycost/{anycost_stream_connection_id}/billing_drops",
        headers={"Authorization": cloudzero_api_key},
        json={"data": cbf_rows},
    )

    print(json.dumps(response.json(), indent=2))

data = get_invoivces()
r = get_invoice_by_date(data, 90)

invoices = r['id'].values.tolist()

for i in invoices:
    r = get_invoice_detail(i)
    d = invoice_detail(r)
    relabel = relabel_dataframe(d)
    #csv = relabel.to_csv(index=False)
    cbf_rows = process_usage_data(relabel)
    print(cbf_rows)
    upload_to_anycost(cbf_rows)

