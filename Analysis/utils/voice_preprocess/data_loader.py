import os
import random
import re
import time
from collections import Counter

import numpy as np
from tqdm import tqdm

from utils import io
from utils.tools import suffix_conv, suffix_filter


def show_shape(iterable, end='\n'):
	try:
		print(np.array(iterable).shape, end=end)
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
		show_shape(self.data, end='\t')
		print('labels: ', end='')
		show_shape(self.labels, end='\t')
		print('names: ', end='')
		show_shape(self.names)
		print()
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

	def select_classes(self, selected_labels):
		selected_labels = set(selected_labels)
		samples, labels, names = [], [], []
		for sample, label, name in zip(self.data, self.labels, self.names):
			if label in selected_labels:
				samples.append(sample)
				labels.append(label)
				names.append(name)
		return DataPack(samples, labels, names)

	def into_ndarray(self):
		self.data = np.array(self.data)
		return self

	def into_list(self):
		self.data = list(self.data)
		return self

	def into_2d(self):
		self.data = np.array([x.flatten() for x in self.data])
		return self

	def squeeze_data(self):
		'''
		squeeze data axis but 0
		'''
		for axis in range(1, np.ndim(self.data)):
			try:
				self.data = np.squeeze(self.data, axis=axis)
			except:
				pass
		return self

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

	def juxtapose(self, other, axis):
		'''
		concatenate another DataPack parallelly

		:param other: DataPack
		:param axis: which axis of data to concatenate
		:return: self
		'''
		if len(self.data) == 0:
			self.data = other.data
			self.labels = other.labels
			self.names = other.names
		else:
			self.data = np.concatenate((self.data, other.data), axis=axis)
		return self

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

	def from_data_dir(self, data_dir, txt_dir, format, data_getter: callable, label_getter: callable, desc='loading'):
		'''
		load from data directory, e.g. 'cjr/trimmed2channel/'

		:param data_dir: directory including lots of data files
		:param txt_dir: directory including lots of .txt
		:param format: 'wav', 'mp4' and so on...
		:return: self, data shape like (n_audio, [n_channel,] n_frame[i])
		'''
		txt_dir = os.path.abspath(txt_dir)
		owd = os.getcwd()
		os.chdir(data_dir)

		file_names = suffix_filter(os.listdir('.'), format)
		for file_name in tqdm(file_names, desc=desc, leave=False):
			# get label
			txt_path = os.path.join(txt_dir, suffix_conv(file_name, '.txt'))
			try:
				label = label_getter(txt_path)
			except FileNotFoundError as e:
				print(e)
				continue
			# get data
			x = data_getter(file_name)
			# store to self
			self.data.append(x)
			self.labels.append(label)
			self.names.append(os.path.abspath(file_name))

		os.chdir(owd)
		return self

	def auto_save(self, folder_name, suffix='.ftr'):
		'''
		auto save the data to their source directory's folder_name

		:param folder_name: sub_dir in every subject, should be the basename of a folder
		'''
		source_pattern = re.compile('(.+Data/Study\d/[\w ]+/[\w ]+/)[\w ]+/(.+)', re.U)

		name_counter = Counter()
		progress = tqdm(total=len(self.labels), desc='saving', leave=False)
		for x, path in zip(self.data, self.names):
			progress.update()
			mt = source_pattern.match(path)
			source_dir = mt.group(1)
			name = mt.group(2).replace('/', ' - ').split('.')[0]
			dst_name = name + ' #%d' % name_counter[name] + suffix
			name_counter.update([name])

			dst_dir = os.path.join(source_dir, folder_name)
			if not os.path.exists(dst_dir):
				os.mkdir(dst_dir)

			dst_path = os.path.join(dst_dir, dst_name)
			io.save_to_file(x, dst_path)

	def grouping(self, group_size):
		'''
		从self.data得到组合列表，会忽略末尾凑不足group_size的单元
		可以不用这种表示方法

		:param group_size: size of each group
		:return: list of groups, shape like (n_group, n_unit, ...) where n_group = n_unit // group_size
		'''
		groups, group = [], []
		for x in self.data:
			group.append(x)
			if len(group) == group_size:
				groups.append(group)
				group = []
		self.data = groups
		return self

	def normalize(self, std=True):
		self.into_ndarray()
		mean = np.mean(self.data, axis=0, keepdims=True)
		self.data -= mean
		if std:
			std = np.std(self.data, axis=0, keepdims=True)
			self.data /= std
		return self
