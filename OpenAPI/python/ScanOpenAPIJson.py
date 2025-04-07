import json
import pandas as pd
import os
import zipfile
import argparse
import os
import jsonref

"""
File: CreateLinks.py
Author: Brian Shepherd
Date: March 11, 2025
Version: 1.0

Description:
This script accepts a OpenAPI specification (formerly known as Swagger), in JSON format, and creates metadata import files to be loaded into CDGC.

This script creates the object files related to OpenAPI assets and generates a new file for each asset type. It then will create a zip file ready to be uploaded to CDGC.

90% of the script was written in ChatGPT and is good enough :)

Usage:
    python CreateLinks.py youropenapi.json

Note: Run the CreateLinks.py script first, so it's output file will be included in the zip file.

Requirements:
- Python 3.x
- pandas
- jsonref

Changelog:
- v1.0: Initial release

"""
modelClass = "custom.openapi"

def extract_info_section(json_file):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    info = data.get("info", {})
    contact = info.get("contact", {})
    license_info = info.get("license", {})

    # Generate core.externalId based on title
    title = info.get("title", "").replace(" ", "~").lower()
    core_external_id = title if title else "unknown_specification"

    petstore_info = {
        "core.externalId": core_external_id,
        "core.name": info.get("title", ""),
        "core.description": info.get("description", ""),
        "core.businessDescription": "",  # Hardcoded to empty
        "core.businessName": "",  # Hardcoded to empty
        modelClass + ".ContactEmail": contact.get("email", ""),
        modelClass + ".ContactName": contact.get("name", ""),
        modelClass + ".ContactURL": contact.get("url", ""),
        modelClass + ".LicenseURL": license_info.get("url", ""),
        modelClass + ".LicenseName": license_info.get("name", ""),
        "core.reference": "",  # Hardcoded to empty
        modelClass + ".termsOfService": info.get("termsOfService", ""),
        modelClass + ".Version": info.get("version", "")
    }

    df = pd.DataFrame([petstore_info])
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, modelClass + ".Info.csv")
    df.to_csv(output_csv, index=False)
    print(f"CSV file created: {output_csv}")

    return core_external_id  # Return the generated core.externalId


def extract_tags_section(json_file, core_external_id):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Check if the doc has a TAGS section
    tags_info = data.get("tags", [])
    tags_data = []
    tag_tracking = []
    for tag in tags_info:
        tag_external_id = f"{core_external_id}~{tag.get('name', '').replace(' ', '~').lower()}"
        tag_entry = {
            "core.externalId": tag_external_id,
            "core.name": tag.get("name", ""),
            "core.description": tag.get("description", ""),
            "core.businessDescription": "",  # Hardcoded to empty
            "core.businessName": "",  # Hardcoded to empty
            "core.reference": ""  # Hardcoded to empty
        }
        if tag_external_id not in tag_tracking:
            tag_tracking.append(tag_external_id)
            tags_data.append(tag_entry)

    # Fall back if the doc doesn't have a TAGS section, read thru the end points and grab any tags
    paths_info = data.get("paths", {})
    for path, methods in paths_info.items():
        for method, details in methods.items():
            tag_name = details.get("tags", [""])[0]  # Get first tag
            tag_external_id = f"{core_external_id}~{tag_name}"
            tag_entry = {
                "core.externalId": tag_external_id,
                "core.name": tag_name,
                "core.description": "",
                "core.businessDescription": "",  # Hardcoded to empty
                "core.businessName": "",  # Hardcoded to empty
                "core.reference": ""  # Hardcoded to empty
            }
            if tag_external_id not in tag_tracking:
                tag_tracking.append(tag_external_id)
                tags_data.append(tag_entry)

    df = pd.DataFrame(tags_data)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, modelClass + ".Tag.csv")
    df.to_csv(output_csv, index=False)
    print(f"CSV file created: {output_csv}")


