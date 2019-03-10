import copy
import os
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from hmmlearn import hmm

from utils.io import *
from utils.logger import DualLogger
from utils.tools import date_time
from utils.voice_preprocess.mfcc_data_loader import DataPack, label_dict

gestures = label_dict.keys()
EPSILON = 1e-8


class MyHMM:
	'''
	Hidden Markov Model classifier which provide feedback of incorrect classified samples' descriptions
	'''

	def __init__(self, n_components=5, cov_type='diag', n_iter=1000):
		self.n_components = n_components
		self.cov_type = cov_type
		self.n_iter = n_iter
		self.model0 = hmm.GaussianHMM(n_components=self.n_components, verbose=True,
									  covariance_type=self.cov_type, n_iter=self.n_iter)
		self.model1 = hmm.GaussianHMM(n_components=self.n_components, verbose=True,
									  covariance_type=self.cov_type, n_iter=self.n_iter)

	def fit(self, dataset: DataPack):
		'''
		fit on dataset

		dataset.data shape like (n_sample, t, n_mfcc)
		'''
		X0 = np.array(dataset.select_class(0).data)
		assert X0.ndim == 3
		n0 = X0.shape[0]
		t = X0.shape[1]
		n_mfcc = X0.shape[2]
		X0 = X0.reshape((n0 * t, n_mfcc))

		X1 = np.array(dataset.select_class(1).data)
		assert X1.ndim == 3
		n1 = X1.shape[0]
		assert X1.shape[1] == t
		assert X1.shape[2] == n_mfcc
		X1 = X1.reshape((n1 * t, n_mfcc))

		self.model0.fit(X0, lengths=tuple(t for _ in range(n0)))
		self.model1.fit(X1, lengths=tuple(t for _ in range(n1)))

	def predict(self, samples):
		'''
		predict list of samples

		:param samples: shape like (n_sample, t, n_mfcc)
		:return:
		'''
		return [1 if self.model0.score(sample) < self.model1.score(sample) else 0 for sample in samples]

	def score(self, dataset: DataPack):
		'''
		score dataset with mistake count

		:param dataset: test datapack
		:return: tuple, (accuracy, f1, mistake rate dict, counter of each gesture)
		'''
		counter = Counter(dataset.names)  # count each gesture
		mistakes = {}  # incorrect rates for all gestures
		for gesture in gestures: mistakes[gesture] = 0
		tp, tn, fp, fn = 0, 0, 0, 0
		predictions = self.predict(dataset.data)
		for prediction, label, gesture in zip(predictions, dataset.labels, dataset.names):
			if prediction == label:
				if label == 1:
					tp += 1
				else:
					tn += 1
			else:  # classified wrongly
				if label == 1:
					fn += 1
				else:
					fp += 1
				mistakes[gesture] += 1
		precision = tp / (tp + fp + EPSILON)
		recall = tp / (tp + fn + EPSILON)
		acc = (tp + tn) / (tp + tn + fp + fn)
		f1 = 2 * precision * recall / (precision + recall + EPSILON)

		for gesture in mistakes:
			if counter[gesture] > 0:
				mistakes[gesture] /= counter[gesture]
			else:
				mistakes[gesture] = float('nan')

		return acc, f1, mistakes, counter


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


def evaluate(which, dataset: DataPack):
	print('== on %s ==' % which)
	acc, f1, mistakes, counter = clf.score(dataset)
	print('acc = %.4f%%, f1 = %.4f%%' % (acc * 100, f1 * 100))
	print('\tgesture \tmistakes rate \tgesture count')
	for gesture in mistakes:
		print('\t%s:  %.2f%%,  \t%d' % (gesture, mistakes[gesture] * 100, counter[gesture]))
	print()


os.chdir('..')

# data config ######################################################
# todo adjustable
wkdirs = [
	'Data/Study3/subjects/gfz/trimmed',
	'Data/Study3/subjects/xy/trimmed',
	'Data/Study3/subjects/wty/trimmed',
	'Data/Study3/subjects/zfs/trimmed',
	'Data/Study3/subjects/wj/trimmed',
	'Data/Study3/subjects/wwn/trimmed',
]
testdir = 'Data/Study3/subjects/yzc/trimmed'

DATE_TIME = date_time()
DualLogger('logs/%shmm.txt' % DATE_TIME)

# res = leave_one_out_val(wkdirs)
# save_to_file(res, 'logs/%sEvaluation Result' % DATE_TIME)

# load ######################################################
# todo can use load from chunks
dataset = DataPack()
dataset.from_chunks_dir(wkdirs, cache=True, reload=False)
# dataset.crop(500)

test = DataPack()
test.from_chunks_dir(testdir, cache=True, reload=False)
# test.crop(100)

dataset.apply_subsampling()
dataset.roll_f_as_last()
test.apply_subsampling()
test.roll_f_as_last()

print('data loaded.')

print('train shape:')
dataset.show_shape()
print()

print('test  shape:')
test.show_shape()
print()

train, val = dataset.train_test_split(test_size=0.1)

# classifier ######################################################
# todo adjustable
print('\n\n=== train & dev ===')
clf = MyHMM()
print('\nclf config:\n%s\n' % clf)

print('training...')
clf.fit(train)
print('\ntrain over.\n')

# evaluate ######################################################
print('=== evaluating ===\n')

evaluate('train', train)
evaluate('dev', val)
evaluate('test', test)

save_to_file(clf, 'voice/model_state/%s%s(chunk).clf' % (DATE_TIME, type(clf)))
