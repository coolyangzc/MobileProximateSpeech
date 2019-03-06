from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from utils.voice_preprocess import mfcc_data_loader
from utils.voice_preprocess.mfcc_data_loader import DataPack
from configs.subsampling_config import subsampling_config
from utils.tools import date_time
from utils.logger import DualLogger
import os
from utils.io import *
import copy
import numpy as np


def flattened_pack(pack: DataPack) -> DataPack:
	return DataPack([x.flatten() for x in pack.data], pack.labels, pack.names)


def leave_one_out_val(wkdirs):
	'''
	以 n-1 个人的数据进行训练，以剩余一个人的数据进行验证，将结果以列表形式输出

	:param wkdirs: list of subjecs' working directory
	:return: list of acc result tuples (train_acc, val_acc)
	'''
	train_accs, val_accs = [], []
	for i, val_dir in enumerate(wkdirs):
		print('\n=== leave one out val %d / %d ===' % (i + 1, len(wkdirs)))
		train_dirs = copy.copy(wkdirs)
		train_dirs.remove(val_dir)

		train = DataPack()
		train.from_wav_dir(train_dirs, cache=True)
		val = DataPack()
		val.from_wav_dir(val_dir, cache=True)
		train.apply_subsampling()
		train = flattened_pack(train)
		val.apply_subsampling()
		val = flattened_pack(val)
		clf = MLPClassifier(hidden_layer_sizes=(300, 200, 100, 10),
							activation='relu', solver='adam',
							learning_rate_init=1e-5, verbose=False, shuffle=True)
		print('clf ready.\n', clf)
		print()
		clf.fit(train.data, train.labels)
		print('\ntrain over.\n')
		train_acc = clf.score(train.data, train.labels)
		print('train acc =', train_acc)
		val_acc = clf.score(val.data, val.labels)
		print('val acc =', val_acc)
		print()

		train_accs.append(train_acc)
		val_accs.append(val_acc)


os.chdir('..')

# todo adjustable
wkdirs = [
	'Data/Study3/subjects/gfz/trimmed',
	'Data/Study3/subjects/xy/trimmed',
	'Data/Study3/subjects/wty/trimmed',
	'Data/Study3/subjects/zfs/trimmed',
	'Data/Study3/subjects/wj/trimmed',
	'Data/Study3/subjects/wwn/trimmed'
]

DATE_TIME = date_time()
DualLogger('logs/%sMLP(chunk) train' % DATE_TIME)

res = leave_one_out_val(wkdirs)

save_to_file(res, 'logs/%sEvaluation Result' % DATE_TIME)

# valdir = 'Data/Study3/subjects/wwn/trimmed'
#
#
# # todo can use load from chunks
# dataset = mfcc_data_loader.load_ftr_from_chunks_dir(wkdirs, shuffle=False, cache=True)
# valset = mfcc_data_loader.load_ftr_from_chunks_dir(valdir, shuffle=False, cache=True)
# print('data loaded.')
# dataset = mfcc_data_loader.apply_subsampling(*dataset, **subsampling_config, shuffle=True)
# valset = mfcc_data_loader.apply_subsampling(*valset, **subsampling_config, shuffle=True)
# print('before flatten\n  data.shape  = ', end='')
# show_shape(dataset.data)
# dataset = flattened_pack(dataset)
# valset = flattened_pack(valset)
#
# print('after flatten\n  data.shape   = ', end='')
# show_shape(dataset.data)
# print('  labels.shape = ', end='')
# show_shape(dataset.labels)
# print('  names.shape  = ', end='')
# show_shape(dataset.names)
# print()
#
# train, test = mfcc_data_loader.train_test_split(*dataset, test_size=0.1)
#
# print('===train & test===')
# # todo adjustable
# # clf = SVC(kernel='rbf', gamma=1e-5, C=1.0, verbose=1)
# clf = MLPClassifier(hidden_layer_sizes=(300, 200, 100, 10),
# 					activation='relu', solver='adam',
# 					learning_rate_init=1e-5, verbose=True, shuffle=True)
# print('\nclf config:\n%s\n' % clf)
#
# print('tranning on :')
# for wkdir in wkdirs: print(' ', wkdir)
# print()
#
# clf.fit(train.data, train.labels)
# print('\ntrain over.\n')
# print('on train', clf.score(train.data, train.labels))
# print('on test ', clf.score(test.data, test.labels))
#
# print('\n===evaluating===')
# print('  val.shape = ', end='')
# show_shape(valset.data)
# print('  val.shape = ', end='')
# show_shape(valset.labels)
# print('  val.shape = ', end='')
# show_shape(valset.names)
# print('evaluating...\n')
# print('on val  ', clf.score(valset.data, valset.labels))
#
# save_to_file(clf, 'voice/model_state/%s%s(chunk).clf' % (DATE_TIME, type(clf)))
