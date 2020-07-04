# Using Phantoscope to Search Similar Furniture

This article shows how to use Phantoscope to build a image-based search system to find similar furniture.

## 1 Environment requirements

The following table lists the recommended configurations for building a similar furniture map system, which have been tested.

| Component | Recommended Configuration                                    |
| --------- | ------------------------------------------------------------ |
| CPU       | Intel(R) Core(TM) i7-7700K CPU @ 4.20GHz                     |
| Memory    | 32GB                                                         |
| OS        | Ubuntu 18.04                                                 |
| Software  | Docker >= 19.03<br />Docker Compose >= 1.25.0<br />Python >= 3.5<br />Phantoscope 0.1.0 |

## 2 Data Preparation

Our furniture images organized from the Internet, the image zip file has been uploaded to the Baidu Pan, download links and extraction code as follows.

link:https://pan.baidu.com/s/19dUIPPBt-cvU1v8vj2XfJw   code:h09j

## 3 Deployment Process

1. Download Phantoscope:

```bash
$ git clone -b 0.1.0 https://github.com/zilliztech/phantoscope.git && cd phantoscope
```

2. Set Environment Variables:

```bash
$ export LOCAL_ADDRESS=$(ip a | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'| head -n 1)
```

3. Run Phantoscope:

```bash
$ docker-compose up -d
```

4. Check the status of all containers

```bash
$ docker-compose ps
```

Expected outputs:

```bash
Name                   Command                          State   Ports
----------------------------------------------------------------------------------------------------------------
phantoscope_api_1      /usr/bin/gunicorn3 -w 4 -b ...   Up      0.0.0.0:5000->5000/tcp
phantoscope_milvus_1   /var/lib/milvus/docker-ent ...   Up      0.0.0.0:19530->19530/tcp, 0.0.0.0:8080->8080/tcp
phantoscope_minio_1    /usr/bin/docker-entrypoint ...   Up      0.0.0.0:9000->9000/tcp
phantoscope_mysql_1    docker-entrypoint.sh mysqld      Up      0.0.0.0:3306->3306/tcp
phantoscope_vgg_1      python3 server.py                Up      0.0.0.0:50001->50001/tcp
```

5. Prepare environment
 ```bash
# Run the prepare.sh script in the scripts folder. The script registers an operator and creates a pipeline with that operator. Then you can create an application called example_app from this pipeline. 
   
$ chmod +x scripts/prepare.sh
$ ./scripts/prepare.sh
 ```

6. Import furniture pictures

 ```bash
$ unzip furniture.zip -d /tmp/
$ pip3 install requests tqdm
$ python3 scripts/load_data.py -s $LOCAL_ADDRESS:5000 -a example_app -p example_pipeline -d /tmp/furniture
 ```

## 4 Interface Display

1. Run the front end of Phantoscope Preview

```bash
$ docker run -d -e API_URL=http://$LOCAL_ADDRESS:5000 -p 8000:80 phantoscope/preview:latest
```

2. Access 127.0.0.1:8000 with browser

<img src="./pic/jiaju_web.gif" width = "800" height = "500" alt="系统架构图" align=center />

