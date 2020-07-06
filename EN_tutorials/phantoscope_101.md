# Phantoscope Installation and Use 

## Summary

Phantoscope is a cloud-native image search engine based on Milvus and deep learning. It uses deep learning models, flexible combinations of different image processing techniques, and the powerful empowerment of the Milvus vector search engine to provide a unified interface for high-performance image search engine.

Fully compatible with mainstream deep learning frameworks such as Tensorflow, Pytorch TensorRT, ONNX and XGBoost.

Provide GUI to display search results and manage Phantoscope resources.

[Details of Phantoscope Projects](https://github.com/zilliztech/Phantoscope/tree/0.1.0)

This article will show you how to quickly install the Phantoscope image search engine and build an image search application with Phantscope.

## Environment Preparation

- Docker >= 19.03
- Docker Compose >= 1.25.0
- Python >= 3.5

## Install

1. Download Phantoscope:

```shell
$ git clone https://github.com/zilliztech/Phantoscope.git
$ cd Phantoscope
```

2. Set up the environment:

```shell
$ export LOCAL_ADDRESS=$(ip a | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'| head -n 1)
```

3. Start up Phantoscope containers:

```shell
$ docker-compose up -d
```

4. Check the status of all containers：

```shell
$ docker-compose ps
```

*You are expected to see the following output:*

```
Name                   Command                          State   Ports
-----------------------------------------------------------------------------------------
Phantoscope_api_1      /usr/bin/gunicorn3 -w 4 -b ...   Up      0.0.0.0:5000->5000/tcp
Phantoscope_Milvus_1   /var/lib/Milvus/docker-ent ...   Up      0.0.0.0:19530->19530/tcp, 0.0.0.0:8080->8080/tcp
Phantoscope_minio_1    /usr/bin/docker-entrypoint ...   Up      0.0.0.0:9000->9000/tcp
Phantoscope_mysql_1    docker-entrypoint.sh mysqld      Up      0.0.0.0:3306->3306/tcp
Phantoscope_vgg_1      python3 server.py                Up      0.0.0.0:50001->50001/tcp
```

The above outputs shows that five containers were launched in this project.

| Container            | Function                                                     |
| -------------------- | ------------------------------------------------------------ |
| Phantoscope_api_1    | This container provides all APIs for phantscope. [See RESTful API  for more details](https://app.swaggerhub.com/apis-docs/phantoscope/Phantoscope/0.1.0). |
| Phantoscope_milvus_1 | This container starts the Milvus service, which is used to store the vectors that the image is converted to, as well as to do vector similarity searches. |
| Phantoscope_minio_1  | This container provides MinIO object storage services for storing imported images. |
| Phantoscope_mysql_1  | This container starts the Mysql service for the storage of structured data. |
| Phantoscope_vgg_1    | This container provides the Vgg service and is responsible for vectorizing the image. |

> The startup of the above containers specifies where the data in the three containers, `Phantoscope_milvus_1` , `Phantoscope_mysql_1 `, and `Phantoscope_minio_1` , is stored on the physical machine. Specifying where data is stored on the physical machine can be accomplished by modifying the `volumes` in docker-compose.yml. The data in this project is stored in the **/mnt/om** path by default.



## Launching an application

1. Run the prepare.sh script in the scripts folder.

```shell
$ chmod +x scripts/prepare.sh
$ ./scripts/prepare.sh
```

> The script registers an Operator, creates a Pipeline from that Operator, and then creates an application named example_app from that Pipeline.
>
> This Operator refers to the container Phantoscope_vgg_1 started above. The Operator in Phantoscope provides the service to vectorize the image. After an Operator has been started, the Operator needs to be registered. The script prepare.sh registers the above-started Phantoscope_vgg_1 to Phantoscope. For more information, please refer to [What is an Operator?](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/en/tutorials/operator.md).
>
> The Pipeline is used in Phatoscope to group Operator, and is an abstraction of the data processing flow. This step creates a Pipeline with the Operator registered above.For more information, please refer to [What is a pipeline?](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/en/tutorials/pipeline.md)
>
> The Application corresponds to the actual business scenario. After the Application is created, you can import and query the pictures. For more information, please refer to [What is an application?](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/en/tutorials/application.md)
>
> In Phantoscope, several Operator implementations using open source models are available. You can also create an Operate with your own model and register it in Phantoscope. How to register a new Operator, create a Pipeline, and create an Application in Phantoscope (the steps this script implements) can refer to [create_application.md.](create_application.md)



2. Download and decompress the dataset

```shell
$ curl http://cs231n.stanford.edu/coco-animals.zip
$ unzip coco-animals.zip
```

> This dataset is derived from portions of the mscoco dataset.



3. Import image data

```shell
$ pip3 install requests tqdm
$ python3 scripts/load_data.py -s $LOCAL_ADDRESS:5000 -a example_app -p example_pipeline -d coco-animals
```

> Use the script load_data.py to import the downloaded dataset into the Application of example_app.
>
> | Parameter | Description                                                  |
> | --------- | ------------------------------------------------------------ |
> | -s        | This parameter specifies the IP and port where the above container phantoscope_api_1 service is located. |
> | -a        | This parameter specifies the name of the Application to import the data into. |
> | -p        | This parameter specifies the name of the used Pipeline.      |
> | -d        | This parameter specifies the name of the image to be imported. |
>

In addition to importing image data via this script, it can also be imported via curl.

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



4. Launch the front-end Phantoscope Preview 

This step will launch the Phantoscope's front-end for image search. For more information about front-end Preview, please refer to [Preview](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/en/tutorials/preview.md).

```shell
$ docker run -d -e API_URL=http://$LOCAL_ADDRESS:5000 -p 8000:80 Phantoscope/preview:latest
```

> | Parameter | Description                                                  |
>| --------- | ------------------------------------------------------------ |
> | -e        | This parameter specifies the IP and port where the above container phantoscope_api_1 service is located. |
> | -p        | This parameter maps the port on which the front-end interface provides services. |
> 

After completing the above steps, open your browser and type 127.0.0.1:8000. The interface appears as follows. Click the search button in the upper left corner to experience the newly built Image Search project.

![1592898199](../tutorials/pic/1592898199.png)

In addition to searching images with Preview we offer. You can also use curl to do a search.

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

















