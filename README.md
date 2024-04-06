### Feature
Query IN/OUT bandwidth
Reboot/Start/Poweroff instance

### Require:
Python 3, AWS API Key(下载脚本后修改你自己的实例信息和密钥)

### Prepare:
```
pip install boto3 botocore requests
```

### For Debian/Ubuntu
```
apt install python3-boto3 python3-botocore python3-requests
```

### Usage:
```
python aws.py
```

---

### Todo

- [x] 脚本接收外部参数
- [x] 脚本内添加crontab任务
- [x] 一键查询所有实例
- [x] 定时开机/超流关机
- [x] 对接TG bot
- [x] etc.

### 参考文献:
[在订阅中显示 Lightsail 流量使用情况](https://moenew.us/Lightsail-Traffic-Subscription.html)
