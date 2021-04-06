clear
rm -rf build dist
pyinstaller --noconfirm --log-level=ERROR \
    --onefile \
    --windowed \
    --name FotoPDF \
    --paths ~/PycharmProjects/FotoPDF/venv/lib/python3.7/site-packages \
    --add-data font_default.ttf:./font_default.ttf \
    --add-data FotoPDF.png:./FotoPDF.png \
    --icon FotoPDF.png \
    main.py