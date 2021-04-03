clear
rm -r dist
pyinstaller --noconfirm --log-level=ERROR \
    --onefile \
    --nowindow \
    --name FotoPDF \
    --paths ~/PycharmProjects/FotoPDF/venv/lib/python3.7/site-packages \
    --add-data font_default.ttf:./font_default.ttf \
    main.py