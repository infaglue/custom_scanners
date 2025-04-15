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