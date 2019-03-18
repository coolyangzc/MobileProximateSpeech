import os

import keras
from keras import Sequential
from keras import layers, optimizers, utils, preprocessing

from cv.funcs import *
from utils import io
from utils.cv_preprocess.img_loader import N_CLASS
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
	CWD = 'E:/ZFS_TEST/Analysis'
	os.chdir(CWD)
	DualLogger('logs/%sCNN.txt' % DATETIME)
	print('====== CNN Training Started At %s ======' % DATETIME)
	print('with random_seed = %d\n' % SEED)

	# data augmenting tool
	datagen = io.load_from_file('cv/model_state/190316 21_26_45 PN datagen.h5')

	# todo
	# model = keras.models.load_model('cv/model_state/190316 21_26_45 PN best model.h5', compile=True)
	model = build_model()
	compile_model(model)
	# callbacks
	csv_logger = keras.callbacks.CSVLogger(
		'outputs/%sCNN hist.csv' % DATETIME,
		separator=',', append=False)
	checkpoint_logger = keras.callbacks.ModelCheckpoint(
		'cv/model_state/%sbest model.h5' % DATETIME,
		monitor='val_loss', verbose=1, save_best_only=True)

	print('===== begin training =====')
	batch_size = 20
	train_gen = datagen.flow_from_directory('Data/Study2/train', target_size=(227, 227), color_mode='rgb',
											class_mode='categorical', batch_size=batch_size,
											shuffle=True, seed=SEED)
	val_gen = datagen.flow_from_directory('Data/Study2/val', target_size=(227, 227), color_mode='rgb',
										  class_mode='categorical', batch_size=batch_size,
										  shuffle=True, seed=(SEED + 1))
	history = model.fit_generator(
		generator=train_gen, validation_data=val_gen,
		steps_per_epoch=500, validation_steps=50, epochs=10, verbose=1,
		callbacks=[csv_logger, checkpoint_logger])

	print('\n=== train over ===\n')
	model.save('cv/model_state/%sfinal.h5' % DATETIME)
	plot_history(history, 'loss', DATETIME)
	plot_history(history, 'acc', DATETIME)
	del train_gen, val_gen

	print('=== testing... ===\n')
	test_gen = datagen.flow_from_directory('Data/Study2/test', target_size=(227, 227), color_mode='rgb',
										   class_mode='categorical', batch_size=batch_size,
										   shuffle=True, seed=(SEED + 2))
	loss, acc = model.evaluate_generator(test_gen, steps=300 // batch_size, verbose=1)
	print('test loss = %f, acc = %f' % (loss, acc))
