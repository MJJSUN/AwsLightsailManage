### Feature
- Query IN/OUT bandwidth
- Reboot/Start/Poweroff instance

### Require
`Python 3, AWS API Key(下载脚本后修改你自己的实例信息和密钥)`

### Prepare
```
pip install boto3 botocore requests
```

### For Debian/Ubuntu
```
apt install python3-boto3 python3-botocore python3-requests
```

### Usage
```
wget https://github.com/MJJSUN/AwsLightsailManage/blob/main/aws.py
```

- EDIT FILE aws.py

```
python aws.py
```

---

### Todo

- [ ] 脚本接收外部参数
- [ ] 脚本内添加crontab任务
- [x] 一键查询所有实例
- [ ] 定时开机/超流关机
- [ ] 对接TG bot
- [ ] etc.

### 参考文献:
[在订阅中显示 Lightsail 流量使用情况](https://moenew.us/Lightsail-Traffic-Subscription.html)

### Stargazers over time
[![Stargazers over time](https://starchart.cc/MJJSUN/AwsLightsailManage.svg?variant=adaptive)](https://starchart.cc/MJJSUN/AwsLightsailManage)
