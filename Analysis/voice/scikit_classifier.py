from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from utils.voice_preprocess import mfcc_data_loader
from utils.voice_preprocess.mfcc_data_loader import show_shape, DataPack
from configs.subsampling_config import subsampling_config
from utils.tools import date_time
from utils.logger import DualLogger
import os
# from keras.preprocessing.sequence import TimeseriesGenerator
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from utils.io import *
import numpy as np


def load_data(wkdirs, chunks=False, flatten=True):
	if chunks:
		loader = mfcc_data_loader.load_ftr_from_chunks_dir
	else:
		loader = mfcc_data_loader.load_ftr_from_wav_dir
	dataset = loader(wkdirs, shuffle=True, cache=True)
	X, y = [], []
	for ftr_file, label in zip(dataset.data, dataset.labels):
		ftr_file = np.rollaxis(ftr_file, 1, 0)  # time dim first
		data_gen = TimeseriesGenerator(
			ftr_file, np.array([label for _ in ftr_file]),
			start_index=0 if chunks else 50, end_index=None if chunks else len(ftr_file) - 50,
			length=10, stride=6, batch_size=1)
		for X_batch, y_batch in data_gen:
			X.append(X_batch[0])
			y.append(y_batch[0])
	if flatten:
		for i in range(len(X)):
			X[i] = X[i].flatten()

	show_shape(X)
	show_shape(y)

	return X, y


def flattened_pack(pack: DataPack) -> DataPack:
	return DataPack([x.flatten() for x in pack.data], pack.labels, pack.names)


os.chdir('..')
DATE_TIME = date_time()
DualLogger('logs/%ssklearn train' % DATE_TIME)

wkdirs = [
	'Data/Study3/subjects/gfz/trimmed',
	'Data/Study3/subjects/xy/trimmed',
	'Data/Study3/subjects/wty/trimmed',
	'Data/Study3/subjects/zfs/trimmed',
	'Data/Study3/subjects/wj/trimmed',
	'Data/Study3/subjects/wwn/trimmed'
]

valdir = 'Data/Study3/subjects/wwn/trimmed'

# X, y = load_data(wkdirs, chunks=False)
#
# print('val')
# X_val, y_val = load_data(valid_dir, chunks=False) # for validation
#
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)
#
# clf = SVC(kernel='rbf', gamma=3e-5, C=1.0)
# clf.fit(X_train, y_train)
# print('training finished.')
# print('on train', clf.score(X_train, y_train))
# print('on test ', clf.score(X_test, y_test))
# print('on val  ', clf.score(X_val, y_val))

dataset = mfcc_data_loader.load_ftr_from_wav_dir(wkdirs, shuffle=False, cache=True)
valset = mfcc_data_loader.load_ftr_from_wav_dir(valdir, shuffle=False, cache=True)
print('data loaded.')
dataset = mfcc_data_loader.apply_subsampling(*dataset, **subsampling_config, shuffle=True)
valset = mfcc_data_loader.apply_subsampling(*valset, **subsampling_config, shuffle=True)
print('before flatten\n  data.shape  = ', end='')
show_shape(dataset.data)
dataset = flattened_pack(dataset)
valset = flattened_pack(valset)

print('after flatten\n  data.shape   = ', end='')
show_shape(dataset.data)
print('  labels.shape = ', end='')
show_shape(dataset.labels)
print('  names.shape  = ', end='')
show_shape(dataset.names)
print()

train, test = mfcc_data_loader.train_test_split(*dataset, test_size=0.1)

print('===train & test===')
# clf = SVC(kernel='rbf', gamma=1e-5, C=1.0, verbose=1)
clf = MLPClassifier(hidden_layer_sizes=(300, 200, 100, 10), activation='relu', learning_rate_init=1e-5, verbose=True)
print('\nclf config:\n%s\n' % clf)

print('tranning on :')
for wkdir in wkdirs: print(' ', wkdir)
print()

clf.fit(train.data, train.labels)
print('\ntrain over.\n')
print('on train', clf.score(train.data, train.labels))
print('on test ', clf.score(test.data, test.labels))

print('\n===evaluating===')
print('  val.shape = ', end='')
show_shape(valset.data)
print('  val.shape = ', end='')
show_shape(valset.labels)
print('  val.shape = ', end='')
show_shape(valset.names)
print('evaluating...\n')
print('on val  ', clf.score(valset.data, valset.labels))

save_to_file(clf, 'voice/model_state/%s%s.h5' % (DATE_TIME, type(clf)))

# clf = load_from_file('/Users/james/MobileProximateSpeech/Analysis/voice/model_state/190305 22_25_44 svm(chunks).clf')
# for dir in wkdirs:
# 	X_val, y_val = load_data(dir, chunks=False) # for validation
# 	print('evaluating on %s' % dir, clf.score(X_val, y_val))
