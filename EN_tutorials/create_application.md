# Create Applications with the in-built Operator

This article describes in detail how to create applications in Phantoscope with the built-in Operator.

## Preparation

- Docker >= 19.03
- Docker Compose >= 1.25.0
- Python >= 3.5

## Install Phantoscope

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

4. Check the status of all containers

```shell
$ docker-compose ps
```

You are expected to see the following output:

```
Name                   Command                          State   Ports
-----------------------------------------------------------------------------------------
Phantoscope_api_1      /usr/bin/gunicorn3 -w 4 -b ...   Up      0.0.0.0:5000->5000/tcp
Phantoscope_milvus_1   /var/lib/milvus/docker-ent ...   Up      0.0.0.0:19530->19530/tcp, 0.0.0.0:8080->8080/tcp
Phantoscope_minio_1    /usr/bin/docker-entrypoint ...   Up      0.0.0.0:9000->9000/tcp
Phantoscope_mysql_1    docker-entrypoint.sh mysqld      Up      0.0.0.0:3306->3306/tcp
Phantoscope_vgg_1      python3 server.py                Up      0.0.0.0:50001->50001/tcp
```



## Create an Application

After completing the Phantoscope installation, you can build a complete image search application by starting and registering the Operator, creating the Pipeline, and creating the Application.

### Run Operator

The operator is the unit of work in Phantoscope and is responsible for vectorizing the input picture. Phantoscope provides a number of Operators which are implemented using different models, these Operators are detailed in [Phantoscope in-build Operator](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/en/tutorials/operator.md).

> You can also use your own model to implement an Operator. How to create an Operator from your model in Phantoscope can be found in [Create Operator to implement custom model](create_operator.md).

In Phantoscope, there are two types of Operators: Processor and Encoder. The Processor is usually responsible for further processing of the image data. For example, the Processor receives an image, extracts the face data from the image, and sends the data to the out. Usually, the data that the Processor receives and the data that it sends are of the same type. The Encoder is the last step in the Operator's chain, and the Encoder converts unstructured data into vectors or tags.

This article will take the two operators SSD-object-detector and Xception in-build Phantoscope as an example to explain how to start and register the operator in Phantoscope. Two Operators are used in this project to build an application, or you can use just one Operator (which is of type Encoder when using just one Operator) to be responsible for vectorizing the image.

The SSD-object-detector is able to detect objects in the picture and return a set of objects in the detected picture, which belongs to the category of Processor.

Xception embedding the input picture to get the feature vectors representing the picture, which belongs to the category of Encoder.

```shell
$ export LOCAL_ADDRESS=$(ip a | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'| head -n 1)
# Run SSD-object-detector
$ docker run -d -p 50010:50010 -e OP_ENDPOINT=${LOCAL_ADDRESS}:50010 psoperator/ssd-detector:latest
# Run Xception
$ docker run -d -p 50011:50011 -e OP_ENDPOINT=${LOCAL_ADDRESS}:50011 psoperator/xception-encoder:latest
```

> This step starts the two Operators mentioned above and maps the ports 50010 and 50011 on which they provide services.
>
> `docker ps`: check if the above container started successfully.
>
> ```
> $ docker ps                                                                                            
> CONTAINER ID        IMAGE                                      COMMAND                  CREATED             STATUS              PORTS                                              NAMES
> 05e666f48f5f        psoperator/xception-encoder:latest         "python3 server.py"      9 seconds ago       Up 9 seconds        0.0.0.0:50011->50011/tcp, 50012/tcp                happy_ellis
> c4dd13b3fc5d        psoperator/ssd-detector:latest             "python3 server.py"      15 seconds ago      Up 14 seconds       0.0.0.0:50010->50010/tcp, 51002/tcp                keen_leavitt
> ```



### Register Operator

There is no Operator when Phantosscope is started, in the current version if you want to use Operator in Phantoscope you need to register the started Operator manually in Phantoscope first.

This step registers the two Operators started above separately into the Phantoscope.

By sending a registration request to the API `/v1/operator/regist`:

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

> `endpoint`: Binds the Operator's service port. The Operator ssd-detector started above provides service port 50010, so when registering the Operator for ssd-detector, fill in here with 50010. Operator xception-encoder provides the service port 50011, so when registering the Operator for xception-encoder, fill in here with 50011. 
>
> The endpoint here is used by the Phantoscope to communicate with the Operator, so you can't fill in 127.0.0.1, you should fill in the intranet address starting with 192 or 10. Make sure the Phantoscope is accessible.
>
> `name`: Customize the Operator name. In this case, the Operator ssd-detector is registered as ssd-detector. Operator xception-encoder is registered to the Phantoscope under the name xception. Note that this name cannot be duplicated with the names of other Operators already in existence.



### Create Pipeline

Pipeline receives data from the application and gives it to the first operator, waits for the return of the first operator, and then takes the return value as input to the next operator until the last operator has been run. For more information, please refer to [What is a pipeline?](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/en/tutorials/pipeline.md)

