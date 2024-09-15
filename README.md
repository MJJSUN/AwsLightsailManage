## 因为AWS码子涨价了，故作者需要减少使用AWS，新功能的开发无限延后。

### Encoded by ChatGPT. 开发版请切换到dev分支

### Feature
- Query IN/OUT bandwidth
- Reboot/Start/Poweroff instance

### Require
`Python 3, AWS API Key(下载脚本后修改你自己的实例信息和密钥)`

### Prepare
```
pip3 install boto3 botocore requests
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
python3 aws.py
```

---

### Todo

- [ ] 脚本接收外部参数
- [ ] 脚本内添加~~crontab~~systemd任务
- [x] 一键查询所有实例
- [ ] 定时开机/超流关机
- [ ] 对接TG bot
- [ ] etc.

### 参考文献:
[在订阅中显示 Lightsail 流量使用情况](https://moenew.us/Lightsail-Traffic-Subscription.html)

### Stargazers over time
[![Stargazers over time](https://starchart.cc/MJJSUN/AwsLightsailManage.svg?variant=adaptive)](https://starchart.cc/MJJSUN/AwsLightsailManage)