def extract_endpoints_section(json_file, core_external_id):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    paths_info = data.get("paths", {})
    endpoints_data = []
    for path, methods in paths_info.items():
        for method, details in methods.items():
            tag_name = details.get("tags", [""])[0]  # Get first tag
            endpoint_external_id = f"{core_external_id}~" + tag_name + "~" + path.replace("/", "~")
            endpoint_entry = {
                "core.externalId": endpoint_external_id,
                "core.name": path,
                "core.description": "", # Description is left for the method, so we keep it empty for now,
                "core.businessDescription": "",  # Hardcoded to empty
                "core.businessName": "",  # Hardcoded to empty
                "core.reference": ""  # Hardcoded to empty
            }
            if endpoint_entry not in endpoints_data:
                endpoints_data.append(endpoint_entry)

    df = pd.DataFrame(endpoints_data)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, modelClass + ".Endpoint.csv")
    df.to_csv(output_csv, index=False)
    print(f"CSV file created: {output_csv}")


def extract_methods_section(json_file, core_external_id):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    paths_info = data.get("paths", {})
    endpoints_data = []

    for path, methods in paths_info.items():
        for method, details in methods.items():
            tag_name = details.get("tags", [""])[0]  # Get first tag
            endpoint_external_id = f"{core_external_id}~" + tag_name + "~" + path.replace("/", "~") + "~" + method.lower()
            endpoint_entry = {
                "core.externalId": endpoint_external_id,
                "core.name": method.upper(),
                "core.description": details.get("description"), # Description is left for the method, so we keep it empty for now,
                "core.businessDescription": "",  # Hardcoded to empty
                "core.businessName": "",  # Hardcoded to empty
                "core.reference": ""  # Hardcoded to empty
            }

            if endpoint_entry not in endpoints_data:
                endpoints_data.append(endpoint_entry)

    df = pd.DataFrame(endpoints_data)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, modelClass + ".Method.csv")
    df.to_csv(output_csv, index=False)
    print(f"CSV file created: {output_csv}")


def create_response_stubs(json_file, core_external_id):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    paths_info = data.get("paths", {})
    response_data = []
    for path, methods in paths_info.items():
        for method, details in methods.items():
            tag_name = details.get("tags", [""])[0]  # Get first tag
            external_id = f"{core_external_id}~" + tag_name + "~" + path.replace("/", "~") + "~" + method.lower() + "~(responses)"
            endpoint_entry = {
                "core.externalId": external_id,
                "core.name": "(responses)",
                "core.description": "The responses used by this API endpoint",
                "core.businessDescription": "",  # Hardcoded to empty
                "core.businessName": "",  # Hardcoded to empty
                "core.reference": ""  # Hardcoded to empty
            }

            if endpoint_entry not in response_data:
                response_data.append(endpoint_entry)

    df = pd.DataFrame(response_data)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, modelClass + ".ResponseGroup.csv")
    df.to_csv(output_csv, index=False)
    print(f"CSV file created: {output_csv}")


def create_responses(json_file, core_external_id):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    paths_info = data.get("paths", {})
    response_data = []
    for path, methods in paths_info.items():
        for method, details in methods.items():
            for response in details.get("responses"):
                tag_name = details.get("tags", [""])[0]  # Get first tag
                external_id = f"{core_external_id}~" + tag_name + "~" + path.replace("/","~") + "~" + method.lower() + "~(responses)" + "~" + response
                endpoint_entry = {
                    "core.externalId": external_id,
                    "core.name": response,
                    "core.description": details.get("responses")[response]['description'],
                    "core.businessDescription": "",  # Hardcoded to empty
                    "core.businessName": "",  # Hardcoded to empty
                    "core.reference": ""  # Hardcoded to empty
                }

                if endpoint_entry not in response_data:
                    response_data.append(endpoint_entry)

    df = pd.DataFrame(response_data)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, modelClass + ".Response.csv")
    df.to_csv(output_csv, index=False)
    print(f"CSV file created: {output_csv}")


