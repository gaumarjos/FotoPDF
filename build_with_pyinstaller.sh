clear
rm -rf build dist
pyinstaller --noconfirm --log-level=ERROR \
    --clean \
    --onefile \
    --windowed \
    --name FotoPDF \
    --debug all \
    --paths ~/PycharmProjects/FotoPDF/venv2/lib/python3.9/site-packages/ \
    --paths ~/PycharmProjects/FotoPDF/venv2/ \
    --add-data font_default.ttf:. \
    --add-data FotoPDF.png:. \
    --icon FotoPDF.png \
    FotoPDF.py
