# FotoPDF

## GUI
<img src="docs/app_image.png" alt="The app" title="The app" width="200" />

It can be run as python script

    python FotoPDF
    
or built as an app (see below)

Drag and drop the folder containing the images and `settings.json` on the application window. Images will be included in alphabetical order. Dropping any file from that folder has the same effect. Only the folder is considered.


## Command line (you'll need to set the flag GUI to False)
As Python script:

    python FotoPDF <folder-where-images-and-settings.json-are>
    
As executable:

    ./FotoPDF <folder-where-images-and-settings.json-are>
    
## Settings (settings.json)
This file is specific to the PDF to generate and must be placed in the same folder where the images are.

If no settings.json is found, a default one will be created. You will the have to customize it as necessary.

## Building the app
The lightest app (42.3MB) can be created with pyinstaller. Just run:
```
./build_with_pyinstaller_3_6_5.sh
```
and the app will be located in `dist/FotoPDF`.

Alternatively, you can also use py2app (the script uses `setup.py`):
```
./build_with_py2app.sh
```
but the size of the app will be considerably larger (around 160MB).

Note: the reason why I used PySide2 instead of PyQt5 is because Pyinstaller could not build a functioning app. There's a [stackoverflow discussion](https://stackoverflow.com/questions/67057304/pyinstaller-on-macos-bigsur-cannot-build-basic-pyqt5-app/67292307#67292307) about this.

## To do
### Oversaturated colors when the PDF is opened with MacOS Preview
I'm using reportlab to generate the pdf. Sometimes, the images of the pdf that is generated have saturated colors when opened with MacOS Preview.

They are fine when looked in the Finder thumbnail or opened with other SW like, say, Google Chrome. It's clearly a MacOS Preview limitation but unfortunately that's the viewer most photoeditors use.

I tried with images in color space RGB and two different colour profiles:
- sRGB: images are oversaturated
- AdobeRGB1998: images are treated fine

I could not find a way to solve this in reportlab. Also interesting: if I open the file gerenated with Reportlab with MacOS Preview and export it as pdf, all colours are "fixed".

I also tried using pypdf2 to open, parse page by page and resave the document but it has no effect.
