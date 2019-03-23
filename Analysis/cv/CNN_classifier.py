import os

import keras
from keras import Sequential
from keras import layers, optimizers, utils, preprocessing

from cv.funcs import *
from utils import io
from utils.cv_preprocess.img_loader import ImagePack
from utils.logger import DualLogger
from utils.tools import date_time

# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"	# todo whether to use cpu

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'  # todo this is important on mac

DATETIME = date_time() + 'PN '
SEED = 120


def build_model():
	# using AlexNet
	model = Sequential([
		layers.Conv2D(96, kernel_size=11, strides=4, padding='valid', activation='relu', input_shape=(227, 227, 3)),
		layers.MaxPool2D(3, strides=2),
		layers.Conv2D(256, kernel_size=5, padding='same', activation='relu'),
		layers.MaxPool2D(3, strides=2),
		layers.Conv2D(384, kernel_size=3, padding='same', activation='relu'),
		layers.Conv2D(384, kernel_size=3, padding='same', activation='relu'),
		layers.Conv2D(256, kernel_size=3, padding='same', activation='relu'),
		layers.MaxPool2D(3, strides=2),
		layers.Flatten(),
		layers.Dense(4096, activation='relu'),
		layers.Dense(4096, activation='relu'),
		layers.Dense(N_CLASS, activation='softmax')
	])
	print(model.summary())
	return model


def compile_model(model, lr=0.0001):
	opt = optimizers.RMSprop(lr=lr, decay=1e-5)
	model.compile(loss='categorical_crossentropy',
				  optimizer=opt,
				  metrics=['acc'])
	return model


if __name__ == '__main__':
	CWD = 'E:\ZFS_TEST\Analysis'
	os.chdir(CWD)
	DualLogger('logs/%sCNN.txt' % DATETIME)
	print('====== CNN Training Started At %s ======' % DATETIME)
	print('with random_seed = %d\n' % SEED)

	imgset = ImagePack()
	# positives
	os.chdir('Data/Study2/subjects')
	subject_dirs = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	print('loading from positives:', subject_dirs)
	imgset.from_subject(subject_dirs, shuffle=False)
	# negatives
	os.chdir('../negatives')
	negative_dirs = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	print('loading from negatives:', negative_dirs)
	imgset.from_subject(negative_dirs, random_seed=SEED)
	os.chdir(CWD)

	print(imgset.names[:10:3], '\n')
	print('data loaded.')
	print('whole set:')
	imgset.show_shape()
	print()

	train, val = imgset.train_val_split()
	print('train set:')
	train.show_shape()
	print()
	print('test set:')
	val.show_shape()
	print()

	# data augmenting tool
	# datagen = io.load_from_file('cv/model_state/190316 21_26_45 PN datagen.h5')
	datagen = preprocessing.image.ImageDataGenerator(
		featurewise_center=True,
		featurewise_std_normalization=True,
		rotation_range=40,
		width_shift_range=0.2,
		height_shift_range=0.2,
		horizontal_flip=True)
	print('datagen fitting...')
	datagen.fit(train.select_class([1, 2, 3, 4, 5]).images)
	io.save_to_file(datagen, 'cv/model_state/%sdatagen.h5' % DATETIME)
	train.labels = utils.to_categorical(train.labels)
	val.labels = utils.to_categorical(val.labels)

	# todo
	model = keras.models.load_model('cv/model_state/190316 21_26_45 PN best model.h5', compile=True)
	# model = build_model()
	# compile_model(model)
	# callbacks
	csv_logger = keras.callbacks.CSVLogger(
		'outputs/%sCNN hist.csv' % DATETIME,
		separator=',', append=False)
	checkpoint_logger = keras.callbacks.ModelCheckpoint(
		'cv/model_state/%sbest.h5' % DATETIME,
		monitor='val_loss', verbose=1, save_best_only=True)

	print('===== begin training =====')
	batch_size = 10
	history = model.fit_generator(datagen.flow(train.images, train.labels, batch_size=batch_size),
								  validation_data=datagen.flow(val.images, val.labels, batch_size=batch_size),
								  validation_steps=50, steps_per_epoch=200, epochs=50, verbose=1,
								  callbacks=[csv_logger, checkpoint_logger])

	print('\n=== train over ===\n')
	model.save('cv/model_state/%sfinal.h5' % DATETIME)
	plot_history(history, 'loss', DATETIME)
	plot_history(history, 'acc', DATETIME)

	# print(model.evaluate_generator(datagen.flow(val.images, val.labels, batch_size=32),
	# 							   steps=len(train.images) / 32))
	pass
