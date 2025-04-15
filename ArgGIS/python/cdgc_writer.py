import os
import csv
import zipfile
import logging
import pandas as pd

# import urllib.parse
logger = logging.getLogger(__name__)

class CDGCWriter:

    PACKAGE = "esri.arcgis.custom"

    SERVER_CLASS = f"{PACKAGE}.Server"
    FEATURESERVER_CLASS = f"{PACKAGE}.FeatureServer"
    MAPSERVER_CLASS = f"{PACKAGE}.MapServer"
    LAYER_CLASS = f"{PACKAGE}.Layer"
    FIELD_CLASS = f"{PACKAGE}.Field"
    FOLDER_CLASS = f"{PACKAGE}.Folder"

    LAYER_FIELD_LINK = f"{PACKAGE}.LayerContainsField"
    SERVER_FOLDER_LINK = f"{PACKAGE}.ServerToFolder"
    ZIPFILE_NAME = "arcgis_custom_metadata_cdgc.zip"

    # because we have many services, these links are incomplete and will be finished when needed
    SERVER_SERVICE_LINK = f"{PACKAGE}.ServerContains"
    FOLDER_SERVICE_LINK = f"{PACKAGE}.FolderTo"
    SERVICE_LAYER_LINK_START = f"{PACKAGE}."
    SERVICE_LAYER_LINK_END = f"ContainsLayer"

    hostname = ""
    output_folder = "./out"

    folderList = []
    layerList = []
    serverList = []
    fieldList = []

    featureServerList = []
    mapServerList = []

    service_count = 0
    layer_count = 0
    field_count = 0
    folder_count = 0

    def __init__(self, output_folder: str):

        self.output_folder = output_folder
        self.init_files()

    def init_files(self):

        logger.info(f"Initializing Output Files - folder {self.output_folder}")
        if not os.path.exists(self.output_folder):
            logger.info(f"Creating Folder {self.output_folder}")
            os.makedirs(self.output_folder)

        self.fLinks = open(
            f"{self.output_folder}/links.csv",
            "w",
            newline="",
            encoding="utf8",
        )
        self.linkWriter = csv.writer(self.fLinks)
        self.linkWriter.writerow(["Source", "Target", "Association"])


    def create_output_file(self, itemArray, filename):

        df = pd.DataFrame(itemArray)
        os.makedirs(self.output_folder, exist_ok=True)

        output_csv = os.path.join(self.output_folder, filename)
        df.to_csv(output_csv, index=False)


    def finalize_scan(self):

        self.fLinks.close()

        self.create_output_file(self.folderList, f"{self.FOLDER_CLASS}.csv")
        self.create_output_file(self.featureServerList, f"{self.FEATURESERVER_CLASS}.csv")
        self.create_output_file(self.mapServerList, f"{self.MAPSERVER_CLASS}.csv")
        self.create_output_file(self.layerList, f"{self.LAYER_CLASS}.csv")
        self.create_output_file(self.serverList, f"{self.SERVER_CLASS}.csv")
        self.create_output_file(self.fieldList, f"{self.FIELD_CLASS}.csv")

        # write to zip file
        zFileName = f"{self.output_folder}/{self.ZIPFILE_NAME}"
        logging.info(f"Creating Zipfile: {zFileName}")
        zipf = zipfile.ZipFile(
            f"{zFileName}", mode="w", compression=zipfile.ZIP_DEFLATED
        )
        zipf.write(
            f"{self.output_folder}/links.csv",
            f"links.csv",
        )
        zipf.write(
            f"{self.output_folder}/{self.SERVER_CLASS}.csv",
            f"{self.SERVER_CLASS}.csv",
        )
        zipf.write(
            f"{self.output_folder}/{self.FEATURESERVER_CLASS}.csv",
            f"{self.FEATURESERVER_CLASS}.csv",
        )
        zipf.write(
            f"{self.output_folder}/{self.MAPSERVER_CLASS}.csv",
            f"{self.MAPSERVER_CLASS}.csv",
        )
        zipf.write(
            f"{self.output_folder}/{self.LAYER_CLASS}.csv",
            f"{self.LAYER_CLASS}.csv",
        )
        zipf.write(
            f"{self.output_folder}/{self.FIELD_CLASS}.csv",
            f"{self.FIELD_CLASS}.csv",
        )
        zipf.write(
            f"{self.output_folder}/{self.FOLDER_CLASS}.csv",
            f"{self.FOLDER_CLASS}.csv",
        )
        zipf.close()


    def write_server(self, id: str, url: str):

        serverItem = {
            "core.externalId": id,
            "core.name" : id,
            "core.description": url,
            "core.businessDescription": "",
            "core.businessName": "",
            "core.reference": "FALSE"
        }

        self.serverList.append(serverItem)
        self.linkWriter.writerow(["$resource", id, "core.ResourceParentChild"])


    def write_folder(self, parent_id: str, folder: dict):

        self.folder_count += 1
        objectID = f"{parent_id}/{folder}"

        folderItem = {
            "core.externalId": objectID,
            "core.name": folder,
            "core.description": "",
            "core.businessDescription": "",
            "core.businessName": "",
            "core.reference": "FALSE"
        }

        self.folderList.append(folderItem)
        self.linkWriter.writerow([parent_id, objectID, self.SERVER_FOLDER_LINK])


    def write_service(self, parent_id: str, service_ref: dict, service_data: dict, folder: str, url: str):

        self.service_count += 1
        service_name = service_ref["name"]
        objectID = f"{parent_id}/{service_name}"

        service_url = url + "/" + service_name + "/" + service_ref["type"]

        url_link = f"<a href=\"{service_url}\">ArcGIS REST Services Directory Link</a>"

        map_link = f"<a href=\"https://www.arcgis.com/apps/mapviewer/index.html?url={service_url}&source=sd\">ArcGIS Map Link</a>"
        query_link = f"<a href=\"{service_url}/query\">ArcGIS Query Link</a"

        desc_attr = url_link + "<br/>" + map_link + "<br/>" + query_link

        serviceItem = {
            "core.externalId": objectID,
            "core.name": service_name,
            "core.description": desc_attr,
            "core.businessDescription": "",
            "core.businessName": "",
            "core.reference": "FALSE",
            f"{self.PACKAGE}.Copyright": service_data.get("copyrightText", ""),
            f"{self.PACKAGE}.HasVersionedData": service_data.get("hasVersionedData", ""),
            f"{self.PACKAGE}.MaxRecordCount": service_data.get("maxRecordCount", ""),
            f"{self.PACKAGE}.hasArchivedData": service_data.get("hasArchivedData", ""),
            f"{self.PACKAGE}.supportedQueryFormats": service_data.get("supportedQueryFormats", ""),
            f"{self.PACKAGE}.supportsQueryDataElements": service_data.get("supportsQueryDataElements", ""),
            f"{self.PACKAGE}.type": "",
            f"{self.PACKAGE}.units": service_data.get("units", ""),
            "core.technicalDescription" : service_data.get("description", ""),
            f"{self.PACKAGE}.restServicesLink": "",
        }

        if service_ref.get("type") == "FeatureServer":
            self.featureServerList.append(serviceItem)

        if service_ref.get("type") == "MapServer":
            self.mapServerList.append(serviceItem)

        # Some services are in the root folder, some in subfolder, we need to adjust the link
        if folder:
            parentObject = f"{parent_id}/{folder}"
            link = f"{self.FOLDER_SERVICE_LINK}{service_ref.get('type')}"
        else:
            parentObject = parent_id
            link = f"{self.SERVER_SERVICE_LINK}{service_ref.get('type')}"

        self.linkWriter.writerow([parentObject, objectID, link])


    def write_layer(self, parent_id: str, layer_data: dict, url: str, serviceType: str):

        self.layer_count += 1

        if "id" not in layer_data:
            logger.error(f"no id?? {layer_data}")
        objectID = f"{parent_id}/{layer_data['id']}"

        # format url links to ArcGis
        url_link = f'<a href="{url}">ArcGIS REST Services Directory Link</a>'
        map_link = f'<a href="https://www.arcgis.com/apps/mapviewer/index.html?url={url}&source=sd">ArcGIS Map Link</a>'

        desc_attr = f"Layer id: {layer_data['id']}<br/>{url_link}<br/>{map_link}"

        layerItem = {
            "core.externalId": objectID,
            "core.name": layer_data["name"],
            "core.description": desc_attr,
            "core.businessDescription": "",
            "core.businessName": "",
            "core.reference": "FALSE",
            f"{self.PACKAGE}.Copyright": layer_data.get("copyrightText", ""),
            f"{self.PACKAGE}.geometryType": layer_data.get("geometryType", ""),
            f"{self.PACKAGE}.hasArchivedData": layer_data.get("isDataArchived", ""),
            f"{self.PACKAGE}.MaxRecordCount": layer_data.get("maxRecordCount", ""),
            f"{self.PACKAGE}.supportedQueryFormats": layer_data.get("supportedQueryFormats", ""),
            f"{self.PACKAGE}.supportsAdvancedQueries": layer_data.get("supportsAdvancedQueries", ""),
            f"{self.PACKAGE}.supportsStatistics": layer_data.get("supportsStatistics", ""),
            f"{self.PACKAGE}.Type": layer_data.get("type", ""),
            "core.technicalDescription": layer_data.get("description", "")
        }

        self.layerList.append(layerItem)
        self.linkWriter.writerow([parent_id, objectID, f"{self.SERVICE_LAYER_LINK_START}{serviceType}{self.SERVICE_LAYER_LINK_END}"])


    def write_field(self, parent_id: str, field_data: dict, position: int):

        self.field_count += 1
        objectID = f"{parent_id}/{field_data['name']}"

        fieldItem = {
            "core.externalId": objectID,
            "core.name": field_data.get("name", ""),
            "core.description": "",
            "core.businessDescription": "",
            "core.businessName": "",
            "core.reference": "FALSE",
            "esri.arcgis.custom.Type": field_data.get("type", ""),
            "esri.arcgis.custom.alias": field_data.get("alias", ""),
            "esri.arcgis.custom.defaultValue": field_data.get("defaultValue", ""),
            "esri.arcgis.custom.domain": field_data.get("domain", ""),
            "esri.arcgis.custom.editable": field_data.get("editable", ""),
            "esri.arcgis.custom.modelName": field_data.get("modelName", ""),
            "esri.arcgis.custom.nullable": field_data.get("nullable", ""),
            "core.Position": position
        }

        self.fieldList.append(fieldItem)
        self.linkWriter.writerow([parent_id, objectID, self.LAYER_FIELD_LINK])
