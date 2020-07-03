# 使用内置 Operator 创建 Application

## 概述

本文将详细介绍如何在Phantoscope中通过内置的 Operator 来创建 Application.

## 环境准备

- Docker >= 19.03
- Docker Compose >= 1.25.0
- Python >= 3.5

## 安装 Phantoscope

> 如果已经安装了Phantoscope，则可以跳过该过程。

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
Phantoscope_milvus_1   /var/lib/milvus/docker-ent ...   Up      0.0.0.0:19530->19530/tcp, 0.0.0.0:8080->8080/tcp
Phantoscope_minio_1    /usr/bin/docker-entrypoint ...   Up      0.0.0.0:9000->9000/tcp
Phantoscope_mysql_1    docker-entrypoint.sh mysqld      Up      0.0.0.0:3306->3306/tcp
Phantoscope_vgg_1      python3 server.py                Up      0.0.0.0:50001->50001/tcp
```



## 构建一个应用

完成 Phantoscope 安装后，即可通过启动并注册 Operator、创建 Piplline、创建 Application 来构建一个完整的以图搜图应用。

### 启动 Operator

Operator 是 Phantoscope 中的工作单元，负责将输入的图片向量化，Phantoscope 提供了多个使用不同模型实现的 Operator,  这些 Operator 详情可参考文档 [Phantoscope 内置 Operator](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/zh-CN/tutorials/operator.md)。

> 您也可以使用自己的模型来实现一个Operator，如何将自己的模型在 Phantoscope 中创建一个 Operator 可参考文档 [创建 Operator, 实现自定义模型](create_operator.md)。

在 Phantoscope 中，Operator 可分为 Processor 和 Encoder 两类。Processor 通常负责对图片数据做进一步的处理。比如 Processor 接收了一张图片，然后将图片中的人脸数据提取出来，再将人脸的数据发送出去。通常来说 Processor 接收的数据与发送的数据都是同一种类型的。Encoder 是 Operator 的最后一环，Encoder 会将非结构化的数据转变成向量或者是标签。

本文将以 Phantoscope 中内置的 SSD-object-detector 和 Xception 这两个 Operator 为例，讲解如何在 Phantoscope 中启动并注册 Operator. 本项目中使用了两个 Operator 来构建一个应用，你也可以仅使用一个 Operator （仅使用一个 Operator时，该 Operator 为 Encoder 类型）来负责将图片向量化。

SSD-object-detector 能够检测图片中的物体，并返回检测到的图片中的一组物体，属于 Processor这一类。

Xception 对输入的图片进行 embedding，得到表征图片的特征向量，其属于 Encoder 这一类。

```shell
$ export LOCAL_ADDRESS=$(ip a | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'| head -n 1)
# 启动 SSD-object-detector
$ docker run -d -p 50010:50010 -e OP_ENDPOINT=${LOCAL_ADDRESS}:50010 psoperator/ssd-detector:latest
# 启动 Xception
$ docker run -d -p 50011:50011 -e OP_ENDPOINT=${LOCAL_ADDRESS}:50011 psoperator/xception-encoder:latest
```

> 该步骤启动了上述提到的两个 Operator，并映射了其提供服务的端口 50010 和 50011.
>
> docker ps 查看上述容器是否启动成功
>
> ```
> $ docker ps                                                                                            
> CONTAINER ID        IMAGE                                      COMMAND                  CREATED             STATUS              PORTS                                              NAMES
> 05e666f48f5f        psoperator/xception-encoder:latest         "python3 server.py"      9 seconds ago       Up 9 seconds        0.0.0.0:50011->50011/tcp, 50012/tcp                happy_ellis
> c4dd13b3fc5d        psoperator/ssd-detector:latest             "python3 server.py"      15 seconds ago      Up 14 seconds       0.0.0.0:50010->50010/tcp, 51002/tcp                keen_leavitt
> ```



### 注册Operator

当 Phantosscope 启动时是没有 Operator 的，在当前的版本中如果你想在 Phantoscope 中使用 Operator 需要先将启动好的 Operator 手动注册到 Phantoscope 中。

本步骤将上述启动的两个 Operator 分别注册到 Phantoscope 中。

通过向 `/v1/operator/regist`这个 API 发送注册请求：

```shell
# register ssd-detector to phantoscope with exposed 50010 port and a self-defined name 'ssd_detector'
$ curl --location --request POST ${LOCAL_ADDRESS}':5000/v1/operator/regist' \
--header 'Content-Type: application/json' \
--data '{
    "endpoint": "'${LOCAL_ADDRESS}':50010",
    "name": "ssd_detector"
}'

