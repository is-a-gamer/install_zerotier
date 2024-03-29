pip install pyinstaller

copy files/planet ./planet

copy files/WinIPBroadcast-1.6.exe ./WinIPBroadcast-1.6.exe

copy files/ZerotierOne.msi ./ZerotierOne.msi

pyinstaller --add-data "planet;." --add-data "WinIPBroadcast-1.6.exe;." --add-data "ZeroTierOne.msi;." -F .\windows_client_install.py

pyinstaller --hiddenimport pywin32 --hiddenimport pywin32-ctypes --hiddenimport win32timezone -F .\ZerotierCheck.py