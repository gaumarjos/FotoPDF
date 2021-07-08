# FotoPDF

This app allows to create a presentation PDF from a bunch of images.

<center><img src="docs/app_image.png" alt="The app" title="The app" width="200" /></center>

The presentation has the traditional structure:
1. Cover
2. Text page with a description of the project
3. Full-page images with captions. Captions are read directly from the images' ImageDescription field, "Caption" in Adobe Lightroom.
4. Grid page
5. Final page with contacts.

The expected workflow is:
1. Export images from any software (i.e. Adobe Lightroom, Capture One, etc...) in a folder. Images must be in JPG format. The color space is irrelevant as it will be kept in the PDF. When exporting, remember to export images with all metadata, otherwise captions might not be exported and FotoPDF cannot read them.
2. FotoPDF requires a `settings.json` to know how to draw the presentation. If that's not available in the folder the first time FotoPDF is launched, a default empty one will be created. You will then have to customize it as you wish and drag the folder on the app again.
    * Double click on the app
    * If you're familiar with python, `python FotoPDF` 
4. Open FotoPDF and drag the folder on the app. Images will be included in alphabetical order.
5. Done! A PDF is created in the same folder.

## Settings (settings.json)
`settings.json` can be edited with any text editor and fields should self-explanatory. The name of the file is unimportant provided the extension is `.json`.

If the folder contains multiple json files, it is assumed that the user wants multiple versions of the PDF. For example in different languages.

### Multilanguage support

#### Multiple setting files and multiple captions (how it should be)
If the settings files starts with the same name and have suffixes that look like languages, i.e. `settings it.json` and `settings en.json`, the software will look for tags like `#it` and `#en` in the image captions and, if found, will use the corresponding one.

Example of a caption with multilanguage support: `#it Questa è una didascalia. #en This is a caption.`.

#### Multiple setting files but only one caption
The software uses that caption for all settings.

#### One setting file but multilanguage captions
If the setting file has an ending that looks like a language specifier, then the corresponding caption is found. If the setting file has no particular ending, the first caption will be used.

## Run from command line
To be honest, it makes little sense because the time you'll save is minimal but if you really want to, just set the flag GUI to False in the source code and run `python FotoPDF <folder-where-images-and-settings.json-are>`

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

I could not find a way to solve this in reportlab. Also interesting: if I open the file generated with Reportlab with MacOS Preview and export it as pdf, all colours are "fixed".

I also tried using pypdf2 to open, parse page by page and resave the document but it has no effect.