def create_response_fields(json_file, core_external_id):
    with open(json_file, "r", encoding="utf-8") as file:
        data = jsonref.load(file)

    paths_info = data.get("paths", {})
    response_data = []
    for path, methods in paths_info.items():
        for method, details in methods.items():
            for response in details.get("responses"):
                if details.get("responses")[response]:

                    # Check if schema is attached directly on responses.
                    # It can be attached in different ways
                    if "schema" in details.get("responses")[response]:
                        fieldList = details.get("responses")[response]["schema"]

                        # this try was put into place
                        try:
                            if "allOf" in fieldList:
                                fieldList = fieldList["allOf"][0]["properties"]
                        except KeyError:
                            print(fieldList)


                        fieldList = flatten_json(fieldList)

                        for field in fieldList:
                            tag_name = details.get("tags", [""])[0]  # Get first tag

                            external_id = f"{core_external_id}~" + tag_name + "~" + path.replace("/","~") + "~" + method.lower() + "~(responses)" + "~" + response + "~" + field
                            endpoint_entry = {
                                "core.externalId": external_id,
                                "core.name": field,
                                "core.description": "",
                                "core.businessDescription": "",  # Hardcoded to empty
                                "core.businessName": "",  # Hardcoded to empty
                                "core.reference": "",  # Hardcoded to empty
                                "custom.openapi.v6.Default": details.get("default"),  # Hardcoded to empty
                                "custom.openapi.v6.Example": details.get("example"),  # Hardcoded to empty
                                "custom.openapi.v6.Format": details.get("format"),  # Hardcoded to empty
                                "custom.openapi.v6.Type": details.get("type"),  # Hardcoded to empty
                            }

                            if endpoint_entry not in response_data:
                                response_data.append(endpoint_entry)

                    # Check if schema is attached to content/json path
                    if "content" in details.get("responses")[response]:
                        if "application/json" in details.get("responses")[response]['content']:
                            if "schema" in details.get("responses")[response]['content']["application/json"]:
                                if "properties" in details.get("responses")[response]['content']["application/json"]['schema']:
                                    fieldList = details.get("responses")[response]['content']["application/json"]['schema']['properties']
                                    fieldList = flatten_json(fieldList)

                                    for field in fieldList:
                                        tag_name = details.get("tags", [""])[0]  # Get first tag
                                        external_id = f"{core_external_id}~" + tag_name + "~" + path.replace("/","~") + "~" + method.lower() + "~(responses)" + "~" + response + "~" + field

                                        cType = ""
                                        cFormat = ""
                                        cExample = ""
                                        cDefault = ""

                                        if "->" not in field and field != '':
                                            if details.get("responses")[response]['content']["application/json"]['schema']['properties'][field]['type']:
                                                cType = details.get("responses")[response]['content']["application/json"]['schema']['properties'][field]['type']
                                            if "format" in details.get("responses")[response]['content']["application/json"]['schema']['properties'][field]:
                                                cFormat = details.get("responses")[response]['content']["application/json"]['schema']['properties'][field]['format']
                                            if "example" in details.get("responses")[response]['content']["application/json"]['schema']['properties'][field]:
                                                cExample = details.get("responses")[response]['content']["application/json"]['schema']['properties'][field]['example']
                                            if "default" in details.get("responses")[response]['content']["application/json"]['schema']['properties'][field]:
                                                cDefault = details.get("responses")[response]['content']["application/json"]['schema']['properties'][field]['default']


                                        endpoint_entry = {
                                            "core.externalId": external_id,
                                            "core.name": field,
                                            "core.description": "",
                                            "core.businessDescription": "",  # Hardcoded to empty
                                            "core.businessName": "",  # Hardcoded to empty
                                            "core.reference": "",  # Hardcoded to empty
                                            "custom.openapi.v6.Default": cDefault,# Hardcoded to empty
                                            "custom.openapi.v6.Example": cExample,# Hardcoded to empty
                                            "custom.openapi.v6.Format": cFormat, # Hardcoded to empty
                                            "custom.openapi.v6.Type": cType,  # Hardcoded to empty
                                        }

                                        if endpoint_entry not in response_data:
                                            response_data.append(endpoint_entry)

    df = pd.DataFrame(response_data)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, modelClass + ".ResponseField.csv")
    df.to_csv(output_csv, index=False)
    print(f"CSV file created: {output_csv}")


