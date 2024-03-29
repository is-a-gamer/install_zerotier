import os
import subprocess

# 获取公共IP地址
ip = subprocess.check_output(["wget", "http://ipecho.net/plain", "-O", "-", "-q"]).decode("utf-8").strip()
addr = f"{ip}/9993"

# 更新并安装所需的软件包
subprocess.run(["apt", "autoremove"])
subprocess.run(["apt", "update", "-y"])
subprocess.run(["apt", "install", "curl", "-y"])

# 安装ZeroTier
print("**********Debian Ubuntu自动安装ZeroTier并将其设置为Planet服务器**********")
subprocess.run(["curl", "-s", "https://install.zerotier.com/", "|", "sudo", "bash"])

# 获取ZeroTier身份信息
identity = open("/var/lib/zerotier-one/identity.public").read().strip()
print(f"身份信息: {identity}==============================================")

# 安装构建工具和git
subprocess.run(["apt-get", "-y", "install", "build-essential"])
subprocess.run(["apt-get", "install", "git", "-y"])

# 克隆ZeroTierOne存储库并切换到特定版本
subprocess.run(["git", "clone", "https://github.com/zerotier/ZeroTierOne.git"])
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

os.chdir("../../../")
# 下载并安装ztncui
ztncui_url = "https://s3-us-west-1.amazonaws.com/key-networks/deb/ztncui/1/x86_64/ztncui_0.8.14_amd64.deb"
subprocess.run(["wget", ztncui_url])
subprocess.run(["apt", "install", "-y", "./ztncui_0.8.14_amd64.deb"])

# 配置ztncui
os.chdir("/opt/key-networks/ztncui/")
with open(".env", "a") as file:
    file.write("HTTPS_PORT = 3443\n")
    secret = open("/var/lib/zerotier-one/authtoken.secret").read().strip()
    file.write(f"ZT_TOKEN = {secret}\n")
    file.write(f"ZT_ADDR = 127.0.0.1:9993\n")
    file.write("NODE_ENV = production\n")
    file.write("HTTP_ALL_INTERFACES = yes\n")

# 重启ztncui
subprocess.run(["systemctl", "restart", "ztncui"])

# 清理
#subprocess.run(["rm", "-rf", "/root/ZeroTierOne"])
print("**********安装成功*********************************************************************************")
print("plant文件已经生成在autosync目录")