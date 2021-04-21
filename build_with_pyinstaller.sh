clear
rm -rf build dist
pyinstaller --noconfirm --log-level=ERROR \
    --clean \
    --onefile \
    --windowed \
    --name FotoPDF \
    --debug imports \
    --paths ~/PycharmProjects/FotoPDF/venv2/ \
    --paths ~/PycharmProjects/FotoPDF/venv2/lib/python3.9/site-packages/ \
    --paths ~/PycharmProjects/FotoPDF/venv2/lib/python3.9/site-packages/PyQt5/ \
    --add-data font_default.ttf:. \
    --add-data FotoPDF.png:. \
    --icon FotoPDF.png \
    --hidden-import PyQt5 \
    --hidden-import PyQt5.sip \
    --hidden-import PyQt5.QtWidgets \
    --hidden-import PyQt5.QtGui \
    --hidden-import PyQt5.QtCore \
    simple.py
