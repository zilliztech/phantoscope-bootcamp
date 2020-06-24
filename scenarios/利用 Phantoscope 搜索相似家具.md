# 利用 Phantoscope 搜索相似家具

本文展示如何利用 Phantoscope 搭建一个搜索相似家具的以图搜图系统。

## 1 环境要求

下表列出了搭建相似家具以图搜图系统的推荐配置，这些配置已经经过测试。

| 组件     | 推荐配置                                                     |
| -------- | ------------------------------------------------------------ |
| CPU      | Intel(R) Core(TM) i7-7700K CPU @ 4.20GHz                     |
| Memory   | 32GB                                                         |
| OS       | Ubuntu 18.04                                                 |
| Software | Docker >= 19.03<br />Docker Compose >= 1.25.0<br />Python >= 3.5<br />Phantoscope 0.1.0 |

## 2 数据准备

本文使用的家具图片整理自互联网，图片压缩包已经上传至百度网盘，下载链接及提取码如下：

链接：https://pan.baidu.com/s/19dUIPPBt-cvU1v8vj2XfJw   提取码：h09j

## 3 部署流程

1. 下载 Phantoscope：

```bash
$ git clone https://github.com/zilliztech/phantoscope.git && cd phantoscope
```

2. 设置环境变量：

```bash
$ export LOCAL_ADDRESS=$(ip a | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'| head -n 1)
```

3. 启动 Phantoscope 容器：

```bash
$ docker-compose up -d
```

4. 检查所有容器状态：

```bash
$ docker-compose ps
```

预期得到如下输出：

```bash
Name                   Command                          State   Ports
----------------------------------------------------------------------------------------------------------------
phantoscope_api_1      /usr/bin/gunicorn3 -w 4 -b ...   Up      0.0.0.0:5000->5000/tcp
phantoscope_milvus_1   /var/lib/milvus/docker-ent ...   Up      0.0.0.0:19530->19530/tcp, 0.0.0.0:8080->8080/tcp
phantoscope_minio_1    /usr/bin/docker-entrypoint ...   Up      0.0.0.0:9000->9000/tcp
phantoscope_mysql_1    docker-entrypoint.sh mysqld      Up      0.0.0.0:3306->3306/tcp
phantoscope_vgg_1      python3 server.py                Up      0.0.0.0:50001->50001/tcp
```

5. 准备环境
 ```bash
# 运行 scripts 文件夹下的 prepare.sh 脚本。该脚本注册了一个 operator，并以该 operator 创建一个 pipeline，并根据该 pipeline 创建了一个名为 example_app 的 application.
   
$ chmod +x scripts/prepare.sh
$ ./scripts/prepare.sh
 ```

6. 导入家具图片

 ```bash
$ unzip furniture.zip -d /tmp/
$ pip3 install requests tqdm
$ python3 scripts/load_data.py -s $LOCAL_ADDRESS:5000 -a example_app -p example_pipeline -d /tmp/furniture
 ```

## 4 界面展示

1. 启动 Phantoscope Preview 前端

```bash
$ docker run -d -e API_URL=http://$LOCAL_ADDRESS:5000 -p 8000:80 phantoscope/preview:latest
```

2. 浏览器打开 127.0.0.1:8000

<img src="jiaju_web.gif" width = "800" height = "500" alt="系统架构图" align=center />

