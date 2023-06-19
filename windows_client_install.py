import os
import shutil
import subprocess
import sys
import ctypes
import platform
import win32serviceutil
import time

# pip install pyinstaller
# pyinstaller --add-data "planet;." --add-data "WinIPBroadcast-1.6.exe;." --add-data "ZeroTierOne.msi;." -F .\windows_client_install.py
try:
    def is_admin():
        if platform.system() == 'Windows':
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
        return os.getuid() == 0


    if not is_admin():
        print("请使用管理员权限运行此脚本!")
        input("按任意键继续...")
        sys.exit()

    file_path = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(file_path, "planet")):
        print('没有放置plant')
    if os.path.exists(os.path.join(file_path, "WinIPBroadcast-1.6.exe")):

        NetworkID = input('需要加入的网络ID')
        print("===============================================================================================")
        print('会弹出来安装界面，请手动点击"Next",并且完成安装!')
        print('不要修改任何的安装路径!')
        input("按任意键继续...")
        print("===============================================================================================")
        print('请等待程序安装完成!')

        subprocess.run([os.path.join(file_path, "WinIPBroadcast-1.6.exe"), "/passive", "/norestart"], check=False)
        print('还有一个,请等待程序安装完成!')
        subprocess.run(["msiexec", "/i", os.path.join(file_path, "ZeroTierOne.msi")], check=True)

        print("===============================================================================================")
        planet_path = os.path.join(file_path, "planet")
        destination_path = "C:\\ProgramData\\ZeroTier\\One\\planet"
        print("替换planet")
        shutil.copyfile(planet_path, destination_path)
        service_name = "ZeroTierOneService"
        print("===============================================================================================")
        print("尝试重启服务")
        print("目前为运行状态,尝试重启,加载配置,请继续等待")
        win32serviceutil.RestartService(service_name)
        time.sleep(5)
        print("===============================================================================================")
        print("重启完成,请继续等待")
        subprocess.run([os.path.join("C:\\Program Files (x86)\\ZeroTier\\One\\zerotier-cli.bat"), "NetworkID"],
                       check=True)
        time.sleep(5)
        subprocess.run(
            [os.path.join("C:\\Program Files (x86)\\ZeroTier\\One\\zerotier-cli.bat"), "join", NetworkID],
            check=True)
        print("===============================================================================================")
        print('安装完成，请按任意键关闭此窗口')
        input()
    else:
        print("===============================================================================================")
        print("检查所需文件是否存在这个目录下")
        print(file_path)
        input("按任意键关闭此窗口")
        sys.exit()
except Exception as e:
    print("####################################################################################################")
    print("报错了,快截图,问问是啥情况")
    print("####################################################################################################")
    print(e)
    print("####################################################################################################")
    input("按任意键关闭")
