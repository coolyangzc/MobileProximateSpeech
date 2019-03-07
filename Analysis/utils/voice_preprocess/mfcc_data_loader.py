# load voice mfcc data from .ftr files

from utils import io
from utils.voice_preprocess import mfcc
from utils.tools import suffix_conv
import os
import os.path as path
import random
import time
import numpy as np
from configs.subsampling_config import subsampling_config

# DataPack = namedtuple('DataPack', 'data labels names')

label_dict = {  # 正负例分类字典
	'竖直对脸，碰触鼻子': 1,
	'竖直对脸，不碰鼻子': 1,
	'竖屏握持，上端遮嘴': 1,
	'水平端起，倒话筒': 1,
	'话筒': 1,
	'横屏': 1,

	'耳旁打电话': 0,
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


def show_shape(iterable):
	try:
		print(np.array(iterable).shape)
	except ValueError:
		print('the shape is not standard, len = %d.' % len(iterable))


class DataPack:
	'''
	mfcc data pack class
	'''

	def __init__(self, data=None, labels=None, names=None):
		self.data = [] if data is None else data  # list of samples
		self.labels = [] if labels is None else labels  # list of numbers
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
		print('data: ', end='')
		show_shape(self.data)
		print('labels: ', end='')
		show_shape(self.labels)
		print('names: ', end='')
		show_shape(self.names)

	def shuffle_all(self, random_seed=None):
		if random_seed is None: random_seed = time.time()
		random.seed(random_seed)
		random.shuffle(self.data)
		random.seed(random_seed)
		random.shuffle(self.labels)
		random.seed(random_seed)
		random.shuffle(self.names)

	def __add__(self, other):
		'''
		concatenate another DataPack
		:param other:  DataPack
		'''
		return DataPack(self.data + other.data, self.labels + other.labels, self.names + other.names)

	# loading method

	def __from_wav_dir(self, wkdir, txtdir=None, cache=False):
		'''
		dir -> ftr DataPack

		:param wkdir: has lots of wav files, named with date_time
		:param txtdir: .txt files directory, default: wkdir.parent.original
		:param shuffle: whether to shuffle
		:param random_seed: random seed
		:param cache: whether to store ftr data as cache to expedite future loading
		'''
		old_path = os.getcwd()
		os.chdir(wkdir)
		if txtdir is None:
			txtdir = '../original'
		assert path.exists(txtdir)

		ftrs, labels, descriptions = [], [], []

		cached = True if path.exists('.ftrexist.') else False  # cached
		files = suffix_filter(os.listdir('.'), '.ftr' if cached else '.wav')

		for file_name in files:
			ftr = io.load_from_file(file_name) if cached else mfcc.get_mfcc(file_name)
			if cache == True and cached == False:
				io.save_to_file(ftr, suffix_conv(file_name, '.ftr'))

			txt_path = path.join(txtdir, suffix_conv(file_name, '.txt'))
			with open(txt_path, 'r', encoding='utf-8') as f:
				f.readline()
				description = f.readline().strip()
			label = label_dict[description]

			ftrs.append(ftr)
			labels.append(label)
			descriptions.append(description)

		if cache == True:
			with open('.ftrexist.', 'w'): pass  # a mark

		os.chdir(old_path)
		self.data, self.labels, self.names = ftrs, labels, descriptions

	def __from_chunks_dir(self, wkdir, txtdir=None, cache=False):
		'''
		dir -> ftr DataPack

		:param wkdir: has lots of chunk directories, named with date_time
		:param txtdir: .txt files directory, default: wkdir.parent.original
		:param shuffle: whether to shuffle
		:param random_seed: random seed
		:param cache: whether to store ftr data as cache to expedite future loading
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

			cached = True if path.exists(path.join(chunk_dir, '.ftrexist.')) else False
			chunks = suffix_filter(os.listdir(chunk_dir), '.ftr' if cached else '.wav')
			if len(chunks) == 0:
				# 声音太小，没有被识别出来，就在同级目录下寻找.wav
				if wk_cached:
					file_name = chunk_dir + '.ftr'
					ftr = io.load_from_file(file_name)
				else:
					file_name = chunk_dir + '.wav'
					ftr = mfcc.get_mfcc(file_name)
					if cache == True: io.save_to_file(ftr, suffix_conv(file_name, '.ftr'))
				ftrs.append(ftr)
				labels.append(label)
				descriptions.append(description)
			else:
				for chunk in chunks:
					chunk_path = path.join(chunk_dir, chunk)
					ftr = io.load_from_file(chunk_path) if cached else mfcc.get_mfcc(chunk_path)
					if cache == True:
						if cached == False: io.save_to_file(ftr, suffix_conv(chunk_path, '.ftr'))
						with open(path.join(chunk_dir, '.ftrexist.'), 'w'):
							pass  # a mark
					ftrs.append(ftr)
					labels.append(label)
					descriptions.append(description)

		if cache == True:
			with open('.ftrexist.', 'w'): pass  # a mark

		os.chdir(old_path)
		self.data, self.labels, self.names = ftrs, labels, descriptions

	def __load_sequential(self, one_step: callable, wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False):
		if type(wkdir) == str:
			one_step(wkdir, txtdir, cache)
			if shuffle == True: self.shuffle_all(random_seed)
		elif type(wkdir) == list:
			if txtdir == None: txtdir = [None for _ in wkdir]

			total = DataPack()
			for wkdir_, txtdir_ in zip(wkdir, txtdir):
				one_step(wkdir_, txtdir_, cache=cache)
				# concatenate
				total += self

			self.data, self.labels, self.names = total
			if shuffle == True: self.shuffle_all(random_seed)
		else:
			raise TypeError('type of wkdir which equals %s is neither str nor list.' % type(wkdir))

	def from_wav_dir(self, wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False):
		''' entrance
		dir or dirs -> ftr DataPack

		:param wkdir: str or list, has lots of wav files, named with date_time
		:param txtdir: str or list, .txt files directory, default: list of wkdir.parent.original
		:param cache: whether to store ftr data as cache to expedite future loading
		:return: DataPack of ftrs, labels, descriptions
		'''
		self.__load_sequential(self.__from_wav_dir, wkdir, txtdir, shuffle, random_seed, cache)

	def from_chunks_dir(self, wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False):
		'''
		dir(s) -> ftr DataPack

		:param wkdir: str or list, has lots of chunk directories, named with date_time
		:param txtdir: str or list, .txt files directory, default: wkdir.parent.original
		:param cache: whether to store ftr data as cache to expedite future loading
		:return: DataPack of ftrs, labels, descriptions
		'''
		self.__load_sequential(self.__from_chunks_dir, wkdir, txtdir, shuffle, random_seed, cache)

	# subsampling methods

	def apply_subsampling(self,
						  offset=subsampling_config['offset'],
						  duration=subsampling_config['duration'],
						  window=subsampling_config['window'],
						  stride=subsampling_config['stride'],
						  shuffle=True, random_seed=None):
		'''
		对 DataPack 施用采样，并保持labels，names长度平齐

		:return: new DataPack after conversion
		'''
		new_data = []
		new_labels = []
		new_names = []
		for ftr, label, name in zip(self.data, self.labels, self.names):
			new_elem = _subsampling(ftr, offset, duration, window, stride)
			new_data += new_elem
			extended = _extend_labels_names(new_elem, label, name)
			new_labels += extended.labels
			new_names += extended.names

		self.data, self.labels, self.names = new_data, new_labels, new_names
		if shuffle == True: self.shuffle_all(random_seed)
		assert len(new_data) > 0

	def apply_subsampling_grouping(self,
								   offset=subsampling_config['offset'],
								   duration=subsampling_config['duration'],
								   window=subsampling_config['window'],
								   stride=subsampling_config['stride'],
								   group_size=subsampling_config['group_size'],
								   shuffle=True, random_seed=None):
		'''
		对 DataPack 施用子采样和重组，并保持labels，names长度平齐

		:return: new DataPack after conversion
		'''
		new_data = []
		new_labels = []
		new_names = []
		for ftr, label, name in zip(self.data, self.labels, self.names):
			units = _subsampling(ftr, offset, duration, window, stride)
			groups = _grouping(units, group_size)
			new_data += groups
			extended = _extend_labels_names(groups, label, name)
			new_labels += extended.labels
			new_names += extended.names

		self.data, self.labels, self.names = new_data, new_labels, new_names
		if shuffle == True: self.shuffle_all(random_seed)
		assert len(new_data) > 0

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

	def to_flatten(self):
		'''
		压扁时间维度的数据
		'''
		dim = np.ndim(self.data)
		if  dim == 3:
			self.data = [sample.flatten() for sample in self.data]
		elif dim == 4:
			self.data = [[sample.flatten() for sample in batch] for batch in self.data]
		else:
			raise ValueError('n_dim of data %d is not valid.' % dim)

	def roll_f_as_last(self):
		'''
		将频率维度后置
		'''
		dim = np.ndim(self.data)
		if  dim == 3:
			self.data = np.rollaxis(np.array(self.data), 1, 3)
		elif dim == 4:
			self.data = np.rollaxis(np.array(self.data), 2, 4)
		else:
			raise ValueError('n_dim of data %d is not valid.' % dim)


def _subsampling(ftr, offset, duration, window, stride):
	'''
	ftr data -> list of units

	对单个ftr数据进行子采样，得到一系列子样本单元

	:param ftr: 从单个 .ftr 文件读到的数据, shape like (n_mfcc, n_frame)
	:param offset: 偏移量，毫秒
	:param duration: 采样长度，毫秒
	:param window: 采样单元长度
	:param stride: 每次采样的步长
	:return: list of units, shape like (n_unit, n_mfcc, n_frame)
	'''
	if offset >= ftr.shape[-1]:
		raise ValueError('subsampling offset %d is greater than length of ftr %d.' % (offset, len(ftr)))
	units = []
	high = min(offset + duration, ftr.shape[-1])
	left = offset
	right = left + window
	while right <= high:
		units.append(ftr[:, left: right])
		left += stride
		right += stride
	return units


def _grouping(units, group_size):
	'''
	从单元列表得到组合列表，会忽略末尾凑不足group_size的单元
	可以不用这种表示方法

	:param units: list of units, shape like (n_unit, n_mfcc, n_frame)
	:param group_size: size of each group
	:return: list of groups, shape like (n_group, n_mfcc, n_frame) where n_group = n_unit // group_size
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
	return DataPack(data, [label for _ in data], [name for _ in data])


if __name__ == '__main__':
	from configs.subsampling_config import subsampling_config

	wkdirs = [
		# '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/zfs/trimmed',
		# '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/wj/trimmed',
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/wwn/trimmed',
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/wty/trimmed',
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/gfz/trimmed',
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/xy/trimmed',
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/yzc/trimmed',
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/0305_1/trimmed',
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/0305_2/trimmed',
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/cjr/trimmed',
	]
	pack = DataPack()
	pack.from_wav_dir(wkdirs, shuffle=False, cache=True)
	pack.show_shape()
	pack.apply_subsampling(shuffle=True)
	print('aftrer subsampling')
	print(pack.labels[:5], pack.names[:5])
	pack.show_shape()
	pass
