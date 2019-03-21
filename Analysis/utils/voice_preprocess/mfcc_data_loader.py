# load voice mfcc data from .ftr files

import os
import os.path as path
import time
import random

import numpy as np
from tqdm import tqdm

from configs.subsampling_config import subsampling_config_1_channel, subsampling_config_2_channel
from utils import io
from utils.tools import suffix_conv
from utils.voice_preprocess import mfcc
from utils.voice_preprocess.data_loader import DataPack

label_dict = {  # 正负例分类字典, -1 表示舍弃这个特征的所有数据
	'竖直对脸，碰触鼻子': 1,
	'竖直对脸，不碰鼻子': 1,
	'竖屏握持，上端遮嘴': 1,
	'水平端起，倒话筒': 1,
	'话筒': 1,
	'横屏': 1,

	'耳旁打电话': 1,
	'桌上正面': 0,
	'手上正面': 0,
	'桌上反面': 0,
	'手上反面': 0,
	'裤兜': 0,
}


def suffix_filter(files, suffix):
	'''
	return list of files with given suffix
	'''
	return list(filter(lambda x: x.endswith(suffix), files))


class MfccPack(DataPack):
	'''
	mfcc data pack class
	'''

	def __init__(self, data=None, labels=None, names=None, state=None, n_channel=None):
		super(MfccPack, self).__init__(data, labels, names)
		self.state = set() if state is None else state
		self.n_channel = n_channel

	def show_info(self):
		print(' state:')
		for key in self.state:
			print('  ', key)
		print(' n_channel =', self.n_channel)
		print(' shape:')
		self.show_shape()
		print()

	def shuffle_all(self, random_seed=None):
		super().shuffle_all(random_seed)
		self.state.add('shuffled')

	def select_class(self, selected_label: int):
		'''
		select all samples with label
		:param selected_label: 0 or 1
		:return: a sub DataPack
		'''
		data, labels, names = super().select_class(selected_label)
		return MfccPack(data, labels, names, self.state, self.n_channel)

	def __add__(self, other):
		'''
		concatenate another DataPack
		:param other:  DataPack
		'''
		data, labels, names = super().__add__(other)
		return MfccPack(data, labels, names, self.state, self.n_channel)

	# loading method
	def __from_wav_dir(self, wkdir, txtdir=None, cache=False, reload=False, mono=True):
		'''
		dir -> ftr DataPack

		:param wkdir: has lots of wav files, named with date_time
		:param txtdir: .txt files directory, default: wkdir.parent.original
		:param shuffle: whether to shuffle
		:param random_seed: random seed
		:param cache: whether to store ftr data as cache to expedite future loading
		:param reload: whether to reload from wav file to update mfcc data
		:param mono: whether to load into mono channel
		'''
		old_path = os.getcwd()
		os.chdir(wkdir)
		if txtdir is None:
			txtdir = '../original'
		assert path.exists(txtdir)

		ftrs, labels, descriptions = [], [], []

		cached = True if path.exists('.ftrexist.') else False  # cached
		files = suffix_filter(os.listdir('.'), '.ftr' if cached and not reload else '.wav')

		for file_name in files:
			txt_path = path.join(txtdir, suffix_conv(file_name, '.txt'))
			with open(txt_path, 'r', encoding='utf-8') as f:
				f.readline()
				description = f.readline().strip()
			label = label_dict[description]

			if label == -1:  # abandon this piece of data if label == -1
				continue

			ftr = io.load_from_file(file_name) if cached and not reload else mfcc.get_mfcc(file_name, mono=mono)
			if cache == True:
				if not cached or reload: io.save_to_file(ftr, suffix_conv(file_name, '.ftr'))

			ftrs.append(ftr)
			labels.append(label)
			descriptions.append(description)

		if cache == True:
			with open('.ftrexist.', 'w'): pass  # a mark

		os.chdir(old_path)
		self.data, self.labels, self.names = ftrs, labels, descriptions

	def __from_chunks_dir(self, wkdir, txtdir=None, cache=False, reload=False, mono=True):
		'''
		dir -> ftr DataPack

		:param wkdir: has lots of chunk directories, named with date_time
		:param txtdir: .txt files directory, default: wkdir.parent.original
		:param shuffle: whether to shuffle
		:param random_seed: random seed
		:param cache: whether to store ftr data as cache to expedite future loading
		:param reload: whether to reload from wav file to update mfcc data
		:param mono: whether to load into mono channel
		:return: DataPack of ftrs, labels, descriptions
		'''
		old_path = os.getcwd()
		os.chdir(wkdir)
		if txtdir is None:
			txtdir = '../original'
		assert path.exists(txtdir)

		ftrs, labels, descriptions = [], [], []
		wk_cached = True if path.exists('.ftrexist.') else False  # wkdir cached

		chunk_dirs = filter(lambda x: path.isdir(x), os.listdir('.'))
		for chunk_dir in chunk_dirs:
			txt_path = path.join(txtdir, chunk_dir + '.txt')
			with open(txt_path, 'r', encoding='utf-8') as f:
				f.readline()
				description = f.readline().strip()
			label = label_dict[description]

			if label == -1:  # abandon this piece of data if label == -1
				continue

			cached = True if path.exists(path.join(chunk_dir, '.ftrexist.')) else False
			chunks = suffix_filter(os.listdir(chunk_dir), '.ftr' if cached and not reload else '.wav')
			if len(chunks) == 0:
				# 声音太小，没有被识别出来，就在同级目录下寻找.wav
				if wk_cached and not reload:
					file_name = chunk_dir + '.ftr'
					ftr = io.load_from_file(file_name)
				else:
					file_name = chunk_dir + '.wav'
					ftr = mfcc.get_mfcc(file_name, mono=mono)
					if cache == True: io.save_to_file(ftr, suffix_conv(file_name, '.ftr'))
				ftrs.append(ftr)
				labels.append(label)
				descriptions.append(description)
			else:
				for chunk in chunks:
					chunk_path = path.join(chunk_dir, chunk)
					if cached and not reload:
						ftr = io.load_from_file(chunk_path)
					else:
						ftr = mfcc.get_mfcc(chunk_path, mono=mono)
					if cache == True:
						if not cached or reload: io.save_to_file(ftr, suffix_conv(chunk_path, '.ftr'))
						with open(path.join(chunk_dir, '.ftrexist.'), 'w'):
							pass  # a mark
					ftrs.append(ftr)
					labels.append(label)
					descriptions.append(description)

		if cache == True:
			with open('.ftrexist.', 'w'): pass  # a mark

		os.chdir(old_path)
		self.data, self.labels, self.names = ftrs, labels, descriptions

	def __load_sequential(self, one_step: callable, wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False,
						  reload=False, mono=True):
		if type(wkdir) == str:
			one_step(wkdir, txtdir=txtdir, cache=cache, reload=reload, mono=mono)
			if shuffle == True: self.shuffle_all(random_seed)
		elif type(wkdir) == list:
			if txtdir == None: txtdir = [None for _ in wkdir]

			total = MfccPack()
			progress = tqdm(total=len(wkdir))
			for wkdir_, txtdir_ in zip(wkdir, txtdir):
				progress.update()
				one_step(wkdir_, txtdir=txtdir_, cache=cache, reload=reload, mono=mono)
				# concatenate
				total += self

			self.data, self.labels, self.names = total
			if shuffle == True: self.shuffle_all(random_seed)
		else:
			raise TypeError('type of wkdir which equals %s is neither str nor list.' % type(wkdir))

		if mono == True:
			self.n_channel = 1
		else:
			ftr = self.data[0]
			ndim = np.ndim(ftr)
			if ndim == 2:  # shape (n_mfcc, n_frame)
				self.n_channel = 1
			elif ndim == 3:  # shape (n_channel, n_mfcc, n_frame)
				self.n_channel = np.shape(ftr)[0]
			else:
				raise AttributeError('ndim %d is not valid.' % ndim)
		self.state.add('loaded')
		return self

	def from_wav_dir(self, wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False, reload=False, mono=True):
		''' entrance
		dir or dirs -> ftr DataPack

		:param wkdir: str or list, has lots of wav files, named with date_time
		:param txtdir: str or list, .txt files directory, default: list of wkdir.parent.original
		:param cache: whether to store ftr data as cache to expedite future loading
		:param reload: whether to reload from wav file to update mfcc data
		:param mono: whether to load into mono channel
		:return: DataPack of ftrs, labels, descriptions
		'''
		return self.__load_sequential(self.__from_wav_dir, wkdir, txtdir, shuffle, random_seed, cache, reload, mono)

	def from_chunks_dir(self, wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False, reload=False, mono=True):
		'''
		dir(s) -> ftr DataPack

		:param wkdir: str or list, has lots of chunk directories, named with date_time
		:param txtdir: str or list, .txt files directory, default: wkdir.parent.original
		:param cache: whether to store ftr data as cache to expedite future loading
		:param reload: whether to load from wav file to update mfcc data
		:param mono: whether to load into mono channel
		:return: DataPack of ftrs, labels, descriptions
		'''
		return self.__load_sequential(self.__from_chunks_dir, wkdir, txtdir, shuffle, random_seed, cache, reload, mono)

	# subsampling methods

	def apply_subsampling(self, shuffle=True, random_seed=None):
		'''
		对 DataPack 施用采样，并保持labels，names长度平齐

		:return: new DataPack after conversion, (n_window, [n_channel,] n_mfcc, n_subframe)
		'''
		new_data = []
		new_labels = []
		new_names = []
		if self.n_channel == 1:
			config = subsampling_config_1_channel
			for ftr, label, name in zip(self.data, self.labels, self.names):
				windows = _subsampling(ftr, config['offset'], config['duration'], config['window'], config['stride'])
				new_data += windows
				extended = _extend_labels_names(windows, label, name)
				new_labels += extended.labels
				new_names += extended.names
		else:  # multi channel
			config = subsampling_config_2_channel
			for ftr, label, name in zip(self.data, self.labels, self.names):
				channels_windows = np.array([
					_subsampling(ftr[channel], config['offset'], config['duration'], config['window'], config['stride'])
					for channel in range(self.n_channel)])
				# (n_channel, n_window, n_mfcc, n_subframe)
				windows_channels = list(np.rollaxis(channels_windows, 0, 2))
				# (n_window, n_channel, n_mfcc, n_subframe)
				new_data += windows_channels
				extended = _extend_labels_names(windows_channels, label, name)
				new_labels += extended.labels
				new_names += extended.names

		self.data, self.labels, self.names = new_data, new_labels, new_names
		if shuffle == True: self.shuffle_all(random_seed)
		assert len(new_data) > 0
		self.state.add('subsample')
		return self

	def apply_subsampling_grouping(self, shuffle=True, random_seed=None):
		'''
		对 DataPack 施用子采样和重组，并保持labels，names长度平齐

		:return: new DataPack after conversion, (n_group, n_window, [n_channel,] n_mfcc, n_subframe)
		'''
		new_data = []
		new_labels = []
		new_names = []
		if self.n_channel == 1:
			config = subsampling_config_1_channel
			for ftr, label, name in zip(self.data, self.labels, self.names):
				windows = _subsampling(ftr, config['offset'], config['duration'], config['window'], config['stride'])
				groups = _grouping(windows, config['group_size'])
				# (n_group, n_window, n_mfcc, n_subframe)
				new_data += groups
				extended = _extend_labels_names(groups, label, name)
				new_labels += extended.labels
				new_names += extended.names
		else:  # multichannel
			config = subsampling_config_2_channel
			for ftr, label, name in zip(self.data, self.labels, self.names):
				channels_windows = np.array([
					_subsampling(ftr[channel], config['offset'], config['duration'], config['window'], config['stride'])
					for channel in range(self.n_channel)])
				# (n_channel, n_window, n_mfcc, n_subframe)
				windows_channels = list(np.rollaxis(channels_windows, 0, 2))
				# (n_window, n_channel, n_mfcc, n_subframe)
				groups = _grouping(windows_channels, config['group_size'])
				# (n_group, n_window, n_channel, n_mfcc, n_subframe)
				new_data += groups
				extended = _extend_labels_names(groups, label, name)
				new_labels += extended.labels
				new_names += extended.names

		self.data, self.labels, self.names = new_data, new_labels, new_names
		if shuffle == True: self.shuffle_all(random_seed)
		assert len(new_data) > 0
		self.state.add('subsample')
		self.state.add('group')
		return self

	def _ungroup(self, extend_labels=False, extend_names=False):
		'''
		temporarily ungroup
		'''
		if 'group' in self.state:  # else do nothing
			self.__shape = np.array(self.data).shape
			self.data = np.reshape(self.data, (self.__shape[0] * self.__shape[1], self.__shape[2]))
			if extend_labels:
				new_labels = []
				for label in self.labels:
					for i in range(self.__shape[1]):
						new_labels.append(label)
				self.__labels = self.labels  # cache
				self.labels = new_labels
			if extend_names:
				new_names = []
				for name in self.names:
					for i in range(self.__shape[1]):
						new_names.append(name)
				self.__names = self.names  # cache
				self.names = new_names
		return self

	def _regroup(self, lessen_labels=False, lessen_names=False):
		'''
		recover from temporary ungrouping
		'''
		if 'group' in self.state:  # else do nothing
			_shape = np.shape(self.data)
			self.data = np.reshape(self.data, (self.__shape[0], self.__shape[1], _shape[-1]))
			if lessen_labels:
				self.labels = self.__labels
			if lessen_names:
				self.names = self.__names
		return self

	def train_test_split(self, test_size=None):
		'''
		files or groups (DataPack) -> train_pack + test_pack

		:param test_size: test size ratio, float number
		:return: train_pack, test_pack
		'''
		train, test = super().train_test_split(test_size)
		return MfccPack(train.data, train.labels, train.names, self.state, self.n_channel), \
			   MfccPack(train.data, train.labels, train.names, self.state, self.n_channel)

	def to_flatten(self):
		'''
		压扁时间、通道（如果有）维度的数据
		'''
		if 'subsample' in self.state:
			if 'group' in self.state:
				# (n_group, n_window, [n_channel,] n_mfcc, n_subframe)
				self.data = [[window.flatten() for window in group] for group in self.data]
			else:
				# (n_window, [n_channel,] n_mfcc, n_subframe)
				self.data = [window.flatten() for window in self.data]
		else:
			raise AttributeError('You can\'t flatten it now, because subsampling is not applied yet.')

		self.state.add('flatten')
		return self

	def visualize_distribution(self, dim1: int = 0, dim2: int = 1, title: str = '???', out_path=None):
		'''
		scatter the distribution of dataset projected on dim1 and dim2, with color of each class
		self.state: has `subsample`, but no `group`
		'''
		from matplotlib import pyplot as plt
		self._ungroup(extend_labels=True)
		X0 = np.array(self.select_class(0).data)
		n, p = None, None
		if X0.ndim > 1: n = plt.scatter(X0[:, dim1], X0[:, dim2], s=1, c='blue')
		X1 = np.array(self.select_class(1).data)
		self._regroup(lessen_labels=True)
		if X1.ndim > 1: p = plt.scatter(X1[:, dim1], X1[:, dim2], s=1, c='red')
		name = 'Distribution of %s' % title
		plt.title(name)
		plt.xlabel('Dim %d' % dim1)
		plt.ylabel('Dim %d' % dim2)
		plt.legend([n, p], ['-', '+'])
		if out_path: plt.savefig(out_path)
		plt.show()


