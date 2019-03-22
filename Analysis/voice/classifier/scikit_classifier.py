import copy
import os
import random
import time
from collections import Counter

import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

from configs.subsampling_config import subsampling_config_2_channel
from utils import io
from utils.logger import DualLogger
from utils.tools import date_time
from utils.voice_preprocess.data_loader import DataPack
from utils.voice_preprocess.wav_loader import label_dict, doc_dict
from voice.classifier.MyCLF import MySVC

# globals
gestures = label_dict.keys()
CWD = '/Users/james/MobileProximateSpeech/Analysis'
DATE_TIME = date_time()
FOLDER = '%sstereo chunks features' % DATE_TIME  # todo
AVAILABLE_STEREO_FEATURES = [
	'rms.DataPack',
	'zcr.DataPack',
	# 'spectral_centroid.DataPack',
	# 'spectral_rolloff.DataPack',
	# 'spectral_bandwidth.DataPack',
	# 'spectral_contrast.DataPack',
]
AVAILABLE_MONO_FEATURES = [
	'rms_diff.DataPack',
	'mfcc_diff.DataPack',
	# 'spectral_flatness_diff.DataPack'
]
VAL_ORD = 0
TOT_VAL = 0
bad_testers = []


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
		global output_dir
		print('\n== Summary of %s ==\n' % self.name)
		print('acc = %.4f%%, f1 = %.4f%%\n' % (self.acc * 100, self.f1 * 100))
		show_table(self.mistakes, self.counter)
		visualize_proba(self.tl, self.fl, self.name, out_path=os.path.join(output_dir, '%s summary.png' % self.name))

	def as_csv(self):
		return self.name + ' ACC, ' + str(self.acc) + '\n' + self.name + ' F1, ' + str(self.f1) + '\n'


TRAIN_RES = Results(name='Train')
VAL_RES = Results(name='Dev')
TEST_RES = Results(name='Test')
TRAIN_RES_G = Results(name='Train (group voting)')
VAL_RES_G = Results(name='Dev (group voting)')
TEST_RES_G = Results(name='Test (group voting)')


def visualize_proba(tl, fl, title, out_path=None):
	plt.hist(tl, bins=30, facecolor='green', edgecolor='black', label='correct', alpha=0.6)
	plt.hist(fl, bins=30, facecolor='red', edgecolor='black', label='incorrect', alpha=0.6)
	name = '%s proba distribution' % title
	plt.title(name)
	plt.xlabel('Probability')
	plt.ylabel('Frequency')
	plt.legend()
	if out_path is None:
		out_path = os.path.join(CWD, os.path.join(output_dir, 'val-%d/%s.png' % (VAL_ORD, name)))
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
		label = label_dict[gesture]
		if counter[label] == 0:
			mistake_rate = float('nan')
		else:
			mistake_rate = mistakes[label] / counter[label]
		print('\t{0:{1}<10}  {2:>8.2f}%  {3:>10}'.format(gesture, chr(12288), mistake_rate * 100, counter[label]))
	print()


def evaluate(clf, which, dataset: DataPack, group=False):
	'''
	:return: Results
	'''
	print('== on %s ==' % which)
	acc, f1, mistakes, counter = clf.evaluate(dataset, group)
	print('acc = %.4f%%, f1 = %.4f%%\n' % (acc * 100, f1 * 100))
	show_table(mistakes, counter)
	tl, fl = clf.get_predict_proba_distribution(dataset, group=group)
	title = which + '(group)' if group else which
	visualize_proba(tl, fl, title)
	return Results(acc, f1, mistakes, counter, tl, fl)


def load_features(wkdir: str) -> DataPack:
	fs = DataPack()
	for feature in AVAILABLE_STEREO_FEATURES:
		f = io.load_from_file(os.path.join(wkdir, feature))
		fs.juxtapose(f, axis=-1)
	fs.into_2d()
	for feature in AVAILABLE_MONO_FEATURES:
		f = io.load_from_file(os.path.join(wkdir, feature))
		fs.juxtapose(f, axis=-1)
	return fs


