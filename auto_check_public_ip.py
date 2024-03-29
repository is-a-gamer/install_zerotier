import requests
import time
import os
import subprocess
# 用于存储上一次检测到的IP地址
previous_ip = None

def rebuild_plant_file():
    # 获取ZeroTier身份信息
    identity = open("/var/lib/zerotier-one/identity.public").read().strip()
    print(f"身份信息: {identity}==============================================")
    os.chdir("./ZeroTierOne/")
    subprocess.run(["git", "checkout", "1.12.2"])  # 指定您需要的版本

    # 进入world目录
    os.chdir("./attic/world/")

    # 修改mkworld.cpp
    with open("mkworld.cpp", "r") as file:
        lines = file.readlines()

    lines = [line for line in lines if "roots.push_back" not in line and "roots.back()" not in line]
    lines.insert(85, "\troots.push_back(World::Root());\n")
    lines.insert(86, f'\troots.back().identity = Identity("{identity}");\n')
    lines.insert(87, f'\troots.back().stableEndpoints.push_back(InetAddress("{addr}"));\n')

    with open("mkworld.cpp", "w") as file:
        file.writelines(lines)

    # 构建并移动planet
    print(subprocess.run(["pwd"]))
    subprocess.run(["bash", "./build.sh"])
    subprocess.run(["./mkworld"])
    subprocess.run(["cp", "./world.bin", "./planet"])
    subprocess.run(["mkdir", "-p", "../../../autosync"])
    subprocess.run(["mv", "./world.bin", "../../../autosync/planet"])
    subprocess.run(["cp", "-r", "./planet", "/var/lib/zerotier-one/"])
    subprocess.run(["cp", "-r", "./planet", "/root"])
    subprocess.run(["systemctl", "restart", "zerotier-one.service"])
    print("plant文件已经生成在autosync目录")

def get_public_ip():
    try:
        # 使用一个可以返回你的公网IP地址的服务
        response = requests.get('https://api.ipify.org')
        if response.status_code == 200:
            return response.text
        else:
            print("Failed to retrieve IP address:", response.status_code)
    except Exception as e:
        print("Error retrieving IP address:", e)
    return None

def start():
    global previous_ip
    while True:
        current_ip = get_public_ip()
        if current_ip:
            if current_ip != previous_ip:
                print("Your public IP address has changed to:", current_ip)
                rebuild_plant_file()
                # 执行你想要执行的命令
                # 这里可以是调用其他函数、运行其他脚本等等
                # 示例：os.system("your_command")
                # 示例：subprocess.run(["your_command", "arg1", "arg2"])
                previous_ip = current_ip
        else:
            print("Unable to retrieve public IP address.")
        # 每隔一段时间检测一次
        time.sleep(60)  # 每分钟检测一次

start()