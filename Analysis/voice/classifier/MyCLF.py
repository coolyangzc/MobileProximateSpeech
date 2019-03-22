from collections import Counter

import numpy as np
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from tqdm import tqdm

from utils.voice_preprocess.data_loader import DataPack
from utils.voice_preprocess.wav_loader import label_dict, doc_dict

gestures = label_dict.keys()
epsilon = 1e-8

def to_category(labels):
	ys = np.array(labels)
	ys[ys > 0] = 1
	ys[ys < 0] = 0
	return ys


class MySVC(SVC):
	'''
	Support Vector Classifier which provide feedback of incorrect classified samples' descriptions
	'''

	def learn(self, dataset: DataPack):
		super().fit(dataset.data, to_category(dataset.labels))

	def predict_grouply(self, data):
		'''
		predict the dataset which is applied grouping

		:param data: ndarray, shape like (n_group, n_sample, n_feature)
		:return: a list of predicted labels
		'''
		assert np.ndim(data) == 3
		preds = []
		for group in data:
			prob_sum = np.sum(self.predict_proba(group), axis=0)
			preds.append(0 if prob_sum[0] > prob_sum[1] else 1)
		return preds

	def predict_proba_grouply(self, data):
		'''
		predict probabilities of the dataset which is applied grouping

		:param data: ndarray, shape like (n_group, n_sample, n_feature)
		:return: a list of probabilities of two class
		'''
		assert np.ndim(data) == 3
		probs = []
		for group in data:
			prob = np.mean(self.predict_proba(group), axis=0)
			probs.append(prob)
		return probs

	def evaluate(self, dataset: DataPack, group=False):
		'''
		score dataset with mistake count

		:param dataset: datapack to evaluate
		:param group: whether the dataset is applied with grouping, if so, the predict function will be treated uniquely
		:return: tuple, (accuracy, f1, mistake count dict, counter of each gesture)
		'''
		if group == True:
			predictions = self.predict_grouply(dataset.data)
		else:
			predictions = self.predict(dataset.data)

		labels = dataset.labels
		ys = to_category(labels)

		counter = Counter(labels)  # count each gesture
		mistakes = Counter()  # incorrect count for all gestures
		tp, tn, fp, fn = 0, 0, 0, 0

		for prediction, y, label in zip(predictions, ys, labels):
			if prediction == y:
				if y == 1:
					tp += 1
				else:
					tn += 1
			else:  # classified wrongly
				if y == 1:
					fn += 1
				else:
					fp += 1
				mistakes.update([label])
		precision = tp / (tp + fp + epsilon)
		recall = tp / (tp + fn + epsilon)
		acc = (tp + tn) / (tp + tn + fp + fn + epsilon)
		f1 = 2 * precision * recall / (precision + recall + epsilon)

		return acc, f1, mistakes, counter

	def get_predict_proba_distribution(self, dataset: DataPack, group=False):
		'''
		get the predict probability distribution over dataset

		:param dataset: datapack to evaluate
		:param group: whether the dataset is applied with grouping, if so, the predict function will be treated uniquely
		:return: tuple, (true_prob_list, false_prob_list)
		'''
		true_prob_list, false_prob_list = [], []
		if group == True:
			probs = self.predict_proba_grouply(dataset.data)
			preds = self.predict_grouply(dataset.data)
			labels = dataset.labels
			ys = to_category(labels)
		else:
			ys = to_category(dataset.labels)
			probs = self.predict_proba(dataset.data)
			preds = np.argmax(probs, axis=1)

		for prob, pred, target in zip(probs, preds, ys):
			if pred == target:
				true_prob_list.append(prob[pred])
			else:
				false_prob_list.append(prob[pred])

		return true_prob_list, false_prob_list

class MyKNN(KNeighborsClassifier):
	'''
	KNeighborsClassifier which provide feedback of incorrect classified samples' descriptions
	'''

	def learn(self, dataset: DataPack):
		dataset._ungroup(extend_labels=True)
		super().fit(dataset.data, dataset.labels)
		dataset._regroup(lessen_labels=True)

	def predict_grouply(self, data):
		'''
		predict the dataset which is applied grouping

		:param data: ndarray, shape like (n_group, n_sample, n_feature)
		:return: a list of predicted labels
		'''
		assert np.ndim(data) == 3
		preds = []
		_shape = np.shape(data)
		data = np.reshape(data, (_shape[0] * _shape[1], _shape[-1]))
		probs = self.predict_proba(data)
		probs = np.reshape(probs, (_shape[0], _shape[1], 2))
		for group in probs:
			prob_sum = np.sum(group, axis=0)
			preds.append(0 if prob_sum[0] > prob_sum[1] else 1)
		return preds

	def predict_proba_grouply(self, data):
		'''
		predict probabilities of the dataset which is applied grouping

		:param data: ndarray, shape like (n_group, n_sample, n_feature)
		:return: a list of probabilities of two class
		'''
		assert np.ndim(data) == 3
		probs = []
		for group in tqdm(data):
			prob = np.mean(self.predict_proba(group), axis=0)
			probs.append(prob)
		return probs

	def evaluate(self, dataset: DataPack, group=False):
		'''
		score dataset with mistake count

		:param dataset: datapack to evaluate
		:param group: whether the dataset is applied with grouping, if so, the predict function will be treated uniquely
		:return: tuple, (accuracy, f1, mistake count dict, counter of each gesture)
		'''
		if group == True:
			predictions = self.predict_grouply(dataset.data)
			_, labels, names = dataset
		else:
			_, labels, names = dataset._ungroup(extend_labels=True, extend_names=True)
			predictions = self.predict(dataset.data)
			dataset._regroup(lessen_labels=True, lessen_names=True)

		counter = Counter(names)  # count each gesture
		mistakes = Counter()  # incorrect count for all gestures
		tp, tn, fp, fn = 0, 0, 0, 0

		for prediction, label, gesture in zip(predictions, labels, names):
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
				mistakes.update([gesture])
		precision = tp / (tp + fp)
		recall = tp / (tp + fn)
		acc = (tp + tn) / (tp + tn + fp + fn)
		f1 = 2 * precision * recall / (precision + recall)

		return acc, f1, mistakes, counter

	def get_predict_proba_distribution(self, dataset: DataPack, group=False):
		'''
		get the predict probability distribution over dataset

		:param dataset: datapack to evaluate
		:param group: whether the dataset is applied with grouping, if so, the predict function will be treated uniquely
		:return: tuple, (true_prob_list, false_prob_list)
		'''
		true_prob_list, false_prob_list = [], []
		if group == True:
			probs = self.predict_proba_grouply(dataset.data)
			preds = self.predict_grouply(dataset.data)
			labels = dataset.labels
		else:
			labels = dataset._ungroup(extend_labels=True).labels
			probs = self.predict_proba(dataset.data)
			dataset._regroup(lessen_labels=True)
			preds = np.argmax(probs, axis=1)

		for prob, pred, target in zip(probs, preds, labels):
			if pred == target:
				true_prob_list.append(prob[pred])
			else:
				false_prob_list.append(prob[pred])

		return true_prob_list, false_prob_list
