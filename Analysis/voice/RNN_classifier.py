from keras import layers
from keras import optimizers
from keras.models import Sequential
import numpy as np
import os
from utils.logger import DualLogger
from utils.tools import date_time

from utils.voice_preprocess.mfcc_data_loader import MfccPack

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


def load_train_test(wkdir, test_size=None):
	dataset = MfccPack()
	dataset.from_chunks_dir(wkdir)
	dataset.apply_subsampling()
	dataset.roll_f_as_last()
	# reshape to (n_units, n_frame, n_mfcc)
	# dataset = DataPack([unit.flatten() for unit in dataset.data], dataset.labels, dataset.names)
	print('shape like:')
	dataset.show_shape()
	print('data loaded.\n')
	return dataset.train_test_split(test_size=test_size)

if __name__ == '__main__':
	os.chdir('..')
	os.path.exists('model_state')
	date_time = date_time()
	DualLogger('logs/%sRNN.txt' % date_time)
	print(os.getcwd())
	wkdir = 'Data/Study3/subjects/yzc/trimmed'
	wkdir2 = 'Data/Study3/subjects/zfs//trimmed'
	train, test = load_train_test(wkdir, test_size=0.1)
	train2, test2 = load_train_test(wkdir2, test_size=0)

	model = build_model()
	print(model.summary())
	model.fit(train.data, train.labels, batch_size=10, epochs=1)
	train_loss, train_acc = model.evaluate(train.data, train.labels, batch_size=10)
	test_loss, test_acc = model.evaluate(test.data, test.labels, batch_size=10)
	print('acc on mix train:', train_acc)
	print('acc on mix test :', test_acc)
	print('on zfs test ', model.evaluate(train2.data, train2.labels, batch_size=10))
	model.save('voice/model_state/%sRNN mix%d-%d.model' % (date_time, train_acc * 100, test_acc * 100))
