from keras import Sequential
from keras import layers, optimizers, utils
import os
import numpy as np
from utils.cv_preprocess.img_loader import ImagePack

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True' # todo this is important on mac

model = None

def build_model():
	model = Sequential([

	])


if __name__ == '__main__':
	imgset = ImagePack()
