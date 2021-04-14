# FotoPDF

## GUI (default)
<img src="docs/app_image.png" alt="The app" title="The app" width="200" />

Drag and drop the folder containing the images and `settings.json` on the application window. Images will be included in alphabetical order.

Dropping any file from that folder has the same effect. Only the folder is considered.


## Command line (you'll need to set the flag GUI to False)
As Python script:

    python3 FotoPDF <folder-where-images-and-settings.json-are>
    
As executable:

    ./FotoPDF <folder-where-images-and-settings.json-are>
    
## Settings (settings.json)
This file is specific to the PDF to generate and must be placed in the same folder where the images are.

If no settings.json is found, a default one will be created. You will the have to customize it as necessary.

## Building the app
The app can be built with py2app (the script uses `setup.py`):
```
./build_with_py2app.sh
```
and the app will be located in `dist/FotoPDF`.

Configuration files for Pyinstaller (`build_with_py2app.sh`) and Pyoxidizer (`pyoxidizer.bzl`) are also available. I was not able to build the app with them on BigSur, though.