# register xception-encoder to phantoscope with exposed 50011 port and a self-defined name 'xception'
$ curl --location --request POST ${LOCAL_ADDRESS}':5000/v1/operator/regist' \
--header 'Content-Type: application/json' \
--data '{
    "endpoint": "'${LOCAL_ADDRESS}':50011",
    "name": "xception"
}'
```

> `endpoint`: 绑定 Operator 的服务端口。上述启动的 ssd-detector 这个 Operator 提供的服务端口 50010，故在注册 ssd-detector 这个 Operator 时，此处应填写 50010. xception-encoder 这个 Operator 提供的服务端口 50011，故在注册 xception-encoder 这个 Operator 时，此处应填写 50011.
>
> 此处的 endpoint 会被 Phantoscope 用来与 Operator 进行通讯,故不能填写为 127.0.0.1,应该填写为 192 或 10 开头的内网地址，确保在 phantoscope 可以访问。
>
> `name`: 自定义 Operator 名称。本处将  ssd-detector 这个 Operator 以 ssd-detector 这个名字注册到 Phantoscope 中，将  xception-encoder 这个 Operator 以 xception 这个名字注册到 Phantoscope 中。注意该名称不可和其他已经存在的其他 Operator 的名称重复。



### 创建Pipeline

pipeline 从 application 中接收数据然后将数据交给第一个 operator,等待第一个 operator 的返回, 获取到返回值之后将返回值作为输入交给下一个 operator,直到运行完最后一个 operator。关于 Pipeline 的详细描述请参考 [什么是 Pipeline.](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/zh-CN/tutorials/pipeline.md)

此处将创建一条包含 ssd_detector 和 xception 这两个 Operator 的 Pipeline。

```shell
# create a pipeline with necessary information
$ curl --location --request POST ${LOCAL_ADDRESS}':5000/v1/pipeline/object_pipeline' \
--header 'Content-Type: application/json' \
--data '{
	"input": "image",
	"description": "object detect and encode",
	"processors": "ssd_detector",
	"encoder": "xception",
	"indexFileSize": 1024
}'
```

> `${LOCAL_ADDRESS}':5000/v1/pipeline/object_pipeline'`: object_pipeline 定义了新创建的 Pipeline 的名称。注意该名称不可和其他已经存在的其他 Pipeline 的名称重复。
>
> `processors`: 此处指定创建的这条 Pipeline 包含的 Operator 中的 processors 的名称。如若没有启动 processors 这个 Pipeline，这里可写为`""`。
>
> `encoder`: 此处指定创建的这条 Pipeline 包含的 Operator 中的 encoder 的名称。
>



### 创建 Application

本步骤将以上述创建的 object_pipeline 来构建一个 Phantoscope Application。关于 Application 的详细描述请参考 [什么是Application](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/zh-CN/tutorials/application.md)。

```shell
# create an application with a self-define field name assocatied with pipeline created in step3 
$ curl --location --request POST ${LOCAL_ADDRESS}':5000/v1/application/object-example' \
--header 'Content-Type: application/json' \
--data '{
    "fields":{
        "object_field": {
            "type": "object",
            "pipeline": "object_pipeline"
        }
    },
    "s3Buckets": "object-s3"
}'
```

> `${LOCAL_ADDRESS}':5000/v1/application/object-example'`:  命令中的 object-example 是自定义 Application 的名称。注意该名称不可和其他已经存在的其他 Application 的名称重复。
>
> `object_field`: 自定义的字段名称，保存着 object_pipeline 处理后的结果
>
> `Pipeline` 这里指定了新创建的 Application 要绑定的 Pipeline 的名称。
>
> `s3Buckets`: 将图片存储在名为 object-s3 的 S3 bucket 中。



## 使用

### 数据导入

1. 下载数据

```shell
$ curl http://cs231n.stanford.edu/coco-animals.zip
$ unzip coco-animals.zip
```

2. 导入数据

```shell
$ pip3 install requests tqdm
$ python3 scripts/load_data.py -d /tmp/coco-animals/train -a object-example -p object_pipeline
```

等待运行结束，上传结果如下所示。

```
upload url is http://127.0.0.1:5000/v1/application/object-example/upload
allocate 4 processes to load data, each task including 200 images
Now begin to load image data and upload to phantoscope: ...
100%|████████████████████████████████████████████████████████████████████████████████| 800/800 [03:16<00:00,  4.07it/s]
upload 800 images cost: 196.832s 
All images has been uploaded: success 754, fail 46
Please read file 'path_to_error_log' to check upload_error log.
```

> 如果在导入的图片中没有检测到符合的物体，该张图片的导入会触发导入失败的报错。但不影响其他图片的导入。



### 查询

启动 Phantoscope 的前端进行图片搜索。关于前端界面 Preview 的更多详细说明请参考 [Preview 说明](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/zh-CN/tutorials/preview.md)。

```shell
$ docker run -d -e API_URL=http://$LOCAL_ADDRESS:5000 -p 8000:80 Phantoscope/preview:latest
```

> 如果之前已经启动了 Preview，则不用重新启动了。可以直接在网页中访问已经启动好的 Preview。在前端页面左上角选择名为 object-example 的 Application 即可访问刚刚构建完成的这个 Application。



## 部分 API 说明

上述讲了如何在 Phantoscope 中，注册 Operator、创建 Pipeline 和 Application。那接下来将如何查看和删除 Phantoscope 中的 Operator、Pipeline 和 Application。 更多关于 API 的详细描述请参考 [Phantoscope API](https://app.swaggerhub.com/apis-docs/phantoscope/Phantoscope/0.1.0#/)。

### 查看 Operator、Pipeline、Application

**查看 Phantoscope 中注册的的所有 Operator**

```shell
$ curl -X GET "http://127.0.0.1:5000/v1/operator/" -H "accept: application/json"
```

**查看 Phantoscope 中创建的的所有 Pipeline**

```shell
$ curl -X GET "http://127.0.0.1:5000/v1/pipeline/" -H "accept: application/json"
```

**查看 Phantoscope 中创建的的所有 Application**

```shell
$ curl -X GET "http://127.0.0.1:5000/v1/application/" -H "accept: application/json"
```

### 删除 Operator、Pipeline、Application

**删除一个在 Phantoscope 中注册的 Operator。**

```shell
$ curl -X DELETE "http://127.0.0.1:5000/v1/operator/vgg19" -H "accept: application/json"
```

> 上述语句删除了一个名为 vgg19 的 Operator.

**删除一个 Phantoscope 中的 Pipeline。**

```shell
$ curl -X DELETE "http://127.0.0.1:5000/v1/pipeline/vgg19_pipeline" -H "accept: application/json"
```

> 上述语句删除了一个名为 vgg19_pipeline 的Pipeline。

**删除一个 Phantoscope 中的 Application。**

在删除一个 Application 之前，需要先删除该 Application 中的 entity（也就是这个 Application 中导入的图片数据。）

1. 查看该 Application 下的 entity

```shell
# 查看该 Application 下的 entity
$ curl -X GET "http://127.0.0.1:5000/v1/application/example_app/entity?num=100" -H "accept: application/json"
```

> 该接口可以查看一个 Application 中已有的 entity 的 id。一个 entity 对应一张图片。

2. 删除 entity

```shell
# 删除 entity
$ curl -X DELETE "http://127.0.0.1:5000/v1/application/example_app/entity/1592888165100064000" -H "accept: application/json"
```

> 删除entity，需要传入两个参数。一个是 Application 的名称，也就是上面命令中的 `example_app`, 一个是要删除的 entity 对应的 id，也就是上面个命令中的 `1592888165100064000`。如果要删除一个 Application 中的某张图片，可以通过该接口实现。

3. 删除 Application

```shell
# 删除 Application
$ curl -X DELETE "http://127.0.0.1:5000/v1/application/example_app" -H "accept: application/json"
```

> 该命令删除了一个名为 `example_app` 的 Application。在目前版本中，需要先删除 Application 中的所有 entity 才能删除该 Application 。
