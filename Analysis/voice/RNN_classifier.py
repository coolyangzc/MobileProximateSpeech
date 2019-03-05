from keras import layers
from keras import optimizers
from keras.models import Sequential
import numpy as np
import os
from utils.logger import DualLogger
from utils.tools import date_time

import utils.voice_preprocess.mfcc_data_loader as loader
from utils.voice_preprocess.mfcc_data_loader import show_shape, DataPack
from configs.subsampling_config import subsampling_config


def build_model():
	print('building model...')
	layer_units = (40, 100, 1)
	model = Sequential()
	model.add(layers.GRU(units=layer_units[1], return_sequences=False, input_shape=(None, layer_units[0])))
	model.add(layers.Dropout(0.2))
	model.add(layers.Dense(units=layer_units[2], activation='sigmoid'))

	sgd = optimizers.RMSprop(lr=0.001, rho=0.9, epsilon=None, decay=0.0)
	model.compile(optimizer=sgd, loss='mse', metrics=['acc'])
	print('built.')
	return model


def load_train_test(wkdir, test_size):
	dataset = loader.load_ftr_from_pn_dir(wkdir)
	dataset = loader.apply_subsampling(*dataset, **subsampling_config)
	# reshape to (n_units, n_frame, n_mfcc)
	# dataset = DataPack([unit.flatten() for unit in dataset.data], dataset.labels, dataset.names)
	dataset = DataPack(np.rollaxis(np.array(dataset.data), 1, 3), dataset.labels, dataset.names)
	print('data shape like:')
	show_shape(dataset.data)
	print('data loaded.\n')
	return loader.train_test_split(*dataset, test_size=test_size)


if __name__ == '__main__':
	os.chdir('..')
	os.path.exists('model_state')
	date_time = date_time()
	DualLogger('logs/%sRNN.txt' % date_time)
	print(os.getcwd())
	wkdir = 'Data/Sounds/yzc'
	wkdir2 = 'Data/Sounds/zfs'
	train, test = load_train_test(wkdir, test_size=0.1)
	train2, test2 = load_train_test(wkdir2, test_size=0)

	model = build_model()
	print(model.summary())
	model.fit(train.data, train.labels, batch_size=10, epochs=1)
	train_loss, train_acc = model.evaluate(train.data, train.labels, batch_size=10)
	test_loss, test_acc = model.evaluate(test.data, test.labels, batch_size=10)
	print('acc on mix train:', train_acc)
	print('acc on mix test :', test_acc)
	# print('on zfs test ', model.evaluate(train2.data, train2.labels, batch_size=10))
	model.save('voice/model_state/%sRNN mix%d-%d.model' % (date_time, train_acc * 100, test_acc * 100))
