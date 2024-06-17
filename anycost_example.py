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
import requests


def read_csv(file_path: str) -> list[dict[str, str]]:
    """Read a CSV file and return a list of rows as dictionaries."""
    with open(file_path, "r") as file:
        return list(csv.DictReader(file))


# Accumulate different data sources into a single list of CBF rows
cbf_rows = []

# Read the usage dataset, transform the rows into CBF Usage rows, and accumulate into cbf_rows
usage_rows = read_csv("example_cloud_provider_data/cloud_usage.csv")
for usage in usage_rows:
    # Apply the discount field to the cost field to calculate the discounted cost.
    # Take care when handling numbers. Decimal will maintain the precision.
    discounted_cost = str(decimal.Decimal(usage["cost"]) - abs(decimal.Decimal(usage["discount"])))
    cbf_rows.append(
        {
            "lineitem/type": "Usage",
            "resource/service": usage["sku"],
            "resource/id": f"instance-{usage["instance_id"]}",
            "time/usage_start": usage["usage_date"],
            "cost/cost": usage["cost"],
            "cost/discounted_cost": discounted_cost,
        }
    )

# Read the purchase commitment dataset, transform the rows into CBF CommittedUsePurchase rows, and accumulate into cbf_rows
purchase_commitment_rows = read_csv("example_cloud_provider_data/cloud_purchase_commitments.csv")
for purchase_commitment in purchase_commitment_rows:
    cbf_rows.append(
        {
            "lineitem/type": "CommittedUsePurchase",
            "resource/service": "CommittedUse",
            "resource/id": f"commit-{purchase_commitment["commitment_id"]}",
            "time/usage_start": purchase_commitment["commitment_date"],
            "cost/cost": purchase_commitment["cost"],
            "cost/discounted_cost": purchase_commitment["cost"],
        }
    )

# Read the discount dataset, transform the rows into CBF Discount rows, and accumulate into cbf_rows
discount_rows = read_csv("example_cloud_provider_data/cloud_discounts.csv")
for discount in discount_rows:
    cbf_rows.append(
        {
            "lineitem/type": "Discount",
            "resource/service": discount["discount_type"],
            "resource/id": f"discount-{discount["discount_id"]}",
            "time/usage_start": discount["usage_date"],
            "cost/cost": discount["discount"],
            "cost/discounted_cost": discount["discount"],
        }
    )

# Write the CBF rows to a CSV file for inspection
with open("cbf/cloud_cbf.csv", "w") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[  # Should contain the set of all columns in all rows
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

should_continue = input("Would you like to upload the example CBF to an AnyCost Stream connection? (y/n) ")

if should_continue.lower() != "y":
    sys.exit()

anycost_stream_connection_id = input("Enter your AnyCost Stream Connection ID: ")
cloudzero_api_key = getpass.getpass("Enter your CloudZero API Key: ")

# Send the CBF rows to the AnyCost Stream Billing Drop endpoint
response = requests.post(
    # An AnyCost Stream Connection must be created and the connection id must be used in the URL
    f"https://api.cloudzero.com/v2/connections/billing/anycost/{anycost_stream_connection_id}/billing_drops",
    # Your organization's CloudZero API key must be used for Authorization
    headers={"Authorization": cloudzero_api_key},
    # The request body should be a JSON object with a "data" key containing the CBF rows
    json={"data": cbf_rows},
)

print(json.dumps(response.json(), indent=2))
