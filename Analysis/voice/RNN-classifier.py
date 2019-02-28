from keras import layers
from keras import optimizers
from keras.models import Sequential
import numpy as np
import os

import utils.voice_data_loader as loader
from utils.voice_data_loader import show_shape, DataPack
from configs.subsampling_config import subsampling_config


def build_model():
	print('building model...')
	layer_units = (40, 100, 1)
	model = Sequential()
	model.add(layers.SimpleRNN(units=layer_units[1], return_sequences=False, input_shape=(None, layer_units[0])))
	model.add(layers.Dense(units=layer_units[2], activation='sigmoid'))
	# model.add(layers.Dense(units=100, activation='relu', input_shape=(360,)))
	# model.add(layers.Dense(units=10, activation='relu'))
	# model.add(layers.Dense(units=1, activation='sigmoid'))

	sgd = optimizers.SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
	model.compile(optimizer=sgd, loss='mse', metrics=['acc'])
	print('built.')
	return model


def load_train_test(wkdir):
	dataset = loader.load_ftr_from_dir(wkdir)
	dataset = loader.apply_subsampling(*dataset, **subsampling_config)
	# reshape to (n_units, n_frame, n_mfcc)
	# dataset = DataPack([unit.flatten() for unit in dataset.data], dataset.labels, dataset.names)
	dataset = DataPack(np.rollaxis(np.array(dataset.data), 1, 3), dataset.labels, dataset.names)
	print('data shape like:')
	show_shape(dataset.data)
	print('data loaded.\n')
	return loader.train_test_split(*dataset, test_size=0.1)


if __name__ == '__main__':
	os.chdir('..')
	wkdir = 'Data/Sounds/yzc/'
	train, test = load_train_test(wkdir)

	model = build_model()
	model.fit(train.data, train.labels, batch_size=10)
	print(model.evaluate(train.data, train.labels))
	print(model.evaluate(test.data, test.labels))
