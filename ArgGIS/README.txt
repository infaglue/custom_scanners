******************************************************************************
*
*                   ArcGIS Custom Scanner for CDGC
*
******************************************************************************

v1.3 - April 10, 2025
==================================
** FIXED:
    - Fixed URLs with Links that are generated for descriptions
    - Fixed URLS not using https
    - Removed developer comments

** NEW:
    - Add many new attributes to Services, Layers and Fields.
    - Support for MapServer service.

** UPDATES:
    - Model updated to move Service objects to specific objects within ArcGis (FeatureServer, MapServer, etc).
    - Rewrote file handing of cdgc_writer. Cleaner and easier to add attributes.
    - Model package name was renamed to remove the version number in the classes.


v1.2 - April 8, 2025
==================================
** FIXED:
    - Fixed another issue with ArcGIS URLS when they are missing from the JSON documents.

** NEW:
    - Replaced print statements to use logging library. Moved some output to debug level.
    - Add folder support. Folders will parsed for services. Both folder and the asset hierarchy are cataloged.

** UPDATES:
    - Model updated to include Folder Classification plus associations to Server and Services.



v1.1 - MARCH 1, 2025
==================================
** FIXED:
    - Fixed issue with ArcGIS URLS when they are missing from the JSON documents.



v1 - NOVEMBER 14, 2022
==================================
** NEW:
    - Created.

******************************************************************************
*
*                   How to Install and Use
*
******************************************************************************

** Setup:

    1. Download the two python files and the "arcgis_custom_model.json" model file from this repository
    2. In Metadata Command Center (MCC), create a new model using the model file provided here:
            - In MCC > Customize Menu -> Metadata Models
            - Click "+" plus button towards right hand side
            - Upload the Model Json file
            - Provide "esri.arcgis.custom" for the Package Name setting. Click Create
            - Once uploaded, click Publish in the upper right.
            - Publish can take 5 to 10 minutes
    3. Stay in MCC and create a Custom Catalog Source Type:
            - In MCC -> Customize Menu -> Create Custom Catalog Source Types menu
            - Click "+" plus button towards right hand side
            - Give it the name of your new scanner. E.g. "Esri ArcGIS" and provide a description
            - Now, when you go to New -> Catalog Source, this new Source will show up at the bottom of the list, just like other scanners.
    4. Install Python 3. Following the instructions for your OS
    5. Install any necessary python packages. The scripts use: requests, json, datetime, argparse, logging, os, csv, zipfile, pd
            - Most of these are installed with Python, except for pd in some cases.


** Executing Python Script:

    1. The python script will generate the necessary CSV and ZIP files of metadata that is uploaded to CDGC.
    2. Typically, execution is : "python arggis_scanner.py <your rest api url>"
    3. The ArcGIS Rest API is typically something like this : https://caltrans-gis.dot.ca.gov/arcgis/rest/services
            - This is the URL that is expected. The script will not work (most likely) if you start at a object lower in the hierarchy
            - The script will parse thru Folders looking for Feature and Map Servers. It will skip other services most customers don't need to catalog them
            - The script will drill down to layers, but does have a limit to the number of layers it will catalog per service.
    4. After your execute the python script, an /out directory is created with the CSV files and more importantly the ZIP file that CDGC needs.

 ** Loading Metadata into CDGC

    1. Once the ZIP file is created, it's time to load the metadata into the catalog.
    2. In MCC -> Click New -> Catalog Source and pick the new Source Type you created in the Setup section
    3. In the first section, make sure CSV files is selected and for testing, choose the option to upload the zip file.
    4. Upload the zip file
    5. Do any other standard scanner configuration (Glossary, Classification, etc) and save and execute.
    6. In a production setting, you'd want have the scanner setup to look for the zip file on a secure agent of your choosing, this way the entire process can be scheduled and automated.
