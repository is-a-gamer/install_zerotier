import requests
import subprocess
import json
import time
import win32serviceutil
import win32service
import win32event
import servicemanager
import platform
import ctypes
import os
import sys

# pyinstaller --hiddenimport pywin32 --hiddenimport pywin32-ctypes --hiddenimport win32timezone -F .\ZerotierCheck.py

json_file_path = 'C:\\ProgramData\\ZeroTier\\One\\update.json'
save_planet_path = 'C:\\ProgramData\\ZeroTier\\One\\planet'
ip_pong = True
domain_pong = True
dns_pong = True


def read_json_file():
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Error occurred while reading JSON file: {e}")
        return None


def read_ip_from_json():
    return read_json_file().get('planet_server_ip')  # planet节点的IP地址


def read_domain_from_json():
    return read_json_file().get('planet_server_domain')  # 用于测试服务器的DDNS是否更新


def read_update_url_from_json():
    return read_json_file().get('update_planet_url')  # 下载直链,不知道有什么好的文件同步方案,如果有,请开issue告知，非常感谢

def is_admin():
    if platform.system() == 'Windows':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    return os.getuid() == 0




def ping_ip(ip_address, count=1):
    try:
        # 执行ping命令
        result = subprocess.run(['ping', '-n', str(count), ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=5)
        # 检查返回码，如果返回码为0表示ping通，否则表示无法ping通
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error occurred: {e}")
        return False


def ping_domain(domain, count=1):
    try:
        # 执行ping命令
        result = subprocess.run(['ping', '-n', str(count), domain], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=5)
        # 检查返回码，如果返回码为0表示ping通，否则表示无法ping通
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error occurred: {e}")
        return False


def download_file(url, save_path):
    try:
        # 发起GET请求下载文件
        print("wait download...")
        print(url)
        print("download success")
        # zfile如果不加这个请求头，将会下载失败
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        # 如果请求成功
        if response.status_code == 200:
            # 将文件内容写入到本地文件
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error occurred: {e}")
        return False
class ZerotierCheck(win32serviceutil.ServiceFramework):
    _svc_name_ = "ZerotierCheck"
    _svc_display_name_ = "ZerotierCheck"
    _svc_description_ = "用于检查Zerotier与Planet节点是否正常,并更新planet文件,配置文件位于Zerotier安装目录中的update.json"
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
    def SvcDoRun(self):
        try:
            # 在事件日志中记录服务已启动
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, ''))
            # 调用服务的主要逻辑
            self.main()
        except Exception as e:
            # 捕获任何异常并记录到日志中
            servicemanager.LogErrorMsg(f"An error occurred: {str(e)}")
            # 如果发生异常，报告服务即将停止
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

    def main(self):
        global ip_pong
        global dns_pong
        global domain_pong
        while True:
            ip_address = read_ip_from_json()
            # 测试IP地址是否可达
            if ping_ip(ip_address):
                print("ip pong")
                ip_pong = True
            else:
                print("ip not pong")
                ip_pong = False
                if not ping_ip("223.5.5.5"):
                    print("dns not pong")
                    ip_pong = True
            if not ip_pong:
                # 测试DNS地址是否可达
                if ping_ip("223.5.5.5"):
                    dns_pong = True
                else:
                    dns_pong = False
            if not ip_pong and dns_pong:
                domain = read_domain_from_json()
                if ping_domain(domain):
                    download_url = read_update_url_from_json()
                    download_file(download_url, save_planet_path)
                    service_name = "ZeroTierOneService"
                    # 这一步会使用win32serviceutil.RestartService偶尔会莫名其妙的卡住，并且因为服务启动超时然后崩溃
                    # 如果有人知道是为什么，请修改此代码
                    try:
                        win32serviceutil.StopService(service_name)
                    except Exception as e:
                        print(e)
                    time.sleep(15)
                    service_status = win32serviceutil.QueryServiceStatus("ZeroTierOneService")[1]
                    while service_status != win32service.SERVICE_RUNNING:
                        try:
                            win32serviceutil.StartService(service_name)
                            time.sleep(15)
                            service_status = win32serviceutil.QueryServiceStatus("ZeroTierOneService")[1]
                        except Exception as e:
                            print(e)
                    time.sleep(30)
                    print("重启完成")
                else:
                    print(f"{domain} not pong")
            time.sleep(30)


if __name__ == '__main__':
    if not is_admin():
        print("请使用管理员权限运行此脚本!")
        sys.exit()
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ZerotierCheck)
        servicemanager.StartServiceCtrlDispatcher()
    win32serviceutil.HandleCommandLine(ZerotierCheck)