def _subsampling(ftr, offset, duration, window, stride):
	'''
	ftr data -> list of units

	对单个ftr数据进行子采样，得到一系列子样本单元

	:param ftr: 从单个 .ftr 文件读到的数据, shape like (n_mfcc, n_frame)
	:param offset: 偏移量，毫秒
	:param duration: 采样长度，毫秒
	:param window: 采样单元长度
	:param stride: 每次采样的步长
	:return: list of windows, shape like (n_window, n_mfcc, n_frame)
	'''
	windows = []
	high = min(offset + duration, ftr.shape[-1])
	left = offset
	right = left + window
	while right <= high:
		windows.append(ftr[:, left: right])
		left += stride
		right += stride
	return windows


def _grouping(units, group_size):
	'''
	从单元列表得到组合列表，会忽略末尾凑不足group_size的单元
	可以不用这种表示方法

	:param units: list of units, shape like (n_unit, ...)
	:param group_size: size of each group
	:return: list of groups, shape like (n_group, n_unit, ...) where n_group = n_unit // group_size
	'''
	groups, group = [], []
	for unit in units:
		group.append(unit)
		if len(group) == group_size:
			groups.append(group)
			group = []
	return groups


def _extend_labels_names(data, label, name):
	'''
	.ftr 数据经过 subsampling 或者 grouping 处理后会变成多份，此函数可以将 label, name 也补齐

	:param data: a list of units or groups generated from one .ftr data
	:return: DataPack of (data, labels, names)
	'''
	return MfccPack(data, [label for _ in data], [name for _ in data])


if __name__ == '__main__':
	from configs.subsampling_config import subsampling_config_1_channel
	import random

	os.chdir('/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects copy/')
	subjects = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	# wkdirs = random.sample(wkdirs, k=4)
	# wkdirs.remove('mq')
	# wkdirs = ['mq', 'gfz', 'zfs']
	print(subjects)
	subjects = list(map(lambda x: os.path.join(x, 'trimmed2channel'), subjects))

	pack = MfccPack()
	pack.from_chunks_dir(subjects, shuffle=False, cache=True, reload=False, mono=False)
	pack.show_info()

	pack.apply_subsampling_grouping()
	pack.show_info()

	pack.to_flatten()
	pack.show_info()
