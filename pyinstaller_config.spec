# -*- mode: python -*-

block_cipher = None


a = Analysis(['AppstreamUserManager.py'],
             pathex=['C:\\Users\\Emilio\\Desktop\\Appstream-User-Manager'],
             binaries=[],
             datas=[('.\\images\\icon.gif','.'),
			 ('.\\images\\search.gif','.'),
			 ('.\\images\\refresh.gif','.')],
             hiddenimports=['win32timezone','win32cred'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['scipy','matplotlib','PIL','cython','PyQt4','zmq','sqlite3','lib2to3','hook-numpy','numpy'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
		  Tree('.\\images',  prefix='images\\'),
          a.zipfiles,
          a.datas,
          [],
          name='Appstream User Manager',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
		  icon='.\\images\\icon.ico'
			)