The Pipeline is created that contains the two Operators ssd_detector and xception.

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

> `${LOCAL_ADDRESS}:5000/v1/pipeline/object_ pipeline`: object_pipeline defines the newly created Pipeline. Note that this name must not duplicate the names of other Pipelines that already exist.
>
> `processors`: This specifies that the Pipeline created here contains the Operator processors. If the Pipeline does not start processors, this can be written as `""`.
>
> `encoder`: This specifies that the Pipeline created here contains the Operator encoder.



### Create Application

This step will build a Phantoscope Application with the object_pipeline created above. For more information, please refer to [What is an application?](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/en/tutorials/application.md)

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

> `${LOCAL_ADDRESS}':5000/v1/application/ object-example' `: The object-example in the command is a custom name of the application. Note that this name cannot be duplicated by other existing application names.
>
> `object_field`: A custom field name that holds the result of object_pipeline processing
>
> `Pipeline`: Here specifies the name of the Pipeline that the newly created Application will bind to.
>
> `s3Buckets`: Stores the images in an S3 bucket named object-s3.



## Use

### Import data

1. Download data

```shell
$ curl http://cs231n.stanford.edu/coco-animals.zip
$ unzip coco-animals.zip
```

2. Import data

```shell
$ pip3 install requests tqdm
$ python3 scripts/load_data.py -d /tmp/coco-animals/train -a object-example -p object_pipeline
```

Wait for the run to finish and upload the results as shown below.

```
upload url is http://127.0.0.1:5000/v1/application/object-example/upload
allocate 4 processes to load data, each task including 200 images
Now begin to load image data and upload to phantoscope: ...
100%|████████████████████████████████████████████████████████████████████████████████| 800/800 [03:16<00:00,  4.07it/s]
upload 800 images cost: 196.832s 
All images has been uploaded: success 754, fail 46
Please read file 'path_to_error_log' to check upload_error log.
```

> If no matching object is detected in the imported image, the import of that image triggers an import failure report. However, it does not affect the import of other images.



### Inquiry

Launch Phantoscope's front-end for image search. For more information, please refer to [Preview](https://github.com/zilliztech/phantoscope/blob/0.1.0/docs/site/en/tutorials/preview.md).

```shell
$ docker run -d -e API_URL=http://$LOCAL_ADDRESS:5000 -p 8000:80 Phantoscope/preview:latest
```

> If you've already launched the Preview, you don't need to restart it. You can access the already launched Preview directly on the web page by selecting the option named object-example Application will access the just-built version of this Application.



## API description

The above describes how to register an Operator, create a Pipeline and an Application in Phantoscope. Then see how to remove Operator, Pipeline and Application from Phantoscope. For more information, please refer to [Phantoscope API](https://app.swaggerhub.com/apis-docs/phantoscope/Phantoscope/0.1.0#/)。

### See Operator, Pipeline, Application

**View all Operators registered in Phantoscope**.

```shell
$ curl -X GET "http://127.0.0.1:5000/v1/operator/" -H "accept: application/json"
```

**View all Pipelines created in Phantoscope**.

```shell
$ curl -X GET "http://127.0.0.1:5000/v1/pipeline/" -H "accept: application/json"
```

**View all Applications created in Phantoscope**.

```shell
$ curl -X GET "http://127.0.0.1:5000/v1/application/" -H "accept: application/json"
```

### Delete Operator, Pipeline, Application

**Delete an Operator registered in Phantoscope.**

```shell
$ curl -X DELETE "http://127.0.0.1:5000/v1/operator/vgg19" -H "accept: application/json"
```

> The above statement removes an Operator named vgg19.

**Delete a Pipeline in Phantoscope.**

```shell
$ curl -X DELETE "http://127.0.0.1:5000/v1/pipeline/vgg19_pipeline" -H "accept: application/json"
```

> The above statement deletes a Pipeline named vgg19_pipeline.

**Delete an Application in Phantoscope.**

Before deleting an Application, you need to first delete the entity (that is, the image data imported in this Application).

1. View the entity under this Application.

```shell
# View the entity under this Application.
$ curl -X GET "http://127.0.0.1:5000/v1/application/example_app/entity?num=100" -H "accept: application/json"
```

> This interface looks at the id of an existing entity in an Application. An entity corresponds to a picture.

2. Delete entity

```shell
# Delete entity
$ curl -X DELETE "http://127.0.0.1:5000/v1/application/example_app/entity/1592888165100064000" -H "accept: application/json"
```

> Deleting an entity requires two arguments to be passed. One is the name of the Application, which is the `example_app` in the above command. The other one is the id of the entity to be deleted, i.e. the ` 1592888165100064000`. If you want to delete a picture from an Application, you can do it through this interface.

3. Delete Application

```shell
# Delete Application
$ curl -X DELETE "http://127.0.0.1:5000/v1/application/example_app" -H "accept: application/json"
```

> This command removes an Application named `example_app`. If you want to delete an application, you need to delete all the entities in the application before you can remove the Application .
