# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['/Users/ste/PycharmProjects/FotoPDF/venv/lib/python3.7/site-packages', '/Users/ste/PycharmProjects/FotoPDF'],
             binaries=[],
             datas=[('font_default.ttf', './font_default.ttf'), ('FotoPDF.png', './FotoPDF.png')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='FotoPDF',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon='FotoPDF.png')
app = BUNDLE(exe,
             name='FotoPDF.app',
             icon='FotoPDF.png',
             bundle_identifier=None)
