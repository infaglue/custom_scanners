"""
ArgGIS crawler test app

dwrigley
2022/11/09
"""

"""
File: arcgis_scanner.py
Author: Darren Wrigley
Date: November 22, 2022
Version: 1.2

Description:
Process ArcGIS geospatial metadata and load it into CDGC

Usage:
    python arcgis_scanner.py <arcgis_url>

Changelog:
- v1.0: - dwrigley - Initial release
- v1.1: - bshepherd - Fix issue when URL is not provided by the return metadata
- v1.2: - bshepherd - Work with folders, formatted output, added some custom attributes

"""

import requests
import json
from datetime import datetime
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)-5s - %(message)s'
)

from cdgc_writer import CDGCWriter

class ArgGISCrawler:
    max_layers = 0
    max_fields = 0
    total_layers = 0
    total_fields = 0
    total_services = 0

    hawk = CDGCWriter("./out")

    version = "1.2"

    max_services_to_scan = 0

    def __init__(self, limit: int):
        logging.info(f"Initializing ArcGIS scanner arcgis v{self.version}")

        # max_layers = 0
        self.max_services_to_scan = limit
        # self.out_folder = out_folder

    def read_server(self, url: str):
        logging.info(f"read arcgis server url={url}")

        parms = {"f": "pjson"}
        r = requests.get(url, params=parms)
        if r.status_code != 200:
            logging.error(f"error: {r}")
            return

        # assume success
        server_resp = r.text
        try:
            server_obj = json.loads(server_resp)
        except json.decoder.JSONDecodeError:
            logging.error("error processing json result returned from url, exiting")
            return

        logging.info(f"server version: {server_obj.get('currentVersion')}")
        logging.info(f"services: {len(server_obj.get('services'))}")

        try:
            self.server_name = url.split("/")[3]
        except:
            logging.error("Cannot extract server name from 3rd part if url seperated by /, exiting")
            return

        self.hawk.write_server(self.server_name, url)

        self.svcs_to_scan = len(server_obj.get("services"))

        # count = 0
        logging.info(f"Processing Services at Root level")

        for service_obj in server_obj["services"]:
            self.total_services += 1
            self.read_service(service_obj, url, "")
            if self.total_services >= self.max_services_to_scan:
                logging.error(f"max services to scan level hit: {self.max_services_to_scan} ending")
                break

        logging.info(f"Processing any Folders")
        for folder in server_obj["folders"]:

            logging.info(f"Processing Folder : {folder}")
            folderURL = url + "/" + folder
            logging.debug(f"Folder URL: {folderURL}")
            logging.debug(f"read arcgis server url={folderURL}")

            parms = {"f": "pjson"}
            r = requests.get(folderURL, params=parms)
            if r.status_code != 200:
                logging.error(f"error: {r}")
                return

            # assume success
            server_resp = r.text
            try:
                server_obj = json.loads(server_resp)
            except json.decoder.JSONDecodeError:
                logging.error("error processing json result returned from url, exiting")
                return

            self.hawk.write_folder(self.server_name, folder)

            if "services" in server_obj:
                for service_obj in server_obj["services"]:
                    self.total_services += 1
                    self.read_service(service_obj, url, folder)
                    if self.total_services >= self.max_services_to_scan:
                        logging.error(f"max services to scan level hit: {self.max_services_to_scan} ending")
                        break

        logging.info("returning from server read")
        logging.info(f"max layers: {self.max_layers}")
        logging.info(f"max fields: {self.max_fields}")
        logging.info(f"total services: {self.svcs_to_scan} exported={self.hawk.service_count}")
        logging.info(f"total layers: {self.total_layers} exported={self.hawk.layer_count}")
        logging.info(f"total fields: {self.total_fields} exported={self.hawk.field_count}")
        logging.info(f"total folders: {self.hawk.folder_count} exported={self.hawk.folder_count}")

        self.hawk.finalize_scan()

    def read_service(self, service_ref: dict, url: str, folder: str):

        # We only process FeatureServer types, which typically have data fields customers extract data from
        if service_ref["type"] != "FeatureServer":
            return

        logging.info(f"\t- Service: {service_ref['name']}")
        service_name = service_ref["name"]
        # read the service json
        if "url" in service_ref:
            service_url = service_ref["url"]
        else:
            service_url = url + "/" + service_name + "/" + service_ref["type"]

        r = requests.get(service_url, params={"f": "pjson"})
        if r.status_code != 200:
            print(f"error: {r}")
            return

        service_text = r.text
        service_obj = json.loads(service_text)

        self.hawk.write_service(self.server_name, service_ref, service_obj, folder)

        layer_count = len(service_obj["layers"])
        if layer_count > self.max_layers:
            self.max_layers = layer_count

        logging.debug(f"\t- Service {self.total_services}/{self.svcs_to_scan}: {service_name} layers={len(service_obj['layers'])}")

        for layer in service_obj["layers"]:
            self.read_layer(layer, service_url, self.server_name + "/" + service_name)

    def read_layer(self, layer_ref: dict, service_url: str, parent_id: str):

        logging.debug(f"\t- Reading layer: {layer_ref['id']} -- {layer_ref['name']}")
        self.total_layers += 1

        layer_url = service_url + "/" + str(layer_ref["id"])

        r = requests.get(layer_url, params={"f": "pjson"})
        # note 400 here does not go to status code??
        if r.status_code != 200:
            print(f"error: {r}")
            return

        layer_text = r.text
        layer_obj = json.loads(layer_text)

        self.hawk.write_layer(parent_id, layer_obj, layer_url)

        if "fields" in layer_obj:
            field_count = len(layer_obj["fields"])
            for pos, field in enumerate(layer_obj["fields"]):
                self.hawk.write_field(parent_id + "/" + str(layer_obj["id"]), field, pos + 1)
        else:
            field_count = 0
            logging.error(f"\t- Layer has no fields???")

        if "layers" in layer_obj:
            logging.debug(f"\t-Nested layers: {len(layer_obj['layers'])}")
            for sublayer in layer_obj["layers"]:
                if "fields" in sublayer:
                    field_count = len(sublayer["fields"])
                    logging.debug(f"\t- Nested layer fields : {field_count}")
                    for pos, field in enumerate(sublayer["fields"]):
                        self.hawk.write_field(
                            parent_id + "/" + str(layer_obj["id"]), field, pos + 1
                        )

        self.total_fields += field_count

        if field_count > self.max_fields:
            self.max_fields = field_count

        logging.debug(f"\t- Field count={field_count}")

    # end of class def


def main():
    # command-line
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        help="ArcGIS url to scan - e.g. https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=99999,
        help="limit the number of services to scan",
    )
    args = parser.parse_args()

    if args.url == None:
        print("url not specified")
        print(parser.print_help())
        return

    if args.limit <= 0:
        print("limit cannot be 0 or less")
        print(parser.print_help())
        return

    tstart = datetime.now()
    # initialize the scanner object
    arcgis = ArgGISCrawler(args.limit)
    # arcgis.read_server(
    #     "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services"
    # )
    arcgis.read_server(args.url)

    tend = datetime.now()
    logging.info(f"process completed in {(tend - tstart)} ")

if __name__ == "__main__":
    main()
