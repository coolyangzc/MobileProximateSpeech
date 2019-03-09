from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import Perceptron
from utils.voice_preprocess import mfcc_data_loader
from utils.voice_preprocess.mfcc_data_loader import DataPack
from utils.tools import date_time
from utils.logger import DualLogger
import os
from utils.io import *
import copy
from collections import Counter
from utils.voice_preprocess.mfcc_data_loader import label_dict
import numpy as np

gestures = label_dict.keys()

class MySVC(SVC):
	'''
	Support Vector Classifier which provide feedback of incorrect classified samples' descriptions
	'''
	def score(self, dataset: DataPack):
		'''
		score dataset with mistake count

		:param dataset: test datapack
		:return: tuple, (accuracy, f1, mistake rate dict)
		'''
		counter = Counter(dataset.names) # count each gesture
		mistakes = {} # incorrect rates for all gestures
		for gesture in gestures: mistakes[gesture] = 0
		tp, tn, fp, fn = 0, 0, 0, 0
		predictions = self.predict(dataset.data)
		for prediction, label, gesture in zip(predictions, dataset.labels, dataset.names):
			if prediction == label:
				if label == 1:
					tp += 1
				else:
					tn += 1
			else: # classified wrongly
				if label == 1:
					fn += 1
				else:
					fp += 1
				mistakes[gesture] += 1
		precision = tp / (tp + fp)
		recall = tp / (tp + fn)
		acc = (tp + tn) / (tp + tn + fp + fn)
		f1 = 2 * precision * recall / (precision + recall)

		for gesture in mistakes:
			mistakes[gesture] /= counter[gesture]

		return acc, f1, mistakes


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


os.chdir('..')

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
DualLogger('logs/%sMLP(chunk) train' % DATE_TIME)
# res = leave_one_out_val(wkdirs)


# save_to_file(res, 'logs/%sEvaluation Result' % DATE_TIME)



# todo can use load from chunks
dataset = DataPack()
dataset.from_chunks_dir(wkdirs, cache=True, reload=True)

test = DataPack()
test.from_chunks_dir(testdir, cache=True, reload=True)
print('data loaded.')

print('train shape:')
dataset.show_shape()

print('test  shape:')
test.show_shape()

dataset.apply_subsampling()
test.apply_subsampling()

dataset.to_flatten()
test.to_flatten()
print('\nafter flatten:')
print('train shape:')
dataset.show_shape()

print('test  shape:')
test.show_shape()

train, val = dataset.train_test_split(test_size=0.1)

print('\n\n=== train & dev ===')
# todo adjustable
clf = MySVC(kernel='rbf', gamma='auto', C=1.0, verbose=True)
# clf = MLPClassifier(hidden_layer_sizes=(300, 200, 100, 10),
# 					activation='relu', solver='adam',
# 					learning_rate_init=1e-5, verbose=True, shuffle=True)
# clf = Perceptron(alpha=1e3)
print('\nclf config:\n%s\n' % clf)

clf.fit(train.data, train.labels)
print('\ntrain over.\n')

print('=== evaluating ===\n')

def evaluate(which, dataset: DataPack):
	print('== on %s ==' % which)
	acc, f1, mistakes = clf.score(dataset)
	print('acc = %.4f%%, f1 = %.4f%%' % (acc * 100, f1 * 100))
	print('mistakes rate:')
	for description in mistakes:
		print('\t%s:  %.2f%%' % (description, mistakes[description] * 100))
	print()

evaluate('train', train)
evaluate('dev', val)
evaluate('test', test)

save_to_file(clf, 'voice/model_state/%s%s(chunk).clf' % (DATE_TIME, type(clf)))
