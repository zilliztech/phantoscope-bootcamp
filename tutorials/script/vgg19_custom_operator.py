import os
import uuid
import logging
import time
import numpy as np
import tensorflow as tf
from keras.applications.resnet50 import ResNet50
from keras.preprocessing import image
from keras.applications.resnet50 import preprocess_input
import keras.backend.tensorflow_backend as KTF
from numpy import linalg as LA
from utils import save_tmp_file


def model_data_dir():
    return os.path.abspath(os.path.join('.', 'data'))


# set keras default model path
os.environ['KERAS_HOME'] = model_data_dir()


class CustomOperator:
    def __init__(self):
        self.model_init = False
        self.user_config = self.get_operator_config()

        self.graph = tf.Graph()
        with self.graph.as_default():
            with tf.device(self.device_str):
                self.session = tf.Session(config=self.user_config)
                KTF.set_session(self.session)
                self.model = ResNet50(
                    weights='imagenet',
                    include_top=False,
                    pooling='avg')
                self.graph = KTF.get_graph()
                self.session = KTF.get_session()
                self.model.trainable = False
                # warmup
                self.model.predict(np.zeros((1, 224, 224, 3)))
        logging.info("Succeeded to warmup, Now grpc service is available.")

    def get_operator_config(self):
        try:
            self.device_str = os.environ.get("device_id", "/cpu:0")
            config = tf.ConfigProto(allow_soft_placement=True)
            config.gpu_options.allow_growth = True
            gpu_mem_limit = float(os.environ.get("gpu_mem_limit", 0.3))
            config.gpu_options.per_process_gpu_memory_fraction = gpu_mem_limit
            # for device debug info print
            if os.environ.get("log_device_placement", False):
                self.user_config.log_device_placement = True
            logging.info("device id %s, gpu memory limit: %f",
                         self.device_str, gpu_mem_limit)

        except Exception as e:
            logging.error(
                "unexpected error happen during read config",
                exc_info=True)
            raise e
        logging.info(
            "Model device str: %s, session config: %s",
            self.device_str, config)
        return config

    def execute(self, img_path):
        img = image.load_img(img_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        with self.graph.as_default():
            with tf.device(self.device_str):
                with self.session.as_default():
                    features = self.model.predict(x)
                    norm_feature = features[0] / LA.norm(features[0])
                    norm_feature = [i.item() for i in norm_feature]
                    return norm_feature

    def bulk_execute(self, img_paths):
        result = []
        for img_path in img_paths:
            result.append(self.execute(img_path))
        return result

    def run(self, images, urls):
        result_images = []
        start = time.time()
        try:
            if images:
                for img in images:
                    file_name = "{}-{}".format("processor", uuid.uuid4().hex)
                    image_path = save_tmp_file(file_name, file_data=img)
                    if image_path:
                        result_images.append(self.execute(image_path))
            else:
                for url in urls:
                    file_name = "{}-{}".format("processor", uuid.uuid4().hex)
                    image_path = save_tmp_file(file_name, url=url)
                    if image_path:
                        result_images.append(self.execute(image_path))
        except Exception as e:
            logging.error("something error: %s", str(e), exc_info=True)
            pass
        end = time.time()
        logging.info('%s cost: {:.3f}s, get %d results'.format(end - start),
                     "custom processor", len(result_images))
        return result_images

    @property
    def name(self):
        return "vgg19"

    @property
    def type(self):
        return "encoder"

    @property
    def input(self):
        return "image"

    @property
    def output(self):
        return "vector"

    @property
    def dimension(self):
        return "512"

    @property
    def metric_type(self):
        return "L2"