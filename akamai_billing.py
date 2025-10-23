
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
czid = os.environ.get("CZID")
czkey = os.environ.get("CZKEY")

def get_invoivces():
    headers = {
        "accept": "application/json",
        "authorization": "Bearer {}".format(token)
    }
    url = "https://api.linode.com/{}/account/invoices".format(apiversion)

    response = requests.get(url, headers=headers)
    data = response.json()
    if data["pages"] == 1:
        return data["data"]
    else:
        page = 2
        while page >= data["pages"]:
            url = "https://api.linode.com/v4/account/invoices?page={}".format(page)
            response_p = requests.get(url, headers=headers)
            datapage = response_p.json()
            for x in datapage["data"]:
                data["data"].append(x)
            page =+ 1
        return data["data"]

def get_invoice_detail(id):
    headers = {
        "accept": "application/json",
        "authorization": "Bearer {}".format(token)
    }
    url = "https://api.linode.com/{0}/account/invoices/{1}/items".format(apiversion, id)

    response = requests.get(url, headers=headers)
    data = response.json()

    #print("Pages {}".format(data["pages"]))

    if data["pages"] == 1:
        return data["data"]
    else:
        page = 2
        while page >= data["pages"]:
            url = "https://api.linode.com/{0}/account/invoices/{1}/items?page={2}".format(apiversion, id, page)
            response_p = requests.get(url, headers=headers)
            datapage = response_p.json()
            for x in datapage["data"]:
                data["data"].append(x)
            page =+ 1
        return data["data"]

def get_invoice_by_date(data, d):
    df = pd.DataFrame(data)
    df.style.hide(axis='index')
    df['date'] = pd.to_datetime(df['date'])
    cutoff_date = datetime.now() - pd.Timedelta(days=d)
    records = df[df['date'] > cutoff_date]

    return records

def invoice_detail(data):
    df = pd.DataFrame(data)
    df.style.hide(axis='index')

    return df 

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

    response = requests.post(
        f"https://api.cloudzero.com/v2/connections/billing/anycost/{czid}/billing_drops",
        headers={"Authorization": czkey},
        json={"data": cbf_rows},
    )

    print(json.dumps(response.json(), indent=2))

data = get_invoivces()
#print(data)
r = get_invoice_by_date(data, 90)

invoices = r['id'].values.tolist()

for i in invoices:
    r = get_invoice_detail(i)
    #print(r)
    d = invoice_detail(r)
    relabel = relabel_dataframe(d)
    cbf_rows = process_usage_data(relabel)
    print(cbf_rows)
    upload_to_anycost(cbf_rows)

