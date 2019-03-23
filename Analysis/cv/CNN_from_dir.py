import os

import keras
from keras import Sequential
from keras import layers, optimizers, utils, preprocessing

from cv.funcs import *
from utils import io
from configs import cv_config as config
from utils.logger import DualLogger
from utils.tools import date_time

# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"	# todo whether to use cpu

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'  # todo this is important on mac

PREFIX = date_time() + 'PN '
SEED = config.random_seed

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
		layers.Dense(1, activation='sigmoid')
	])
	print(model.summary())
	return model


def compile_model(model, lr=config.learning_rate):
	opt = optimizers.RMSprop(lr=lr, decay=config.decay)
	# model.compile(loss='categorical_crossentropy',
	model.compile(loss='mse',
				  optimizer=opt,
				  metrics=['acc', f1])
	return model


if __name__ == '__main__':

	CWD = config.working_directory

	os.chdir(CWD)
	DualLogger('logs/%sCNN.txt' % PREFIX)
	print('====== CNN Training Started At %s ======' % PREFIX)
	print('with random_seed = %d\n' % SEED)

	# data augmenting tool
	# datagen = io.load_from_file('cv/model_state/190316 21_26_45 PN datagen.h5') # this generator applies a normalization
	datagen = preprocessing.image.ImageDataGenerator(**config.data_gen_config)

	# todo
	model = keras.models.load_model('cv/model_state/190322 23_46_55 PN best.h5', compile=False)
	# model = build_model()
	compile_model(model, lr=1e-8)
	# callbacks
	csv_logger = keras.callbacks.CSVLogger(
		'outputs/%sCNN hist.csv' % PREFIX,
		separator=',', append=False)
	checkpoint_logger = keras.callbacks.ModelCheckpoint(
		'cv/model_state/%sbest.h5' % PREFIX,
		monitor='val_loss', verbose=1, save_best_only=True)

	print('===== begin training =====')
	batch_size = config.batch_size
	train_gen = datagen.flow_from_directory(os.path.join(config.data_directory, 'train'),
											target_size=(227, 227), color_mode='rgb',
											class_mode='binary', batch_size=batch_size,
											shuffle=True, seed=SEED)
	# train_gen.class_indices = config.class_indices
	val_gen = datagen.flow_from_directory(os.path.join(config.data_directory, 'val'),
										  target_size=(227, 227), color_mode='rgb',
										  class_mode='binary', batch_size=batch_size,
										  shuffle=True, seed=(SEED + 1))
	print(val_gen.class_indices)
	# val_gen.class_indices = config.class_indices
	# todo train begins here
	history = model.fit_generator(
		generator=train_gen, validation_data=val_gen, class_weight=config.class_weight,
		steps_per_epoch=500, validation_steps=50, epochs=config.epochs, verbose=1,
		callbacks=[csv_logger, checkpoint_logger])

	print('\n=== train over ===\n')
	model.save('cv/model_state/%sfinal.h5' % PREFIX)
	plot_history(history, 'loss', PREFIX)
	plot_history(history, 'acc', PREFIX)
	del train_gen, val_gen

	print('=== testing... ===\n')
	test_gen = datagen.flow_from_directory(os.path.join(config.data_directory, 'test'),
										   target_size=(227, 227), color_mode='rgb',
										   class_mode='binary', batch_size=batch_size,
										   shuffle=True, seed=(SEED + 2))
	# test_gen.class_indices = config.class_indices
	loss, acc, f1 = model.evaluate_generator(test_gen, steps=300 // batch_size, verbose=1)
	print('test loss = %f, acc = %f, f1 = %f' % (loss, acc, f1))
