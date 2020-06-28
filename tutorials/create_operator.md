# 创建 Operator 实现自定义模型

Phantoscope 是一个基于 Milvus 与深度学习的云原生图像搜索引擎。我们知道在 [Phantscop 快速开始](https://github.com/zilliztech/phantoscope/tree/0.1.0/docs/site/zh-CN/quickstart) 中使用了 Vgg16 模型来获取表征图片的特征向量，那么如果要换成准确率更高的 ResNet 模型来 [自定义 Operator](https://github.com/zilliztech/phantoscope/blob/0.1.0/operators/HowToAddAnOperator.md) ，应该怎么实现呢？

由于 Phantoscope 完全兼容 Tensorflow、Pytorch、TensorRT、ONNX，XGBoost 等主流深度学习框架，那么如果你想使用自己的深度学习模型可以参考本教程。

## 1. 准备工作

- 具有一定能力的 Python 开发能力

- 了解 gRPC 与 protobuf

- 掌握基础的 Docker 命令

- 熟悉 [Phantoscop 基本概念](https://github.com/zilliztech/phantoscope/blob/0.1.0/README_CN.md#基本概念)

- 成功运行 [Phantscop 快速开始](https://github.com/zilliztech/phantoscope/tree/0.1.0/docs/site/zh-CN/quickstart) ，查看所有容器状态：

```shell
$ docker-compose ps
# You are expected to see the following output
 Name                   Command                          State   Ports
 -----------------------------------------------------------------------------------------
 phantoscope_api_1      /usr/bin/gunicorn3 -w 4 -b ...   Up      0.0.0.0:5000->5000/tcp
 phantoscope_milvus_1   /var/lib/milvus/docker-ent ...   Up      0.0.0.0:19530->19530/tcp, 0.0.0.0:8080->8080/tcp
 phantoscope_minio_1    /usr/bin/docker-entrypoint ...   Up      0.0.0.0:9000->9000/tcp
 phantoscope_mysql_1    docker-entrypoint.sh mysqld      Up      0.0.0.0:3306->3306/tcp
 phantoscope_vgg_1      python3 server.py                Up      0.0.0.0:50001->50001/tcp
```




## 2. 自定义 Operator

接下来我们将实现基于 ResNet 算法自定义 Operator 实现以图搜图，在 **phantoscope/operators/example-custom-operaotor** 目录下展示了最基础的 Operator 结构：

1. 在 **data** 目录下通常存放用于下载模型文件的的脚本，在制作镜像时用于下载模型
2. 在 **rpc** 目录下是 gRPC 生成的 python 文件
3. 主目录下的 **server** 文件通常用来保存 gRPC server 的相关逻辑
4. 主目录下的 **custom_operator** 文件用来实现 rpc 文件需要的接口

我们将基于这个结构来创建 Operator 实现自定义 resnet50-encoder 模型。

### 2.1 创建目录

基于 **example-custom-operaotor** 内容创建 **resnet50-encoder** 目录：

```bash
$ cp -rf example-custom-operator resnet50-encoder
$ cd resnet50-encoder
```

### 2.2 自定义模型

#### 2.2.1 下载模型

- 编辑修改 **data/prepare_model.sh** 脚本，通过 `wget` 命令下载模型：

```bash
file=resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5 url=https://github.com/fchollet/deep-learning-models/releases/download/v0.1/resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5

if [[ ! -f "${file}" ]]; then
   mkdir -p models
   echo "[INFO] Model tar package does not exist, begin to download..."
   wget ${url} -O ${file}
   echo "[INFO] Model tar package download successfully!"
fi

if [[ -f "${file}" ]];then
   echo "[INFO] Model has been prepared successfully!"
   exit 0
fi
```

  > 请确保运行该脚本可以下载模型文件，如果你使用自己的模型，请修改脚本中的 `file` 和 `url` 参数为自己的模型名字和下载地址。

#### 2.2.2 自定义 Operator

- **custom_operator.py** 中实现的接口介绍：

| 函数名 | 描述 |
| -------------- | ----------- |
| __ init __(self) | 模型初始化函数 |
| run(self, images, urls) | 模型 encode 函数，参数包括图片文件或图片 urls <br />函数返回结果是模型将图片转换 list 类型的特征向量 |
| name(self) | 返回自定义 Operator 的名字 |
| type(self) | 返回自定义 Operator 的类型，如 encoder 或 processor |
| input(self) | 返回自定义 Operator 的模型输入，如 image |
| output(self) | 返回自定义 Operator 的模型输出，如 vector |
| dimension(self) | 返回自定义 Operator 的模型输出向量的维度，如2048 |
| metric_type(self) | 返回自定义 Operator 的模型 metric，如 L2(欧氏距离) |

- 本文基于 ResNet50 自定义 `CustomOperator`，参考 [resnet50_custom_operator.py](./script/custom_operator.py) 代码:

```bash
# download custom_operator.py to resnet50-encoder floder
$ mv custom_operator.py custom_operator.py.bak
$ wget https://raw.githubusercontent.com/zilliztech/phantoscope-bootcamp/master/tutorials/script/custom_operator.py
```

- 根据 **custom_operator.py** 代码添加相关依赖，在 **requirements.txt, requirements-gpu.txt** 中添加：

```bash
Keras==2.3.1
tensorflow==1.14.0
grpcio==1.27.2
pillow
```

  > 如果你使用自己的模型，请修改 custom_operator.py 中的接口函数和 requirements.txt 中的相关依赖。

#### 2.2.3 调整 gRPC 服务

**server.py** 文件实现对自定义 Operator 的调用逻辑，我们需要根据自己定义的 Operator 类型调整 gRPC 服务，本文实现的是基于 ResNet 的 encoder 方法，那么将删除关于 processor 的代码模块：

```bash
# download server.py to resnet50-encoder floder
$ mv server.py server.py.bak
$ wget https://raw.githubusercontent.com/zilliztech/phantoscope-bootcamp/master/tutorials/script/server.py
```

> 如果你的模型实现的功能是 processor 类型，那么应该删除 encoder 的相关代码。 

### 2.3 构建 Docker 镜像

综上，通过修改 **data**、**server** 和 **custom_operator** 文件自定义了一个 Operactor 结构，接下来将运行 `make cpu` 命令构建自定义 Operator 的 Docker 镜像：

```bash
$ mv Makefile Makefile.bak
$ wget wget https://raw.githubusercontent.com/zilliztech/phantoscope-bootcamp/master/tutorials/script/Makefile
$ make cpu
```

 我们可以在 **Makefile** 中修改 `IMAGE_NAME` 自定义镜像名称，例如 `resnet50_encoder`，那么通过运行 `docker images` 命令可以看到有一个名为 `psoperator/resnet50_encoder:latest` 的镜像。

### 2.4 启动容器并验证

- 启动容器

```bash
$ docker run -p 52001:52001 -e OP_ENDPOINT=127.0.0.1:52001 -d psoperator/resnet50_encoder:latest
```

  该命令的参数介绍：

| 参数                               | 描述                                                         |
| ---------------------------------- | ------------------------------------------------------------ |
| -p 52001:52001                     | -p 表示端口映射，将本机的 52001 端口映射到 Docker 中的52001端口 |
| -e OP_ENDPOINT=127.0.0.1:52001     | -e 定义 Docker 的环境变量，容器的 OP_ENDPOINT 环境变量的端口需要与 -p 映射的 Docker 端口一致 |
| psoperator/resnet50_encoder:latest | Docker 镜像名称，请修改为上一步自定义的镜像名                |

  容器启动后可以运行 `docker logs <resnet50_encoder container id>` 查看状态。

- 验证容器

```bash
# Download and run the test_operator.py
$ wget https://raw.githubusercontent.com/zilliztech/phantoscope-bootcamp/master/tutorials/script/test_custom_operator.py
$ python3 test_custom_operator.py -e 127.0.0.1:52001
# You are expected to see the following output
INFO:root:Begin to test: endpoint-127.0.0.1:50013
INFO:root:Endpoint information: {'name': 'resnet50', 'endpoint': '192.168.1.85:50013', 'type': 'encoder', 'input': 'image', 'output': 'vector', 'dimension': '2048', 'metric_type': 'L2'}
INFO:root:Endpoint health: healthy
INFO:root:Result :
  vector size: 1;  data size: 0
INFO:root:  vector dim: 2048
INFO:root:All tests over.
```

> 运行测试脚本 -e 的参数与启动容器时的 `OP_ENDPOINT` 内容对应。
>
> 应该在启动容器后过约 3 分钟再运行验证代码，因为初始化 Operator 需要一些时间。



## 3. 注册 Operator

- 查看容器的运行状态，包括 [Phantoscope 快速开始](https://github.com/zilliztech/phantoscope/tree/0.1.0/docs/site/zh-CN/quickstart) 时启动的 5 个容器，以及上一步启动的自定义Operator 的容器。

```bash
$ docker ps                                                                                            
CONTAINER ID        IMAGE                                      COMMAND                  CREATED             STATUS              PORTS                                              NAMES
05e666f48f5f        psoperator/xception-encoder:latest         "python3 server.py"      9 seconds ago       Up 9 seconds        0.0.0.0:50011->50011/tcp, 50012/tcp                happy_ellis
c4dd13b3fc5d        psoperator/ssd-detector:latest             "python3 server.py"      15 seconds ago      Up 14 seconds       0.0.0.0:50010->50010/tcp, 51002/tcp                keen_leavitt
  09bd2658493b        psoperator/vgg16:latest                    "python3 server.py"      23 seconds ago      Up 22 seconds       0.0.0.0:50001->50001/tcp                           omnisearch_vgg_1
  0ce974dc8891        phantoscope/api-server:0.1.0               "/usr/bin/gunicorn3 …"   23 seconds ago      Up 22 seconds       0.0.0.0:5000->5000/tcp                             omnisearch_api_1
  3bf49c362d79        daocloud.io/library/mysql:5.6              "docker-entrypoint.s…"   26 seconds ago      Up 24 seconds       0.0.0.0:3306->3306/tcp                             omnisearch_mysql_1
  3f6f6750bc21        milvusdb/milvus:0.7.0-cpu-d031120-de409b   "/var/lib/milvus/doc…"   26 seconds ago      Up 23 seconds       0.0.0.0:8080->8080/tcp, 0.0.0.0:19530->19530/tcp   omnisearch_milvus_1
  f5e387c6016b        minio/minio:latest                         "/usr/bin/docker-ent…"   26 seconds ago      Up 24 seconds       0.0.0.0:9000->9000/tcp                             omnisearch_minio_1
  bedc9420d6d5        phantoscope/preview:latest                 "/bin/bash -c '/usr/…"   40 minutes ago      Up 40 minutes       0.0.0.0:8000->80/tcp                               brave_ellis
```

将 `resnet50-encoder` Operator 注册到 Phantoscope 中：

```bash
# register ssd-object-detector to phantoscope with exposed 50010 port and a self-defined name 'ssd_detector'
$ export LOCAL_ADDRESS=$(ip a | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'| head -n 1)
$ curl --location --request POST ${LOCAL_ADDRESS}':5000/v1/operator/regist' \
--header 'Content-Type: application/json' \
--data '{
    "endpoint": "'${LOCAL_ADDRESS}':52001",     
    "name": "resnet50-encoder"
}'
```

  > 端口 52001 是启动自定义 Operactor 容器时映射的端口。
  >
  >  `name` 参数 resnet50-encoder 是在 custom_operator.py 中定义的 Operator 名称。

  正确的运行结果会返回对应 Operator 的信息：

```bash
{"_name": "resnet50-encoder", "_backend": "ssd", "_type": "processor", "_input": "image", "_output": "images", "_endpoint": "192.168.1.192:52001", "_metric_type": "-1", "_dimension": -1}%  
```



## 4. 创建 Application

综上，我们已经将自定义的 Operator 注册到 Phantoscope 中了，接下来可以创建一个  Application 实现以图搜图，参考 [创建 Application](./object.md)。

> 在创建 Phantoscope Application 时我们已经在上一步完成了注册 Operator，而在接下来创建 Pipeline 时请**注意**修改 `encoder` 参数为 `resnet50-encoder`。



## 5. VGG 模型比对

本文实现了基于 ResNet 模型以图搜图，与 Vgg16 模型创建的 Application 搜索同一张图片的效果比对如下：

- Vgg 模型检索效果
- 自定义 Operator 检索效果（ResNet）

我们知道 Vgg 模型的准确率确实低于 ResNet，本文检索的效果也是后者更优。