import os
import uuid
import logging
import time
import numpy as np
import tensorflow as tf
from tensorflow.python.keras.backend import set_session
from keras.applications.resnet50 import ResNet50
from keras.preprocessing import image
from keras.applications.resnet50 import preprocess_input
import keras.backend.tensorflow_backend as KTF
from numpy import linalg as LA
from utils import save_tmp_file


# set keras default model path
os.environ['KERAS_HOME'] = os.path.abspath(os.path.join('.', 'data'))


class CustomOperator:
    def __init__(self):
        self.session = tf.Session()
        set_session(self.session)
        self.graph = tf.get_default_graph()
        self.model = ResNet50(
                    weights='imagenet',
                    include_top=False,
                    pooling='avg')


    def execute(self, img_path):
        img = image.load_img(img_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        with self.graph.as_default():
            with self.session.as_default():
                features = self.model.predict(x)
                norm_feature = features[0] / LA.norm(features[0])
                norm_feature = [i.item() for i in norm_feature]
                return norm_feature


    def run(self, images, urls):
        images_vectors = []
        start = time.time()
        try:
            if images:
                for img in images:
                    file_name = "{}-{}".format("processor", uuid.uuid4().hex)
                    image_path = save_tmp_file(file_name, file_data=img)
                    if image_path:
                        images_vectors.append(self.execute(image_path))
            else:
                for url in urls:
                    file_name = "{}-{}".format("processor", uuid.uuid4().hex)
                    image_path = save_tmp_file(file_name, url=url)
                    if image_path:
                        images_vectors.append(self.execute(image_path))
        except Exception as e:
            logging.error("something error: %s", str(e), exc_info=True)
            pass
        end = time.time()
        logging.info('%s cost: {:.3f}s, get %d results'.format(end - start),
                     "custom processor", len(images_vectors))
        return images_vectors

    @property
    def name(self):
        return "resnet50-encoder"

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
        return "2048"

    @property
    def metric_type(self):
        return "L2"