def leave_one_out(wkdirs, testdir):
	'''
	train and validate on wkdirs, transfer testing on testdir

	:param wkdirs: str or list of str, directory of a subject or some subjects, for train and dev
	:param testdir: str, directory of a subject, for test
	'''
	global VAL_ORD, TOT_VAL, TRAIN_RES, VAL_RES, TEST_RES, TRAIN_RES_G, VAL_RES_G, TEST_RES_G, bad_testers
	VAL_ORD += 1
	logger = DualLogger(os.path.join(logs_dir, 'val-%d.txt' % VAL_ORD))
	os.mkdir(os.path.join(output_dir, 'val-%d' % VAL_ORD))

	print('====== Leave One Out # %d / %d ======\n' % (VAL_ORD, TOT_VAL))
	print('Training and validating on %s' % wkdirs)
	print('Testing on %s' % testdir)
	print()
	wkdirs = [os.path.join(wkdir, 'features') for wkdir in wkdirs]
	tester_name = testdir
	testdir = os.path.join(testdir, 'features')

	# load ######################################################
	# todo can use load from chunks
	print('=== Data ===')
	dataset = DataPack()
	for wkdir in wkdirs:
		dataset += load_features(wkdir)

	print('train & val:')
	dataset.shuffle_all().normalize().into_ndarray().show_shape()

	test = load_features(testdir)
	print('test:')
	test.shuffle_all().normalize().into_ndarray().show_shape()

	print('data loaded.')

	# PCA ######################################################
	# todo adjustable
	# pca_reduction(dataset, test, n_components=20)
	# print('\napplied transform on train, dev & test.')

	train, val = dataset.train_test_split(test_size=0.1)
	print('train shape:')
	train.show_shape()
	print('dev shape:')
	val.show_shape()
	print()

	# visualize ######################################################
	# todo whether to enable distribution visualization
	# output_path1 = os.path.join(output_dir, 'val-%d/Distribution of train & dev.png' % VAL_ORD)
	# output_path2 = os.path.join(output_dir, 'val-%d/Distribution of test.png' % VAL_ORD)
	# dataset.visualize_distribution(title='train & dev', out_path=output_path1)
	# test.visualize_distribution(title='test', out_path=output_path2)

	# classifier ######################################################
	# todo adjustable
	print('=== train & dev ===')
	clf = MySVC(kernel='rbf', gamma='scale', C=1.0, class_weight='balanced', probability=True,
				verbose=False, cache_size=1000)
	# clf = MyKNN(n_neighbors=8, weights='distance', algorithm='auto', leaf_size=30, n_jobs=-1)
	print('\nclf config:\n%s\n' % clf)
	print('gamma =', clf.gamma)

	clf.learn(train)

	print('\ntrain over.')
	print('number of support vectors: ', clf.n_support_)
	print()

	# evaluate ######################################################
	print('=== evaluating ===')

	print('\n== without group voting ==')
	TRAIN_RES += evaluate(clf, 'train', train)
	VAL_RES += evaluate(clf, 'dev', val)
	res = evaluate(clf, 'test', test)
	if res.acc < 0.80: bad_testers.append((tester_name, res.acc))
	TEST_RES += res

	# print('\n== with group voting ==')
	# TRAIN_RES_G += evaluate(clf, 'train', train, group=True)
	# VAL_RES_G += evaluate(clf, 'dev', val, group=True)
	# TEST_RES_G += evaluate(clf, 'test', test, group=True)

	io.save_to_file(clf, os.path.join(model_state_dir, 'val-%d-%s.clf' % (VAL_ORD, type(clf))))
	logger.close()


if __name__ == '__main__':

	since = time.time()
	os.chdir(CWD)
	output_dir = os.path.abspath('output/%s' % FOLDER)
	logs_dir = os.path.abspath('logs/%s' % FOLDER)
	model_state_dir = os.path.abspath('voice/model_state/%s' % FOLDER)
	os.mkdir(output_dir)
	os.mkdir(logs_dir)
	os.mkdir(model_state_dir)
	os.chdir('../Data/Study3/subjects copy')

	subject_dirs = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))  # whole set
	# females = ['gfz', 'jwy', 'mq', 'wrl', 'lgh']
	# males = ['wty', 'wzq', 'yzc', 'xy', 'gyz', 'cjr']
	# subject_dirs = random.sample(females, k=1)
	# subject_dirs += random.sample(males, k=3)
	subject_dirs = subject_dirs[:5]
	print('subjects: ', subject_dirs)
	TOT_VAL = len(subject_dirs)

	for testdir in subject_dirs:
		wkdirs = copy.copy(subject_dirs)
		wkdirs.remove(testdir)
		leave_one_out(wkdirs, testdir)

	os.chdir(CWD)
	logger = DualLogger(os.path.join(logs_dir, 'summary.txt'))
	print('===== Summary =====\n')

	for res in TRAIN_RES, VAL_RES, TEST_RES:#, TRAIN_RES_G, VAL_RES_G, TEST_RES_G:
		res /= TOT_VAL
		res.summary()
	print()

	print('used features:')
	for item in AVAILABLE_MONO_FEATURES:
		print(item, ': mono')
	for item in AVAILABLE_STEREO_FEATURES:
		print(item, ': stereo')
	print()

	print('bad testers:')
	for tester in bad_testers:
		print(tester[0], ':', tester[1])
	print()

	print('label_dict:')
	for gesture in label_dict:
		print(gesture, ':', label_dict[gesture])
	print()

	print('subsampling config:')
	for item in subsampling_config_2_channel:
		print(item, ':', subsampling_config_2_channel[item])
	print()

	elapse = int(time.time() - since)
	minutes = elapse // 60
	seconds = elapse % 60
	print('total run time: %d min %d sec\n' % (minutes, seconds))
	logger.close()

	# save to .csv
	with open(os.path.join(logs_dir, 'summary.csv'), 'w') as f:
		for res in TRAIN_RES, VAL_RES, TEST_RES: #, TRAIN_RES_G, VAL_RES_G, TEST_RES_G:
			f.write(res.as_csv())