def create_parameter_stubs(json_file, core_external_id):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    paths_info = data.get("paths", {})
    response_data = []
    for path, methods in paths_info.items():
        for method, details in methods.items():
            parameters = details.get("parameters", [])
            if parameters:
                tag_name = details.get("tags", [""])[0]  # Get first tag
                external_id = f"{core_external_id}~" + tag_name + "~" + path.replace("/", "~") + "~" + method.lower() + "~(parameters)"
                endpoint_entry = {
                    "core.externalId": external_id,
                    "core.name": "(parameters)",
                    "core.description": "The parameters used by this API endpoint",
                    "core.businessDescription": "",  # Hardcoded to empty
                    "core.businessName": "",  # Hardcoded to empty
                    "core.reference": ""  # Hardcoded to empty
                }

                if endpoint_entry not in response_data:
                    response_data.append(endpoint_entry)

    df = pd.DataFrame(response_data)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, modelClass + ".ParameterGroup.csv")
    df.to_csv(output_csv, index=False)
    print(f"CSV file created: {output_csv}")


def create_parameters(json_file, core_external_id):
    with open(json_file, "r", encoding="utf-8") as file:
        data = jsonref.load(file)

    paths_info = data.get("paths", {})
    parameter_data = []
    for path, methods in paths_info.items():
        for method, details in methods.items():
            parameters = details.get("parameters", [])
            if parameters:
                for parameter in parameters:
                    tag_name = details.get("tags", [""])[0]  # Get first tag
                    external_id = f"{core_external_id}~" + tag_name + "~" + path.replace("/","~") + "~" + method.lower() + "~(parameters)" + "~" + parameter['name']
                    if "description" in parameter:
                        description = parameter["description"]
                    else:
                        description = ""

                    endpoint_entry = {
                        "core.externalId": external_id,
                        "core.name": parameter['name'],
                        "core.description": description,
                        "core.businessDescription": "",  # Hardcoded to empty
                        "core.businessName": "",  # Hardcoded to empty
                        "core.reference": ""  # Hardcoded to empty
                    }

                    if endpoint_entry not in parameter_data:
                        parameter_data.append(endpoint_entry)

    df = pd.DataFrame(parameter_data)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, modelClass + ".Parameter.csv")
    df.to_csv(output_csv, index=False)
    print(f"CSV file created: {output_csv}")


def create_zip_file(json_file):
    base_name = os.path.splitext(os.path.basename(json_file))[0]
    zip_filename = f"{base_name}.zip"

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, _, files in os.walk("data"):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)
    print(f"ZIP file created: {zip_filename}")


def flatten_json(json_obj, parent_key='', sep='->'):
    """
    Recursively flattens a nested JSON object while filtering out keys named 'example'.
    """
    flattened_dict = {}

    def recursive_flatten(obj, parent_key):
        if isinstance(obj, dict):
            for key, value in obj.items():
                badKeys = ['example', 'format', 'enum', 'xml', 'description']
                if key in badKeys:
                    continue
                new_key = f"{parent_key}{sep}{key}" if parent_key else key
                if key == 'type':
                    new_key = parent_key
                if key == 'properties':
                    new_key = parent_key
                recursive_flatten(value, new_key)
        else:
            flattened_dict[parent_key] = obj

    recursive_flatten(json_obj, parent_key)
    return flattened_dict


if __name__ == "__main__":

    # Ensure 'data' directory exists
    os.makedirs('data', exist_ok=True)

    parser = argparse.ArgumentParser(description="Process an OpenAPI JSON file to generate output files.")
    parser.add_argument("json_file", help="Path to the OpenAPI JSON file")

    args = parser.parse_args()

    core_external_id = extract_info_section(args.json_file)
    extract_tags_section(args.json_file, core_external_id)
    extract_endpoints_section(args.json_file, core_external_id)
    extract_methods_section(args.json_file, core_external_id)

    create_parameter_stubs(args.json_file, core_external_id)
    create_parameters(args.json_file, core_external_id)

    create_response_stubs(args.json_file, core_external_id)
    create_responses(args.json_file, core_external_id)
    create_response_fields(args.json_file, core_external_id)

    create_zip_file(args.json_file)
