clear
rm -rf build dist
pyinstaller --noconfirm --log-level=ERROR \
    --clean \
    --onefile \
    --windowed \
    --name FotoPDF \
    --debug imports \
    --paths ~/PycharmProjects/FotoPDF/venv/lib/python3.9/site-packages/ \
    --add-data font_default.ttf:. \
    --add-data FotoPDF.png:. \
    --icon FotoPDF.png \
    --hidden-import PyQt5 \
    --hidden-import PyQt5.sip \
    --hidden-import PyQt5.QtWidgets \
    --hidden-import PyQt5.QtGui \
    --hidden-import PyQt5.QtCore \
    FotoPDF.py
