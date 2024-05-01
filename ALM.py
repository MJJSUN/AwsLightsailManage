import os
import sys
import json
import time
import argparse
import readline
import subprocess
from boto3 import client
from botocore.client import Config
from datetime import datetime, timedelta


parser = argparse.ArgumentParser(description="Description of options")
parser.add_argument(
    "-c",
    dest="config_file",
    default="config.json",
    help="Path to config file",
)
parser.add_argument("-r", dest="r_value", help="The instance name")
parser.add_argument("-n", dest="n_value", help="The region name")
parser.add_argument("-o", dest="o_value", help="Operation")
parser.add_argument("-l", dest="l_value", help="Limit traffic")
args = parser.parse_args()


def read_config():
    config_file = args.config_file
    if os.path.exists(config_file):
        # 如果配置文件存在，则读取内容
        with open(config_file, "r") as f:
            config = json.load(f)
    else:
        try:
            # 如果配置文件不存在，则提示用户输入
            config = {}
            print("检测到配置文件不存在")
            config["access_key_id"] = input("请输入access_key_id: ")
            config["secret_access_key"] = input("请输入secret_access_key: ")

            # 将用户输入的内容写入配置文件
            with open(config_file, "w") as f:
                json.dump(config, f, indent=4)
        except KeyboardInterrupt:
            print("\n你按下了 Ctrl+C，正在退出...")
            sys.exit()
        except EOFError:
            print("\n你按下了 Ctrl+D，正在退出...")
            sys.exit()

    return config


config = read_config()
# 参考了 https://aws.amazon.com/cn/blogs/china/monitor-amazon-lightsail-data-traffic-using-lambda/
# AWS API 信息
Data = {
    "vps_name": "Debian-1",
    "region": "us-east-1",
    "access_key_id": config.get("access_key_id") if config else "默认值1",
    "secret_access_key": config.get("secret_access_key") if config else "默认值2",
}


def initialize_aws_api(region):
    return client(
        "lightsail",
        region_name=region,
        aws_access_key_id=Data["access_key_id"],
        aws_secret_access_key=Data["secret_access_key"],
        config=Config(connect_timeout=3, read_timeout=3, retries={"max_attempts": 3}),
    )


# 初始化客户端
aws_api = initialize_aws_api(Data["region"])


def update_credentials():
    global Data
    global aws_api
    new_config = {}
    config_file = "config.json"
    print("请输入新的 Access Key ID 和 Secret Access Key：")

    new_config["access_key_id"] = input("Access Key ID: ")
    new_config["secret_access_key"] = input("Secret Access Key: ")

    Data["access_key_id"] = new_config["access_key_id"]
    Data["secret_access_key"] = new_config["secret_access_key"]

    aws_api = initialize_aws_api(Data["region"])
    # 将用户输入的内容写入配置文件
    with open(config_file, "w") as f:
        json.dump(new_config, f, indent=4)
    print("Access Key ID 和 Secret Access Key 更新成功。")


def check_systemd_file_exists(name):
    # 构建文件名后缀列表
    suffix_list = [".service", ".timer"]

    # 遍历后缀列表
    for suffix in suffix_list:
        # 拼接文件路径
        file_path = f"/etc/systemd/system/{name}{suffix}"

        # 检查文件是否存在
        if os.path.exists(file_path):
            print(f"File '{file_path}' exists!")
            return True

    # 没有找到符合条件的文件
    print(f"No matching file for service found!")
    return False


# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lightsail/client/get_instance_metric_data.html
def get_usage(data_type):  # 获取一个月的流量信息
    dt = datetime.today().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )  # 获取当月起始时间
    res = aws_api.get_instance_metric_data(
        instanceName=Data["vps_name"],
        metricName=data_type,
        period=300 * 12 * 24,  # 一天的秒数，300s 是最小统计单位
        unit="Bytes",
        statistics=["Sum"],
        startTime=dt,  # 开始日期
        endTime=(dt + timedelta(days=32)).replace(day=1),  # 结束日期，下月起始时间
    )
    usage = sum([p["sum"] for p in res["metricData"]])
    usage_gb = usage / (1024**3)
    return round(usage_gb, 2)  # 返回以 GB 为单位的流量信息，保留两位小数

    # 获取当前日期和时间
    # current_time = datetime.now()
    # 如果实例状态为关机且当前日期是下个月的1号早上8点
    # if state == 'stopped' and current_time.day == 1 and current_time.hour == 8:
    # 开启实例
    # aws_api.start_instance(instanceName=Data["vps_name"])
    # print("实例已开启。")

    # 如果总流量超过 500GB，则关闭 Lightsail 实例
    # if total_usage > 500:
    #     aws_api.stop_instance(instanceName=Data["vps_name"])
    #     print("总流量超过500GB，已关闭 Lightsail 实例。")


