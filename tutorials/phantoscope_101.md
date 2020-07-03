# Phantoscope 安装与使用

## 概述

Phantoscope 是一个基于 Milvus 与深度学习的云原生图像搜索引擎。利用深度学习模型，灵活组合不同的图片处理技术，加上 Milvus 向量搜索引擎的强大赋能后，提供统一接口的高性能图像搜索引擎。

完全兼容 Tensorflow Pytorch TensorRT ONNX XGBoost 等主流深度学习框架。

提供 GUI 展示搜索效果、管理 Phantoscope 资源。

[Phantoscope 项目详情](https://github.com/zilliztech/Phantoscope/tree/0.1.0)。

本文将介绍如何快速安装 Phantoscope 图像搜索引擎，并使用 phantscope 构建一个图像搜索的应用。

## 环境准备

- Docker >= 19.03
- Docker Compose >= 1.25.0
- Python >= 3.5

## 安装

1. 拉取源码

```shell
$ git clone https://github.com/zilliztech/Phantoscope.git
$ cd Phantoscope
```

2. 设置环境变量

```shell
$ export LOCAL_ADDRESS=$(ip a | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'| head -n 1)
```

3. 启动 Phantoscope 容器

```shell
$ docker-compose up -d
```

4. 检查所有容器状态：

```shell
$ docker-compose ps
```

*预期得到如下输出：*

```
Name                   Command                          State   Ports
-----------------------------------------------------------------------------------------
Phantoscope_api_1      /usr/bin/gunicorn3 -w 4 -b ...   Up      0.0.0.0:5000->5000/tcp
Phantoscope_Milvus_1   /var/lib/Milvus/docker-ent ...   Up      0.0.0.0:19530->19530/tcp, 0.0.0.0:8080->8080/tcp
Phantoscope_minio_1    /usr/bin/docker-entrypoint ...   Up      0.0.0.0:9000->9000/tcp
Phantoscope_mysql_1    docker-entrypoint.sh mysqld      Up      0.0.0.0:3306->3306/tcp
Phantoscope_vgg_1      python3 server.py                Up      0.0.0.0:50001->50001/tcp
```

上述输出可以看到，本项目中一共启动了五个容器。

| 容器名               | 功能                                                         |
| -------------------- | ------------------------------------------------------------ |
| Phantoscope_api_1    | 该容器提供 phantscope 的所有 API，[详情参考 RESTful API 文档](https://app.swaggerhub.com/apis-docs/phantoscope/Phantoscope/0.1.0)。 |
| Phantoscope_milvus_1 | 该容器启动 Milvus 服务，用来存储图片转化成的向量，以及做向量相似度搜索。 |
| Phantoscope_minio_1  | 该容器提供MinIO对象存储服务，用于存储导入的图片。            |
| Phantoscope_mysql_1  | 该容器启动 Mysql 服务，用结构化数据的存储。                        |
| Phantoscope_vgg_1    | 该容器提供 vgg 服务，容器负责将图片向量化。                  |

> 在上述容器启动时，指定了 Phantoscope_milvus_1 和 Phantoscope_mysql_1 以及 Phantoscope_minio_1 三个容器中的数据在物理机上的存储位置。可以通过修改文件 docker-compose.yml 中的参数 `volumes` 来指定数据在物理机的存储位置。本项目中的数据默认存储在 **/mnt/om** 路径下。



## 启动一个应用

1. 运行 scripts 文件夹下的 prepare.sh 脚本。

```shell
$ chmod +x scripts/prepare.sh
$ ./scripts/prepare.sh
```

> 该脚本注册了一个 Operator ，并以该 Operator 创建一个 Pipeline，然后根据该 Pipeline 创建了一个名为 example_app 的 Application。
>
> 这里的 Operator 指是上述启动的的容器Phantoscope_vgg_1，Phantoscope中的 Operator 提供将图片向量化的服务。在启动了一个 Operator 后，还需要注册该 Operator。在脚本 prepare.sh 中，完成了将上面启动的 Phantoscope_vgg_1 注册到了Phantoscope中。Operator 的详解请参考 [什么是 Operator](https://github.com/zilliztech/Phantoscope/blob/0.1.0/docs/site/zh-CN/tutorials/operator.md).
>
> Pipeline 是 phatoscope 中用来组合 Operator 的，是对数据处理流程的抽象。本步骤以上述注册好的 Operator 创建了一个 Pipeline. 关于更多 Pipeline 的详解请参考 [什么是 Pipeline.](https://github.com/zilliztech/Phantoscope/blob/0.1.0/docs/site/zh-CN/tutorials/pipeline.md)
>
> Application 对应的是实际业务场景。创建完成 Application 后即可实现图片的导入和查询等操作了。关于更多 Application 的详解请参考 [什么是Application.](https://github.com/zilliztech/Phantoscope/blob/0.1.0/docs/site/zh-CN/tutorials/application.md)
>
> 在 Phantoscope 中，提供了多种将图片向量化的开源的深度学习模型实现的 Operator，你可以将我们提供的其他 Operator 注册到 Phantoscope中。也可以用自己的模型创建一个 Operate并注册到 Phantoscope 中。如何在 Phantoscope 中注册一个新的 Operator、创建 Pipeline、并创建 Application (也就是该脚本实现的步骤)可以参考文档 [通过 Phantoscope 创建 Application.](Create_Application.md)



2. 下载并解压数据集

```shell
$ curl http://cs231n.stanford.edu/coco-animals.zip -o ./coco-animals.zip
$ unzip coco-animals.zip
```

> 本数据集来源于 mscoco 数据集的部分。



3. 导入图片数据

```shell
$ pip3 install requests tqdm
$ python3 scripts/load_data.py -s $LOCAL_ADDRESS:5000 -a example_app -p example_pipeline -d coco-animals
```

> 使用脚本 load_data.py 将下载好的数据集导入上述创建的名为 example_app 的 Application 中。
>
> | 参数 | 说明                                                         |
> | ---- | ------------------------------------------------------------ |
> | -s   | 该参数指定了上述容器 phantoscope_api_1 服务所在的 IP 和端口。 |
> | -a   | 该参数指定要将数据导入的 Application 的名称。                |
> | -p   | 该参数指定了使用到的 Pipeline 的名称。                       |
> | -d   | 该参数指定了要导入图片的路径。                               |
>

除了通过该脚本导入图片数据，也可以通过 curl 导入。

```shell
$ curl --location --request POST $LOCAL_ADDRESS':5000/v1/application/example_app/upload' \
--header 'Content-Type: application/json' \
--data "{
    \"fields\": {
        \"example_field\": {
            \"url\": \"https://tse2-mm.cn.bing.net/th/id/OIP.C3pWPyFPhBMiBeWoncc24QHaCq?w=300&h=108&c=7&o=5&dpr=2&pid=1.7\"
        }
    }
}"
```



4. 启动前端 Phantoscope Preview 

本步骤将启动 Phantoscope 的前端进行图片搜索。关于前端界面 Preview 的更多详细说明请参考 [Preview 说明](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/zh-CN/tutorials/preview.md)。

```shell
$ docker run -d -e API_URL=http://$LOCAL_ADDRESS:5000 -p 8000:80 Phantoscope/preview:latest
```

> | 参数 | 说明                                                         |
>| ---- | ------------------------------------------------------------ |
> | -e   | 该参数指定了上述容器 phantoscope_api_1 服务所在的 IP 和端口。 |
> | -p   | 该参数映射前端界面提供服务的端口                             |
> 

完成上述步骤后，打开浏览器，输入127.0.0.1:8000。界面显示如下，点击左上角的搜索按钮即可体验刚搭建好的以图搜图项目。

![1592898199](pic/1592898199.png)

除了通过我们提供的前端 Preview 来搜索图片。您也可以通过 curl 来进行搜搜。

```shell
$ curl --location --request POST $LOCAL_ADDRESS':5000/v1/application/example_app/search' \
--header 'Content-Type: application/json' \
--data "{
    \"fields\": {
        \"example_field\": {
            \"url\": \"https://tse2-mm.cn.bing.net/th/id/OIP.C3pWPyFPhBMiBeWoncc24QHaCq?w=300&h=108&c=7&o=5&dpr=2&pid=1.7\"
        }
    },
    \"topk\": 2
}"
```

















