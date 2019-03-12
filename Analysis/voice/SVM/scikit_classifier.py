import copy
import os
import time
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA

from configs.subsampling_config import subsampling_config
from utils.io import *
from utils.logger import DualLogger
from utils.tools import date_time
from utils.voice_preprocess.mfcc_data_loader import DataPack, label_dict
from voice.SVM.MySVC import MySVC

# globals
gestures = label_dict.keys()
CWD = '/Users/james/MobileProximateSpeech/Analysis'
DATE_TIME = date_time()
FOLDER = '%sSVM leave one out' % DATE_TIME
VAL_ORD = 0
TOT_VAL = 0


class Results:
	def __init__(self, acc=0., f1=0., mistakes=None, counter=None, tl=None, fl=None, name=None):
		self.acc, self.f1 = acc, f1
		self.mistakes = Counter() if mistakes is None else mistakes
		self.counter = Counter() if counter is None else counter
		self.tl = [] if tl is None else tl
		self.fl = [] if fl is None else fl
		self.name = name

	def __iadd__(self, other):
		self.acc += other.acc
		self.f1 += other.f1
		self.mistakes += other.mistakes
		self.counter += other.counter
		self.tl += other.tl
		self.fl += other.fl
		return self

	def __itruediv__(self, other: int):
		self.acc /= other
		self.f1 /= other
		return self

	def summary(self):
		print('\n== Summary of %s ==\n' % self.name)
		print('acc = %.4f%%, f1 = %.4f%%\n' % (self.acc * 100, self.f1 * 100))
		show_table(self.mistakes, self.counter)
		visualize_proba(self.tl, self.fl, self.name, out_path='output/%s/%s summary.png' % (FOLDER, self.name))


TRAIN_RES = Results(name='Train')
VAL_RES = Results(name='Dev')
TEST_RES = Results(name='Test')
TRAIN_RES_G = Results(name='Train (group voting)')
VAL_RES_G = Results(name='Dev (group voting)')
TEST_RES_G = Results(name='Test (group voting)')


def visualize_distribution(dataset: DataPack, dim1: int = 0, dim2: int = 1, title: str = '???', out_path=None):
	'''
	scatter the distribution of dataset projected on dim1 and dim2, with color of each class
	'''
	X0 = np.array(dataset.select_class(0).data)
	n, p = None, None
	if X0.ndim > 1: n = plt.scatter(X0[:, dim1], X0[:, dim2], s=1, c='blue')
	X1 = np.array(dataset.select_class(1).data)
	if X1.ndim > 1: p = plt.scatter(X1[:, dim1], X1[:, dim2], s=1, c='red')
	name = 'Distribution of %s' % title
	plt.title(name)
	plt.xlabel('Dim %d' % dim1)
	plt.ylabel('Dim %d' % dim2)
	plt.legend([n, p], ['-', '+'])
	if out_path is None:
		out_path = os.path.join(CWD, 'output/%s/val-%d/%s.png' % (FOLDER, VAL_ORD, name))
	plt.savefig(out_path)
	plt.show()


def visualize_proba(tl, fl, title, out_path=None):
	plt.hist(tl, bins=30, facecolor='green', edgecolor='black', label='correct', alpha=0.6)
	plt.hist(fl, bins=30, facecolor='red', edgecolor='black', label='incorrect', alpha=0.6)
	name = '%s proba distribution' % title
	plt.title(name)
	plt.xlabel('Probability')
	plt.ylabel('Frequency')
	plt.legend()
	if out_path is None:
		out_path = os.path.join(CWD, 'output/%s/val-%d/%s.png' % (FOLDER, VAL_ORD, name))
	plt.savefig(out_path)
	plt.show()


def pca_reduction(dataset, test, n_components):
	'''
	reduce the feature dimension using pca
	'''
	print('=== PCA ===')
	pca = PCA(n_components=n_components)
	print('pca config: \n%s\n' % pca)

	dataset._ungroup()
	pca.fit(dataset.data)
	print('predicted n_components =', pca.n_components_)
	print('variances ratio =', pca.explained_variance_ratio_)
	dataset.data = pca.transform(dataset.data)
	dataset._regroup()

	test._ungroup()
	test.data = pca.transform(test.data)
	test._regroup()


def show_table(mistakes, counter):
	print('\t[Gesture] 　　　 [Mistakes Rate]  [Gesture Count]')
	for gesture in gestures:
		if counter[gesture] == 0:
			mistake_rate = float('nan')
		else:
			mistake_rate = mistakes[gesture] / counter[gesture]
		print('\t{0:{1}<10}  {2:>8.2f}%  {3:>10}'.format(gesture, chr(12288), mistake_rate * 100, counter[gesture]))
	print()


def evaluate(clf, which, dataset: DataPack, group=False):
	'''
	:return: Results
	'''
	print('== on %s ==' % which)
	acc, f1, mistakes, counter = clf.score(dataset, group)
	print('acc = %.4f%%, f1 = %.4f%%\n' % (acc * 100, f1 * 100))
	show_table(mistakes, counter)
	tl, fl = clf.get_predict_proba_distribution(dataset, group=group)
	title = which + '(group)' if group else which
	visualize_proba(tl, fl, title)
	return Results(acc, f1, mistakes, counter, tl, fl)


