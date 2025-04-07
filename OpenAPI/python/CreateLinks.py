import json
import pandas as pd
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

This script specifically creates the hierarchical links between parent and children objects. 

95% of the script was written in ChatGPT and is good enough :)

Usage:
    python CreateLinks.py youropenapi.json

Note: Run the this script first, so it's output file will be included in the zip file created by ScanOpenAPIJson.py

Requirements:
- Python 3.x
- pandas
- jsonref

Changelog:
- v1.0: Initial release

"""

modelClass = "custom.openapi"

def generate_links_csv(openapi_json_path, output_csv_path):

    # Load the OpenAPI JSON file
    with open(openapi_json_path, 'r', encoding='utf-8') as file:
        openapi_data = jsonref.load(file)

    # Extract the INFO section name
    api_name = openapi_data.get("info", {}).get("title", "UnknownAPI").replace(" ", "~").lower()

    # Initialize list to store all relationships
    relationships = []

    # Add the first entry that links the Resource to the Information Object in the OpenAPI Spec
    relationships.append(["$resource", api_name, "core.ResourceParentChild"])

    # Extract and process tags
    tags = openapi_data.get("tags", [])
    for tag in tags:
        tag_name = tag.get("name", "").lower()
        if tag_name:
            # Create target by prefixing tag name with API name
            prefixed_tag = f"{api_name}~{tag_name}"
            if [api_name, prefixed_tag, modelClass + ".InfoToTag"] not in relationships:
                relationships.append([api_name, prefixed_tag, modelClass + ".InfoToTag"])

    # Fall back if the doc doesn't have a TAGS section, read through the endpoints and grab any tags
    paths_info = openapi_data.get("paths", {})
    for path, methods in paths_info.items():
        for method, details in methods.items():
            tag_name = details.get("tags", [""])[0]  # Get first tag
            prefixed_tag = f"{api_name}~{tag_name}"
            if [api_name, prefixed_tag, modelClass + ".InfoToTag"] not in relationships:
                relationships.append([api_name, prefixed_tag, modelClass + ".InfoToTag"])

    # Process endpoints
    for path, methods in paths_info.items():
        for method, details in methods.items():
            tag_name = details.get("tags", [""])[0]  # Get first tag
            source_path = f"{api_name}~{tag_name}"
            endpoint = api_name + "~" + tag_name + "~" + path.replace("/", "~")
            if [source_path, endpoint, modelClass + ".TagToEndpoint"] not in relationships:
                relationships.append([source_path, endpoint, modelClass + ".TagToEndpoint"])

    # Process Methods
    for path, methods in paths_info.items():
        for method, details in methods.items():
            tag_name = details.get("tags", [""])[0]  # Get first tag
            source_path = f"{api_name}~{tag_name}~" + path.replace("/", "~")
            method_link = source_path + "~" + method
            relationships.append([source_path, method_link, modelClass + ".EndpointToMethod"])

    # Process Response Stubs (adds /response to breadcrumb trail if response(s) exist
    for path, methods in paths_info.items():
        for method, details in methods.items():
            tag_name = details.get("tags", [""])[0]  # Get first tag
            source_path = f"{api_name}~{tag_name}~" + path.replace("/", "~") + "~" + method
            method_link = source_path + "~(responses)"
            relationships.append([source_path, method_link, modelClass + ".MethodToResponseGroup"])

    # Process Responses
    for path, methods in paths_info.items():
        for method, details in methods.items():
            for response in details.get("responses"):
                tag_name = details.get("tags", [""])[0]  # Get first tag
                source_path = f"{api_name}~{tag_name}~" + path.replace("/", "~") + "~" + method + "~(responses)"
                method_link = source_path + "~" + response
                relationships.append([source_path, method_link, modelClass + ".ResponseGroupToResponse"])

    # Process Response Fields
        for path, methods in paths_info.items():
            for method, details in methods.items():
                for response in details.get("responses"):
                    # if schema is attached to response directly
                    if "schema" in details.get("responses")[response]:
                        fieldList = details.get("responses")[response]["schema"]
                        fieldList = flatten_json(fieldList)
                        for field in fieldList:
                            tag_name = details.get("tags", [""])[0]  # Get first tag
                            source_path = f"{api_name}~{tag_name}~" + path.replace("/", "~") + "~" + method + "~(responses)" + "~" + response
                            method_link = source_path + "~" + field
                            relationships.append([source_path, method_link, modelClass + ".ResponseToResponseField"])

                    # if schema is attached to json application type directly (more types are possible, not supported yet)
                    if "content" in details.get("responses")[response]:
                        if "application/json" in details.get("responses")[response]['content']:
                            if "schema" in details.get("responses")[response]['content']["application/json"]:
                                if "properties" in details.get("responses")[response]['content']["application/json"]['schema']:
                                    for field in details.get("responses")[response]['content']["application/json"]['schema']['properties']:
                                        tag_name = details.get("tags", [""])[0]  # Get first tag
                                        source_path = f"{api_name}~{tag_name}~" + path.replace("/","~") + "~" + method + "~(responses)" + "~" + response
                                        method_link = source_path + "~" + field
                                        relationships.append([source_path, method_link, modelClass + ".ResponseToResponseField"])

    # Process Parameter Stubs (adds /parameter to breadcrumb trail if parameters(s) exist
    for path, methods in paths_info.items():
        for method, details in methods.items():
            parameters = details.get("parameters", [])
            for parameter in parameters:
                tag_name = details.get("tags", [""])[0]  # Get first tag
                source_path = f"{api_name}~{tag_name}~" + path.replace("/", "~") + "~" + method
                method_link = source_path + "~(parameters)"
                relationships.append([source_path, method_link, modelClass + ".MethodToParameterGroup"])

    # Process Parameters
    for path, methods in paths_info.items():
        for method, details in methods.items():
            parameters = details.get("parameters", [])
            for parameter in parameters:
                tag_name = details.get("tags", [""])[0]  # Get first tag
                source_path = f"{api_name}~{tag_name}~" + path.replace("/", "~") + "~" + method + "~(parameters)"
                method_link = source_path + "~" + parameter['name']
                relationships.append([source_path, method_link, modelClass + ".ParameterGroupToParameter"])

    # Create DataFrame from all relationships
    df_links = pd.DataFrame(relationships, columns=["Source", "Target", "Association"])

    # Save the CSV file in the provided format
    df_links.to_csv(output_csv_path, index=False)
    print(f"CSV file generated successfully: {output_csv_path}")


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

    parser = argparse.ArgumentParser(description="Process an OpenAPI JSON file to generate a links CSV file.")
    parser.add_argument("json_file", help="Path to the OpenAPI JSON file")

    args = parser.parse_args()

    # Validate the input file exists
    if not os.path.isfile(args.json_file):
        print(f"Error: The file '{args.json_file}' does not exist.")
        exit(1)

    generate_links_csv(args.json_file, "data\links.csv")