def print_usage():
    try:
        network_out_usage = get_usage("NetworkOut")
        network_in_usage = get_usage("NetworkIn")
        total_usage = network_out_usage + network_in_usage  # 计算总流量
        print(f"入站流量: {network_in_usage} GB")
        print(f"出站流量: {network_out_usage} GB")
        print(f"总流量: {total_usage} GB")
        if args.l_value is not None:
            if total_usage > float(args.l_value):
                aws_api.stop_instance(instanceName=Data["vps_name"])
                print(f"总流量超过{args.l_value}GB，已关闭 Lightsail 实例。")
                subprocess.run(
                    [
                        "systemctl",
                        "stop",
                        Data["region"] + "_" + Data["vps_name"] + ".timer",
                    ]
                )
        else:
            print(datetime.now())
    except Exception as e:
        # 捕获异常并打印错误信息
        print("Error:", e)


def boot_on_1():
    instance_details = aws_api.get_instance(instanceName=Data["vps_name"])
    state = instance_details["instance"]["state"]["name"]
    if state == "stopped":
        aws_api.start_instance(instanceName=Data["vps_name"])
        print("实例已开启。")
        subprocess.run(
            ["systemctl", "start", Data["region"] + "_" + Data["vps_name"] + ".timer"]
        )
    else:
        print("实例处于非关机状态")


def get_all_regions():
    try:
        # 调用get_regions方法获取所有区域信息
        response = aws_api.get_regions()
        regions = response["regions"]

        # 提取每个区域的名称并存储在列表中
        region_names = [region["name"] for region in regions]

        # print("Region Name:", region["name"])
        # print("Display Name:", region["displayName"])
        # print("Description:", region["description"])

        return region_names

    except Exception as e:
        print("Error:", e)


# 更新区域设置
def update_region(new_region):
    global aws_api
    global Data
    # 当前使用的客户端信息
    aws_api = initialize_aws_api(new_region)
    Data["region"] = aws_api.meta.region_name


def get_all_instances():
    region_names = get_all_regions()
    with open("instances.txt", mode="w", encoding="utf-8") as file:
        # 遍历每个区域名称并调用update_region方法
        for name in region_names:
            update_region(name)
            print("更新区域至: ", name)
            instances = aws_api.get_instances()
            if instances:  # 检查instances是否不为空
                for instance in instances["instances"]:
                    file.write(f"Region: {name}, Instance Name: {instance['name']}\n")
                    print("找到实例:", instance["name"])


def read_instances_from_file(file_path):
    instances = []
    with open(file_path, mode="r", encoding="utf-8") as file:
        for line in file:
            if line.strip():  # 跳过空行
                region, instance_name = line.strip().split(", ")
                instances.append((region.split(": ")[1], instance_name.split(": ")[1]))
    return instances


def is_file_empty(file_path):
    try:
        with open(file_path, "r") as file:
            content = file.read()
            return not content.strip()
    except FileNotFoundError:
        return True


def select_instance(instances):
    print("从缓存中读取到以下实例信息: ")
    for i, instance in enumerate(instances, 1):
        print(f"{i}. {instance[1]} in {instance[0]}")

    while True:
        try:
            choice = int(input("请输入序号选择实例: "))
            if 1 <= choice <= len(instances):
                return instances[choice - 1]
            else:
                print("无效的选项，请重新输入。")
        except ValueError:
            print("无效的选项，请重新输入。")


def create_timer_service(limit, sec):
    global Data
    # systemd服务单元文件内容
    systemd_unit_content = f"""[Unit]
Description=ALM Service
After=network.target
    
[Service]
Type=simple
ExecStart={sys.executable} -c {os.path.dirname(sys.executable)}/config.json -r {Data["region"]} -n {Data["vps_name"]} -o 1 -l {limit}

[Install]
WantedBy=default.target
"""

    # 定时器服务单元文件内容
    timer_unit_content = f"""[Unit]
Description=ALM Timer Service

[Timer]
OnUnitActiveSec={sec}m
OnBootSec={sec}m

[Install]
WantedBy=timers.target
"""

    service_name = Data["region"] + "_" + Data["vps_name"]
    s = "/etc/systemd/system/" + service_name + ".service"
    t = "/etc/systemd/system/" + service_name + ".timer"
    with open(s, "w") as f:
        f.write(systemd_unit_content)
    with open(t, "w") as f:
        f.write(timer_unit_content)
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "start", service_name + ".timer"])
    subprocess.run(["systemctl", "enable", service_name + ".timer"])


def create_boot_on_1_service():
    global Data
    # systemd服务单元文件内容
    systemd_unit_content = f"""[Unit]
Description=ALM Service
After=network.target

[Service]
Type=simple
ExecStart={sys.executable} -c {os.path.dirname(sys.executable)}/config.json -r {Data["region"]} -n {Data["vps_name"]} -o 2
    
[Install]
WantedBy=default.target
"""

    # 定时器服务单元文件内容
    timer_unit_content = f"""[Unit]
Description=ALM Timer Service

[Timer]
OnCalendar=*-*-01 08:00:00
    
[Install]
WantedBy=timers.target
"""

    service_name = Data["region"] + "_" + Data["vps_name"] + "_boot"
    s = "/etc/systemd/system/" + service_name + ".service"
    t = "/etc/systemd/system/" + service_name + ".timer"
    with open(s, "w") as f:
        f.write(systemd_unit_content)
    with open(t, "w") as f:
        f.write(timer_unit_content)
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "start", service_name + ".timer"])
    subprocess.run(["systemctl", "enable", service_name + ".timer"])


