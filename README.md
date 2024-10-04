# AnyCost Stream Example

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE-OF-CONDUCT.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
![GitHub release](https://img.shields.io/github/release/cloudzero/template-cloudzero-open-source.svg)

This repository contains an example script to illustrate the structure of an Adaptor for an [AnyCost Stream](https://docs.cloudzero.com/docs/anycost-stream-getting-started) connection. The sample Adaptor script is written in Python and transforms cost data to the [Common Bill Format (CBF)](https://docs.cloudzero.com/docs/anycost-common-bill-format-cbf), then sends the CBF to the [CloudZero REST API](https://docs.cloudzero.com/reference/createoneanycoststreamconnectionbillingdrop).

You can use this Adaptor as a model for structuring your own AnyCost Stream Adaptor, and modify it to fit your use case.

**Note:** The AnyCost Stream feature is in beta. Contact your CloudZero representative to request access.

## Table of Contents

- [Documentation](#documentation)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Usage Examples](#usage-examples)
- [Contributing](#contributing)
- [Support + Feedback](#support--feedback)
- [Vulnerability Reporting](#vulnerability-reporting)
- [What is CloudZero?](#what-is-cloudzero)
- [License](#license)

## Documentation

- [Getting Started with AnyCost Stream](https://docs.cloudzero.com/docs/anycost-stream-getting-started)
- [Creating AnyCost Custom Adaptors](https://docs.cloudzero.com/docs/anycost-custom-adaptors)
- [Sending AnyCost Stream Data to CloudZero](https://docs.cloudzero.com/docs/anycost-send-stream-data)
- [CloudZero Common Bill Format](https://docs.cloudzero.com/docs/anycost-common-bill-format-cbf)
- [CloudZero API Authorization](https://docs.cloudzero.com/reference/authorization)
- [AnyCost Stream API](https://docs.cloudzero.com/reference/createoneanycoststreamconnectionbillingdrop)

## Installation

### Prerequisites

- Python 3.12
- [An existing AnyCost Stream connection](https://docs.cloudzero.com/docs/anycost-stream-getting-started#step-1-register-the-connection-in-the-ui)
- [A CloudZero API key](https://app.cloudzero.com/organization/api-keys)

### Install Dependencies

Consider using the [venv](https://docs.python.org/3/library/venv.html) system module to create a virtual environment:

```
python3 -m venv venv
```

Activate the virtual environment, if you chose to create it:

```
source venv/bin/activate
```

Install the required dependency, which is the Python [requests](https://requests.readthedocs.io/en/latest/) module:

```
pip install -r requirements.txt
```

## Getting Started

An [AnyCost Stream connection](https://docs.cloudzero.com/docs/anycost-stream-getting-started) automates the flow of cost data into CloudZero by allowing you to send data from _any_ cost source to the CloudZero REST API.

An [AnyCost Stream Adaptor](https://docs.cloudzero.com/docs/anycost-custom-adaptors) is the code that queries data from the provider, transforms it to fit the required format, and sends the transformed data to CloudZero.

An AnyCost Stream Adaptor typically performs three actions:

1. [Retrieve data from a cloud provider for a billing month.](#step-1-retrieve-cost-data-from-cloud-provider)
2. [Transform the data into the Common Bill Format (CBF).](#step-2-transform-cost-data-to-cbf)
3. [Send the CBF data to the CloudZero API.](#step-3-send-the-cbf-data-to-cloudzero)

You can write an Adaptor in any language, but this example uses Python.

### Step 1: Retrieve Cost Data From Cloud Provider

Your Adaptor should start by retrieving cost data from your cloud provider. Follow your provider's instructions to retrieve the data you need. For example, this could involve sending requests to the provider's APIs to retrieve billing records for one or more accounts, or downloading a CSV of all cost data from the provider.

Because every provider makes its cost data available in a different way, the example Adaptor skips this step. Instead, we've provided you with three CSVs representing the data your Adaptor could retrieve from this step:

- [cloud_usage.csv](./example_cloud_provider_data/cloud_usage.csv): Data related to cloud resource usage
- [cloud_purchase_commitments.csv](./example_cloud_provider_data/cloud_purchase_commitments.csv): Data for discounts related to committed-use contracts
- [cloud_discounts.csv](./example_cloud_provider_data/cloud_discounts.csv): Data for other discounts received

The dummy data is taken from the [CBF example](https://docs.cloudzero.com/docs/anycost-common-bill-format-cbf#examples) in the CloudZero documentation.

### Step 2: Transform Cost Data to CBF

The next step is for the Adaptor to remap the existing cost data to the [Common Bill Format (CBF)](https://docs.cloudzero.com/docs/anycost-common-bill-format-cbf). Conforming to a standard format allows CloudZero to process cost data from any source.

This example Adaptor takes the following actions:

- [Reads the data from each of the three sample CSV files.](#read-each-csv-file)
- [Maps each CSV's data to the appropriate CBF data type.](#map-each-csv-row-to-a-cbf-line-item)
- [Combines the CBF data into a single CSV.](#combine-all-csv-rows)

#### Read Each CSV File

The Adaptor uses the `read_csv()` function to read each of the three example CSV files that contain CBF data. The filenames are hardcoded in the script, so if you modify this script for your own use case, ensure you change the filenames as needed:

- [example_cloud_provider_data/cloud_usage.csv](./example_cloud_provider_data/cloud_usage.csv)
- [example_cloud_provider_data/cloud_purchase_commitments.csv](./example_cloud_provider_data/cloud_purchase_commitments.csv)
- [example_cloud_provider_data/cloud_discounts.csv](./example_cloud_provider_data/cloud_discounts.csv)

#### Map Each CSV Row to a CBF Line Item

Each row within each CSV file represents a single CBF line item. There are multiple [types of line items](https://docs.cloudzero.com/docs/anycost-common-bill-format-cbf#line-item-types), so each line item can represent a charge for usage of a specific resource, a discount for usage of a specific resource, or a charge for a committed use (or savings plan) purchase, for example.

For each row (line item) in a CSV, the Adaptor maps the values to the following [CBF data columns](https://docs.cloudzero.com/docs/anycost-common-bill-format-cbf#data-file-columns):

- `lineitem/type`: The broad category of line item. This example uses the `Usage`, `CommittedUsePurchase`, and `Discount` line item types. [See a full list of supported types.](https://docs.cloudzero.com/docs/anycost-common-bill-format-cbf#line-item-types)
- `resource/service`: The category of resource associated with the line item. This example includes the `Compute` cloud provider service, the `CommittedUse` purchase commitment discount, and two other discounts.
- `resource/id`: The unique ID for the resource associated with the line item.
- `time/usage_start`: The start of the hour during which the line item was charged or applied. Note that the month should be the same for all items in all CSVs, as CloudZero derives the month of usage from this field.
- `cost/cost`: The cost associated with the line item. Negative costs indicate discounts or credits.
- `cost/discounted_cost`: The net cost associated with the line item after discounts or credits have been applied.

After the Adaptor maps each row to the appropriate CBF data types, the row is added to the `cbf_rows` list.

#### Combine All CSV Rows

When the Adaptor has populated the `cbf_rows` list with all of the rows for all of the CSV files, the script writes the `cbf_rows` list to a new CSV file so you can inspect all CBF line items. This file is saved as `cbf/cloud_cbf.csv`, and you can also view it [in this repo](./cbf/cloud_cbf.csv).

### Step 3: Send the CBF Data to CloudZero

The final step is for the Adaptor to send the CBF data to the AnyCost Stream connection using CloudZero's [/v2/connections/billing/anycost/{connection_id}/billing drops](https://docs.cloudzero.com/reference/createoneanycoststreamconnectionbillingdrop) API.

When you run the Adaptor script, it asks you if you want to upload the data to CloudZero. If you enter `y`, the Adaptor uses the [requests](https://requests.readthedocs.io/en/latest/) module to send a POST request with a JSON object containing the CBF rows.

Note that the API requires each element in the `data` object to be a string. This is why there is no need to convert the strings in the `cbf_rows` list to any other type when you send the request to the API.

Additionally, if the `month` parameter is not included in the request body, CloudZero derives the month from the dates in the CBF rows. When you upload your own data, ensure all usage dates are within the same month, as they are in this example.

View the [API Reference](https://docs.cloudzero.com/reference/createoneanycoststreamconnectionbillingdrop) for more detailed information about the endpoint.

## Usage Examples

To use the [anycost_example.py](./anycost_example.py) script to [transform the cost data to CBF](#step-2-transform-cost-data-to-cbf), run the following command:

```
python anycost_example.py
```

The script then optionally uploads the example CBF to an AnyCost Stream connection. To upload the data:

1. Enter `y` at the prompt.
2. Enter your AnyCost Stream connection ID.
3. Enter your CloudZero API key.

The script [sends the example CBF data to CloudZero](#step-3-send-the-cbf-data-to-cloudzero), which processes the first ingest of data.

You can view the data in CloudZero by navigating to [Settings](https://app.cloudzero.com/organization/connections) and selecting your connection from the **Billing Connections** table.

On the connection details page, the **Status** changes from **Pending Data** to **Healthy** after CloudZero has finished processing the data. Note that this can take several hours.

## Contributing

We appreciate feedback and contributions to this repo! Before you get started, see [this repo's contribution guide](CONTRIBUTING.md).

## Support + Feedback

To submit code-level feedback, create a GitHub Issue. Direct all other questions to support@cloudzero.com.

## Vulnerability Reporting

Do not report security vulnerabilities on the public GitHub issue tracker. Email [security@cloudzero.com](mailto:security@cloudzero.com) instead.

## What is CloudZero?

CloudZero is the only cloud cost intelligence platform that puts engineering in control by connecting technical decisions to business results:

- [Cost Allocation And Tagging](https://www.cloudzero.com/tour/allocation): Organize and allocate cloud spend in new ways, increase tagging coverage, or work on showback.
- [Kubernetes Cost Visibility](https://www.cloudzero.com/tour/kubernetes): Understand your Kubernetes spend alongside total spend across containerized and non-containerized environments.
- [FinOps And Financial Reporting](https://www.cloudzero.com/tour/finops): Operationalize reporting on metrics such as cost per customer, COGS, gross margin. Forecast spend, reconcile invoices, and easily investigate variance.
- [Engineering Accountability](https://www.cloudzero.com/tour/engineering): Foster a cost-conscious culture, where engineers understand spend, proactively consider cost, and get immediate feedback with fewer interruptions and faster and more efficient innovation.
- [Optimization And Reducing Waste](https://www.cloudzero.com/tour/optimization): Focus on immediately reducing spend by understanding where we have waste, inefficiencies, and discounting opportunities.

Learn more about [CloudZero](https://www.cloudzero.com/) on our website [www.cloudzero.com](https://www.cloudzero.com/).

## License

This project is licensed under the Apache 2.0 [LICENSE](LICENSE).
