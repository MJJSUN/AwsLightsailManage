from boto3 import client
from botocore.client import Config
from requests import put
from datetime import datetime, timedelta

# 参考了 https://aws.amazon.com/cn/blogs/china/monitor-amazon-lightsail-data-traffic-using-lambda/
Data = {
    # AWS API 信息
    "vps_name": "主机名如Debian-1",
    "region": "区域如ap-southeast-2",
    "access_key_id": "访问密钥",
    "secret_access_key": "秘密访问密钥",
}

aws_api = client(
    "lightsail",
    region_name=Data["region"],
    aws_access_key_id=Data["access_key_id"],
    aws_secret_access_key=Data["secret_access_key"],
    config=Config(connect_timeout=3, read_timeout=3, retries={"max_attempts": 3}),
)


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


def show_menu():
    print()
    print("=== 菜单 ===")
    print("1. 查询流量")
    print("2. 重启")
    print("3. 开机")
    print("4. 关机")
    print("0. 退出")
    print("============")
    print()


def main():
    while True:
        show_menu()
        instance_details = aws_api.get_instance(instanceName=Data["vps_name"])
        state = instance_details["instance"]["state"]["name"]
        print("当前状态: ", state)
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
            print("退出菜单。")
            break
        else:
            print()
            print("无效的选项，请重新输入。")


if __name__ == "__main__":
    main()
