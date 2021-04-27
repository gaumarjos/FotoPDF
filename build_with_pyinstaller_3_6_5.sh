# To install an older python version with pyenv on BigSur
# LDFLAGS="-L$(brew --prefix zlib)/lib -L$(brew --prefix bzip2)/lib" PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install --patch 3.6.5 < <(curl -sSL https://github.com/python/cpython/commit/8ea6353.patch\?full_index\=1)
# https://dev.to/kojikanao/install-python-3-7-3-6-and-3-5-on-bigsure-with-pyenv-3ij2

clear
rm -rf build dist
pyinstaller --noconfirm --log-level=ERROR \
    --clean \
    --onefile \
    --windowed \
    --name FotoPDF \
    --debug imports \
    --paths ~/PycharmProjects/FotoPDF/venv_3_6_5/lib/python3.9/site-packages/ \
    --add-data font_default.ttf:. \
    --add-data FotoPDF.png:. \
    --icon FotoPDF.png \
    --hidden-import PyQt5 \
    --hidden-import PyQt5.sip \
    --hidden-import PyQt5.QtWidgets \
    --hidden-import PyQt5.QtGui \
    --hidden-import PyQt5.QtCore \
    FotoPDF.py