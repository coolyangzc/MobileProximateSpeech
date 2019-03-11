import copy
import os

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPClassifier

from utils.io import *
from utils.logger import DualLogger
from utils.tools import date_time
from utils.voice_preprocess.mfcc_data_loader import DataPack
from voice.MySVC import MySVC


def visualize_distribution(dataset: DataPack, dim1: int = 0, dim2: int = 1, title: str = '???'):
	'''
	scatter the distribution of dataset projected on dim1 and dim2, with color of each class
	'''
	X0 = np.array(dataset.select_class(0).data)
	n, p = None, None
	if X0.ndim > 1: n = plt.scatter(X0[:, dim1], X0[:, dim2], s=1, c='blue')
	X1 = np.array(dataset.select_class(1).data)
	if X1.ndim > 1: p = plt.scatter(X1[:, dim1], X1[:, dim2], s=1, c='red')
	plt.title('Distribution of %s' % title)
	plt.xlabel('Dim %d' % dim1)
	plt.ylabel('Dim %d' % dim2)
	plt.legend([n, p], ['-', '+'])
	plt.show()


def evaluate(which, dataset: DataPack, group=False):
	print('== on %s ==' % which)
	acc, f1, mistakes, counter = clf.score(dataset, group)
	print('acc = %.4f%%, f1 = %.4f%%' % (acc * 100, f1 * 100))
	print('\tgesture \tmistakes rate \tgesture count')
	for gesture in mistakes:
		print('\t%s:  %.2f%%,  \t%d' % (gesture, mistakes[gesture] * 100, counter[gesture]))
	print()


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
		train.to_flatten()
		val.apply_subsampling()
		val.to_flatten()
		clf = MLPClassifier(hidden_layer_sizes=(300, 200, 100, 10),
							activation='relu', solver='adam',
							learning_rate_init=1e-5, verbose=True, shuffle=True)
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


def visualize_prob_distribution(proba_list, title, color):
	plt.title(title)

	plt.show()

def analyze_proba(title, dataset: DataPack, group=False):
	tl, fl = clf.get_predict_proba_distribution(dataset, group=group)
	plt.hist(tl, bins=30, facecolor='green', edgecolor='black', label='correct')
	plt.hist(fl, bins=30, facecolor='red', edgecolor='black', label='incorrect')
	plt.title('%s proba distribution' % title)
	plt.xlabel('Proba Range')
	plt.ylabel('Freq')
	plt.legend()
	plt.show()

os.chdir('..')

# data config ######################################################
# todo adjustable
wkdirs = [
	'Data/Study3/subjects/gfz/trimmed',
	'Data/Study3/subjects/xy/trimmed',
	'Data/Study3/subjects/wty/trimmed',
	'Data/Study3/subjects/zfs/trimmed',
	'Data/Study3/subjects/0305_2/trimmed',
	'Data/Study3/subjects/wwn/trimmed',
	'Data/Study3/subjects/yzc/trimmed',
	'Data/Study3/subjects/0305_1/trimmed',
	'Data/Study3/subjects/cjr/trimmed',
]
testdir = 'Data/Study3/subjects/wj/trimmed'

DATE_TIME = date_time()
DualLogger('logs/%sSVM.txt' % DATE_TIME)

# res = leave_one_out_val(wkdirs)
# save_to_file(res, 'logs/%sEvaluation Result' % DATE_TIME)

# load ######################################################
# todo can use load from chunks
print('=== Data ===')
dataset = DataPack()
dataset.from_chunks_dir(wkdirs, cache=True, reload=False)

test = DataPack()
test.from_chunks_dir(testdir, cache=True, reload=False)
print('data loaded.')

print('train shape:')
dataset.show_shape()
print()

print('test  shape:')
test.show_shape()
print()

dataset.apply_subsampling()

group_size = 5 # todo
test.apply_subsampling_grouping(group_size=group_size)

dataset.to_flatten()
test.to_flatten()
print('\nafter flatten:')
print('train shape:')
dataset.show_shape()
print()

print('test  shape:')
_shape = np.array(test.data).shape
test.data = np.reshape(test.data, (_shape[0] * group_size, _shape[2]))
del _shape
test.show_shape()
print()

# PCA ######################################################
# todo adjustable
print('=== PCA ===')
pca = PCA(n_components=20)
print('pca config: \n%s\n' % pca)
pca.fit(dataset.data)
print('predicted n_components =', pca.n_components_)
print('variances ratio =', pca.explained_variance_ratio_)
dataset.data = pca.transform(dataset.data)
test.data = pca.transform(test.data)
_shape = test.data.shape
test.data = test.data.reshape((_shape[0] // group_size, group_size, _shape[1]))
del _shape
print('applied transform on train, dev & test.')

# visualize ######################################################
# visualize_distribution(dataset, title='train & dev')
# visualize_distribution(test, title='test')

train, val = dataset.train_test_split(test_size=0.1)

# classifier ######################################################
# todo adjustable
print('\n\n=== train & dev ===')
clf = MySVC(kernel='rbf', gamma=0.03, C=1., verbose=True, probability=True)
# clf = MLPClassifier(hidden_layer_sizes=(300, 200, 100, 10),
# 					activation='relu', solver='adam',
# 					learning_rate_init=1e-5, verbose=True, shuffle=True)
# clf = Perceptron(alpha=1e3)
print('\nclf config:\n%s\n' % clf)
print('gamma =', clf.gamma)

clf.fit(train)

print('\ntrain over.\n')

# evaluate ######################################################
print('=== evaluating ===\n')

evaluate('train', train)
evaluate('dev', val)
evaluate('test', test, group=True)

analyze_proba('train', train)
analyze_proba('dev', val)
analyze_proba('test', test, group=True)

save_to_file(clf, 'voice/model_state/%s%s(chunk).clf' % (DATE_TIME, type(clf)))
