clear
pyinstaller --noconfirm --log-level=ERROR \
    --clean \
    --onefile \
    --windowed \
    --debug imports \
    --name FotoPDF \
    --paths ~/PycharmProjects/FotoPDF/venv/lib/python3.9/site-packages/ \
    --paths ~/PycharmProjects/FotoPDF/venv/ \
    --add-data font_default.ttf:. \
    --add-data FotoPDF.png:. \
    --icon FotoPDF.png \
    main.py
