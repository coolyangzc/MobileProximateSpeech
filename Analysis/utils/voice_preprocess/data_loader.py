import numpy as np
import random
import time


def show_shape(iterable):
	try:
		print(np.array(iterable).shape)
	except ValueError:
		print('the shape is not standard, len = %d.' % len(iterable))


class DataPack(object):
	def __init__(self, data=None, labels=None, names=None):
		self.data = [] if data is None else data  # list of samples
		self.labels = [] if labels is None else labels  # list of labels
		self.names = [] if names is None else names  # list of str

	def __iter__(self):
		self.n_var = 0
		return self

	def __next__(self):
		n_var = self.n_var
		self.n_var += 1
		if n_var == 0:
			return self.data
		elif n_var == 1:
			return self.labels
		elif n_var == 2:
			return self.names
		else:
			raise StopIteration

	def show_shape(self):
		print('  data: ', end='')
		show_shape(self.data)
		print('  labels: ', end='')
		show_shape(self.labels)
		print('  names: ', end='')
		show_shape(self.names)
		return self

	def shuffle_all(self, random_seed=None):
		if random_seed is None: random_seed = time.time()
		random.seed(random_seed)
		random.shuffle(self.data)
		random.seed(random_seed)
		random.shuffle(self.labels)
		random.seed(random_seed)
		random.shuffle(self.names)
		return self

	def select_class(self, selected_label: int):
		samples, labels, names = [], [], []
		for sample, label, name in zip(self.data, self.labels, self.names):
			if label == selected_label:
				samples.append(sample)
				labels.append(label)
				names.append(name)
		return DataPack(samples, labels, names)

	def select_classes(self, selected_labels: list):
		samples, labels, names = [], [], []
		for sample, label, name in zip(self.data, self.labels, self.names):
			if label in selected_labels:
				samples.append(sample)
				labels.append(label)
				names.append(name)
		return DataPack(samples, labels, names)

	def crop(self, size: int):
		'''
		crop the datapack to the designated size ( ≤ len(self.data) )
		'''
		self.data = self.data[:size]
		self.labels = self.labels[:size]
		self.names = self.names[:size]
		return self

	def __add__(self, other):
		'''
		concatenate another DataPack
		:param other:  DataPack
		'''
		return DataPack(list(self.data) + list(other.data), self.labels + other.labels, self.names + other.names)

	def roll_data_axis(self, axis, start):
		self.data = list(np.rollaxis(np.array(self.data), axis, start))
		return self

	def train_test_split(self, test_size=None):
		'''
		files or groups (DataPack) -> train_pack + test_pack

		:param test_size: test size ratio, float number
		:return: train_pack, test_pack
		'''
		if test_size is None:  # auto
			if len(self.data) < 5000:
				test_size = 0.3
			elif len(self.data) < 10000:
				test_size = 0.2
			elif len(self.data) < 50000:
				test_size = 0.1
			else:
				test_size = 0.05
		else:
			assert 0.0 <= test_size <= 1.0
		cut = int(len(self.data) * test_size)
		return DataPack(self.data[cut:], self.labels[cut:], self.names[cut:]), \
			   DataPack(self.data[:cut], self.labels[:cut], self.names[:cut])