def leave_one_out(wkdirs, testdir, verbose=False):
	'''
	train and validate on wkdirs, transfer testing on testdir

	:param wkdirs: str or list of str, directory of a subject or some subjects, for train and dev
	:param testdir: str, directory of a subject, for test
	'''
	global VAL_ORD, TOT_VAL, TRAIN_RES, VAL_RES, TEST_RES, TRAIN_RES_G, VAL_RES_G, TEST_RES_G
	VAL_ORD += 1
	logger = DualLogger(os.path.join(CWD, 'logs/%s/val-%d.txt' % (FOLDER, VAL_ORD)))
	os.mkdir(os.path.join(CWD, 'output/%s/val-%d' % (FOLDER, VAL_ORD)))

	print('====== Leave One Out # %d / %d ======\n' % (VAL_ORD, TOT_VAL))
	print('Training and validating on %s' % wkdirs)
	print('Testing on %s' % testdir)
	print()
	wkdirs = [os.path.join(wkdir, 'trimmed') for wkdir in wkdirs]
	testdir = os.path.join(testdir, 'trimmed')

	# load ######################################################
	# todo can use load from chunks
	print('=== Data ===')
	dataset = DataPack()
	dataset.from_chunks_dir(wkdirs, cache=True, reload=False)

	test = DataPack()
	test.from_chunks_dir(testdir, cache=True, reload=False)
	print('data loaded.')

	# print('dataset shape:')
	# dataset.show_shape()
	# print()
	# print('test shape:')
	# test.show_shape()
	# print()

	dataset.apply_subsampling_grouping()
	test.apply_subsampling_grouping()
	dataset.to_flatten()
	test.to_flatten()

	print('after flatten:\n')
	print('dataset shape:')
	dataset.show_shape()
	print()
	print('test  shape:')
	test.show_shape()
	print()

	# PCA ######################################################
	# todo adjustable
	pca_reduction(dataset, test, n_components=30)
	print('\napplied transform on train, dev & test.')
	train, val = dataset.train_test_split(test_size=0.1)
	print('train shape:')
	train.show_shape()
	print()
	print('dev shape:')
	val.show_shape()
	print()
	print('test  shape:')
	test.show_shape()
	print()

	# visualize ######################################################
	visualize_distribution(dataset, title='train & dev')
	visualize_distribution(test, title='test')

	# classifier ######################################################
	# todo adjustable
	print('=== train & dev ===')
	clf = MySVC(kernel='rbf', gamma='auto', C=1.0, class_weight='balanced', probability=True,
				verbose=verbose, cache_size=1000)
	print('\nclf config:\n%s\n' % clf)
	print('gamma =', clf.gamma)

	clf.fit(train)

	print('\ntrain over.')
	print('number of support vectors: \n' % clf.n_support_)
	print()

	# evaluate ######################################################
	print('=== evaluating ===')

	print('\n== without group voting ==')
	TRAIN_RES += evaluate(clf, 'train', train)
	VAL_RES += evaluate(clf, 'dev', val)
	TEST_RES += evaluate(clf, 'test', test)

	print('\n== with group voting ==')
	TRAIN_RES_G += evaluate(clf, 'train', train, group=True)
	VAL_RES_G += evaluate(clf, 'dev', val, group=True)
	TEST_RES_G += evaluate(clf, 'test', test, group=True)

	save_to_file(clf, os.path.join(CWD, 'voice/model_state/%s/val-%d-%s.clf' % (FOLDER, VAL_ORD, type(clf))))
	logger.close()


if __name__ == '__main__':
	import random

	since = time.time()
	os.chdir(CWD)
	os.mkdir('output/%s' % FOLDER)
	os.mkdir('logs/%s' % FOLDER)
	os.mkdir('voice/model_state/%s' % FOLDER)
	os.chdir('Data/Study3/subjects')

	subject_dirs = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	subject_dirs = random.choices(subject_dirs, k=4)
	TOT_VAL = len(subject_dirs)

	for testdir in subject_dirs:
		wkdirs = copy.copy(subject_dirs)
		wkdirs.remove(testdir)
		leave_one_out(wkdirs, testdir)

	os.chdir(CWD)
	logger = DualLogger('logs/%s/summary.txt' % FOLDER)
	print('===== Summary =====\n')

	for res in TRAIN_RES, VAL_RES, TEST_RES, TRAIN_RES_G, VAL_RES_G, TEST_RES_G:
		res /= TOT_VAL
		res.summary()

	print('label_dict:')
	for gesture in label_dict:
		print(gesture, ':', label_dict[gesture])
	print()

	print('subsampling config:')
	for item in subsampling_config:
		print(item, ':', subsampling_config[item])
	print()

	elapse = int(time.time() - since)
	minutes = elapse // 60
	seconds = elapse % 60
	print('total run time: %d min %d sec\n' % (minutes, seconds))
	logger.close()
