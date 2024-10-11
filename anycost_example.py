#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# An example script showcasing the structure of an AnyCost Stream adaptor.
# An adaptor generally performs the following steps:
#   1. Query data from a given cloud provider for a billing month
#   2. Transform that cloud provider data into Common Billing Format (CBF)
#   3. Send that CBF data into the CloudZero platform through an AnyCost Stream connection

import csv
import decimal
import getpass
import json
import sys
from typing import List, Dict

import requests


def read_csv(file_path: str) -> List[Dict[str, str]]:
    """Read a CSV file and return a list of rows as dictionaries."""
    with open(file_path, "r") as file:
        return list(csv.DictReader(file))


def process_usage_data(file_path: str) -> List[Dict[str, str]]:
    """Process usage data and return transformed CBF rows."""
    usage_rows = read_csv(file_path)
    cbf_rows = []
    for usage in usage_rows:
        discounted_cost = str(decimal.Decimal(usage["cost"]) - abs(decimal.Decimal(usage["discount"])))
        cbf_rows.append({
            "lineitem/type": "Usage",
            "resource/service": usage["sku"],
            "resource/id": f"instance-{usage['instance_id']}",
            "time/usage_start": usage["usage_date"],
            "cost/cost": usage["cost"],
            "cost/discounted_cost": discounted_cost,
        })
    return cbf_rows


def process_purchase_commitments(file_path: str) -> List[Dict[str, str]]:
    """Process purchase commitments data and return transformed CBF rows."""
    purchase_commitment_rows = read_csv(file_path)
    cbf_rows = []
    for purchase_commitment in purchase_commitment_rows:
        cbf_rows.append({
            "lineitem/type": "CommittedUsePurchase",
            "resource/service": "CommittedUse",
            "resource/id": f"commit-{purchase_commitment['commitment_id']}",
            "time/usage_start": purchase_commitment["commitment_date"],
            "cost/cost": purchase_commitment["cost"],
            "cost/discounted_cost": purchase_commitment["cost"],
        })
    return cbf_rows


def process_discounts(file_path: str) -> List[Dict[str, str]]:
    """Process discounts data and return transformed CBF rows."""
    discount_rows = read_csv(file_path)
    cbf_rows = []
    for discount in discount_rows:
        cbf_rows.append({
            "lineitem/type": "Discount",
            "resource/service": discount["discount_type"],
            "resource/id": f"discount-{discount['discount_id']}",
            "time/usage_start": discount["usage_date"],
            "cost/cost": discount["discount"],
            "cost/discounted_cost": discount["discount"],
        })
    return cbf_rows


def write_cbf_rows_to_csv(cbf_rows: List[Dict[str, str]], output_file_path: str):
    """Write CBF rows to a CSV file."""
    with open(output_file_path, "w") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "lineitem/type",
                "resource/service",
                "resource/id",
                "time/usage_start",
                "cost/cost",
                "cost/discounted_cost",
            ],
        )
        writer.writeheader()
        writer.writerows(cbf_rows)


def upload_to_anycost(cbf_rows: List[Dict[str, str]]):
    """Upload CBF rows to an AnyCost Stream connection."""
    anycost_stream_connection_id = input("Enter your AnyCost Stream Connection ID: ")
    cloudzero_api_key = getpass.getpass("Enter your CloudZero API Key: ")

    response = requests.post(
        f"https://api.cloudzero.com/v2/connections/billing/anycost/{anycost_stream_connection_id}/billing_drops",
        headers={"Authorization": cloudzero_api_key},
        json={"data": cbf_rows},
    )

    print(json.dumps(response.json(), indent=2))


def main():
    cbf_rows = []
    cbf_rows.extend(process_usage_data("example_cloud_provider_data/cloud_usage.csv"))
    cbf_rows.extend(process_purchase_commitments("example_cloud_provider_data/cloud_purchase_commitments.csv"))
    cbf_rows.extend(process_discounts("example_cloud_provider_data/cloud_discounts.csv"))

    write_cbf_rows_to_csv(cbf_rows, "cbf/cloud_cbf.csv")

    should_continue = input("Would you like to upload the example CBF to an AnyCost Stream connection? (y/n) ")
    if should_continue.lower() == "y":
        upload_to_anycost(cbf_rows)
    else:
        sys.exit()


if __name__ == "__main__":
    main()
