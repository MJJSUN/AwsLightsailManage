### Usage
```
wget https://github.com/MJJSUN/AwsLightsailManage/releases/download/v1.0.0/ALM-linux-amd64 -O ALM && chmod +x ALM
```
```
./ALM
```

你也可以直接执行脚本，前提是安装boto3 botocore requests这三个运行库。
```
wget -P /root -N --no-check-certificate "https://raw.githubusercontent.com/MJJSUN/AwsLightsailManage/dev/ALM.py" && python3 /root/ALM.py
```

### Build
方法1. 在较低版本的 Linux 系统上打包
为了确保兼容性，最好在一个较老的 Linux 发行版上进行打包。因为老版本的 GLIBC 通常可以向后兼容较新的版本，而相反则不行。
因此，你可以尝试在使用较低版本 GLIBC 的系统（例如 CentOS 7、Ubuntu 18.04）上打包你的 Python 脚本。
以已经安装Python3的CentOS 7 为例
```
pip3 install boto3 botocore requests wheel pyinstaller
```

```
wget -P /root -N --no-check-certificate "https://raw.githubusercontent.com/MJJSUN/AwsLightsailManage/dev/ALM.py" && pyinstaller --onefile /root/ALM.py
```

方法2. 使用 Docker 创建一致的环境
通过在 Docker 中创建一个具有特定 GLIBC 版本的环境，你可以确保打包时的环境和目标系统的一致性。步骤如下：

创建一个使用旧版本 Linux（如 CentOS 或 Ubuntu）的 Docker 容器。
在容器中安装 Python 以及所需的依赖项。
使用 PyInstaller 打包你的应用程序。
将打包好的可执行文件从容器中拷贝出来。
示例 Dockerfile（以 CentOS 7 为例）：
```
FROM centos:7

RUN yum install -y python3 python3-pip gcc
RUN pip3 install pyinstaller

# 复制你的项目到容器中
COPY . /app
WORKDIR /app

# 打包 Python 脚本
RUN pyinstaller --onefile your_script.py

# 将打包好的文件从容器复制到宿主系统
```