def delete_service():
    subprocess.run(
        ["systemctl", "stop", Data["region"] + "_" + Data["vps_name"] + ".timer"]
    )
    subprocess.run(
        [
            "systemctl",
            "stop",
            Data["region"] + "_" + Data["vps_name"] + "_boot" + ".timer",
        ]
    )
    subprocess.run(
        ["systemctl", "disable", Data["region"] + "_" + Data["vps_name"] + ".timer"]
    )
    subprocess.run(
        [
            "systemctl",
            "disable",
            Data["region"] + "_" + Data["vps_name"] + "_boot" + ".timer",
        ]
    )
    directory = "/etc/systemd/system/"
    target_string = Data["region"] + "_" + Data["vps_name"]
    file_list = os.listdir(directory)
    for filename in file_list:
        if target_string in filename:
            file_path = os.path.join(directory, filename)
            os.remove(file_path)
            print(f"已删除: {file_path}")
    subprocess.run(["systemctl", "daemon-reload"])


def show_menu1():
    try:
        while True:
            print()
            print("=== 菜单 ===")
            print("1. 获取所有实例")
            print("2. 选择实例操作")
            print("3. 修改 Access Key ID 和 Secret Access Key")
            print("0. 退出")
            print("============")
            print()
            # instance_details = aws_api.get_instance(instanceName=Data["vps_name"])
            # state = instance_details["instance"]["state"]["name"]
            # print("当前状态: ", state)
            choice = input("请输入选项：")

            if choice == "1":
                print()
                get_all_instances()
            elif choice == "2":
                print()
                if is_file_empty("instances.txt"):
                    print("缓存为空，请先运行获取所有实例。")
                    time.sleep(3)
                    show_menu1()
                else:
                    # 从文件中读取实例信息
                    instances = read_instances_from_file("instances.txt")
                    # 选择实例
                    selected_instance = select_instance(instances)
                    print()
                    print("你选择了: ", selected_instance)
                    update_region(selected_instance[0])
                    Data["vps_name"] = selected_instance[1]
                    show_menu2()
            elif choice == "3":
                print()
                update_credentials()
            elif choice == "0":
                print()
                print("退出脚本。")
                break
            else:
                print()
                print("无效的选项，请重新输入。")
    except KeyboardInterrupt:
        print("\n你按下了 Ctrl+C，正在退出...")
    except EOFError:
        print("\n你按下了 Ctrl+D，正在退出...")


def show_menu2():
    try:
        while True:
            print()
            print("=== 菜单 ===")
            print("1. 查询流量")
            print("2. 添加”超流关机&一号开机“任务")
            print("3. 删除”超流关机&一号开机“任务")
            print("4. 重启")
            print("5. 开机")
            print("6. 关机")
            print("0. 返回上一级菜单。")
            print("99. 退出")
            print("============")
            print()

            choice = input("请输入选项：")
            if choice == "1":
                print()
                print_usage()
            elif choice == "2":
                print()
                limit = input("输入限制的总流量(GB,默认900): ") or "900"
                sec = input("输入定时查询间隔(分钟,默认10): ") or "10"
                create_timer_service(limit, sec)
                create_boot_on_1_service()
            elif choice == "3":
                print()
                delete_service()
            elif choice == "4":
                print()
                aws_api.reboot_instance(instanceName=Data["vps_name"])
                print("实例已重启。")
            elif choice == "5":
                print()
                aws_api.start_instance(instanceName=Data["vps_name"])
                print("实例已开启。")
            elif choice == "6":
                print()
                aws_api.stop_instance(instanceName=Data["vps_name"])
                print("实例已关闭。")
            elif choice == "0":
                print()
                print("返回上一级菜单。")
                break
            elif choice == "99":
                print()
                print("退出脚本。")
                sys.exit()
            else:
                print()
                print("无效的选项，请重新输入。")
    except KeyboardInterrupt:
        print("\n你按下了 Ctrl+C，正在退出...")
    except EOFError:
        print("\n你按下了 Ctrl+D，正在退出...")


if __name__ == "__main__":
    if args.r_value is not None:
        update_region(args.r_value)
    if args.n_value is not None:
        Data["vps_name"] = args.n_value
    if args.o_value is not None:
        if args.o_value == "1":
            print()
            print_usage()
        elif args.o_value == "2":
            print()
            boot_on_1()
        elif args.o_value == "3":
            print()
            aws_api.reboot_instance(instanceName=Data["vps_name"])
            print("实例已重启。")
        elif args.o_value == "4":
            print()
            aws_api.start_instance(instanceName=Data["vps_name"])
            print("实例已开启。")
        elif args.o_value == "5":
            print()
            aws_api.stop_instance(instanceName=Data["vps_name"])
            print("实例已关闭。")
    else:
        show_menu1()
