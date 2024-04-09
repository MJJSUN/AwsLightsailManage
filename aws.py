from boto3 import client
from botocore.client import Config
from datetime import datetime, timedelta

# 参考了 https://aws.amazon.com/cn/blogs/china/monitor-amazon-lightsail-data-traffic-using-lambda/
Data = {
    # AWS API 信息
    "vps_name": "YourLightsailInstanceName",  # 替换为你的 Lightsail 实例名称
    "region": "YourRegion",                   # 替换为你的实例所在区域，如 "us-east-1"
    "access_key_id": "YourAccessKeyID",       # 替换为你的 AWS Access Key ID
    "secret_access_key": "YourSecretAccessKey",  # 替换为你的 AWS Secret Access Key
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
    usage_GB = usage / (1024**3)
    return round(usage_GB, 2)  # 返回以 GB 为单位的流量信息，保留两位小数

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
    aws_api = initialize_aws_api(new_region)


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
    if is_file_empty(file_path):
        print("缓存为空，请先运行获取所有实例。")
    else:
        instances = []
        with open(file_path, mode="r", encoding="utf-8") as file:
            for line in file:
                if line.strip():  # 跳过空行
                    region, instance_name = line.strip().split(", ")
                    instances.append(
                        (region.split(": ")[1], instance_name.split(": ")[1])
                    )
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


def show_menu1():
    print()
    print("=== 菜单 ===")
    print("1. 获取所有实例")
    print("2. 选择实例操作")
    print("0. 退出")
    print("============")
    print()


def show_menu2():
    while True:
        print()
        print("=== 菜单 ===")
        print("1. 查询流量")
        print("2. 重启")
        print("3. 开机")
        print("4. 关机")
        print("0. 返回上一级菜单。")
        print("99. 退出")
        print("============")
        print()

        choice = input("请输入选项：")
        if choice == "1":
            print()
            try:
                network_out_usage = get_usage("NetworkOut")
                network_in_usage = get_usage("NetworkIn")
                total_usage = network_out_usage + network_in_usage  # 计算总流量
                print(f"入站流量: {network_in_usage} GB")
                print(f"出站流量: {network_out_usage} GB")
                print(f"总流量: {total_usage} GB")
            except Exception as e:
                # 捕获异常并打印错误信息
                print("Error:", e)
        elif choice == "2":
            print()
            aws_api.reboot_instance(instanceName=Data["vps_name"])
            print("实例已重启。")
        elif choice == "3":
            print()
            aws_api.start_instance(instanceName=Data["vps_name"])
            print("实例已开启。")
        elif choice == "4":
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
            exit()
        else:
            print()
            print("无效的选项，请重新输入。")


def main():
    while True:
        show_menu1()
        # instance_details = aws_api.get_instance(instanceName=Data["vps_name"])
        # state = instance_details["instance"]["state"]["name"]
        # print("当前状态: ", state)
        choice = input("请输入选项：")

        if choice == "1":
            print()
            get_all_instances()
        elif choice == "2":
            print()
            # 从文件中读取实例信息
            instances = read_instances_from_file("instances.txt")

            # 选择实例
            selected_instance = select_instance(instances)
            print()
            print("你选择了: ", selected_instance)
            update_region(selected_instance[0])
            Data["vps_name"] = selected_instance[1]
            show_menu2()
        elif choice == "0":
            print()
            print("退出脚本。")
            break
        else:
            print()
            print("无效的选项，请重新输入。")


if __name__ == "__main__":
    main()
