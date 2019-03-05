# load voice mfcc data from .ftr files

from utils import io
from utils.voice_preprocess import mfcc
from utils.tools import suffix_conv
import os
import os.path as path
from collections import namedtuple
import random
import time
import numpy as np

DataPack = namedtuple('DataPack', 'data labels names')

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
	print(np.array(iterable).shape)


def __scan_pn_dir(wkdir, label):
	'''
	scan .ftr files in file_dir and return (data, labels, names)
	labels are copies of label (1: positive, 0: negative)
	'''
	assert label == 1 or label == 0
	old_path = os.getcwd()
	os.chdir(wkdir)

	ftrs, names = [], []
	files = suffix_filter(os.listdir('.'), '.ftr')
	for filename in files:
		ftrs.append(io.load_from_file(filename))
		names.append(filename)
	labels = [label for _ in ftrs]

	os.chdir(old_path)
	return DataPack(ftrs, labels, names)


def __load_sequential(func: callable, wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False):
	if type(wkdir) == str:
		return func(wkdir, txtdir, shuffle, random_seed, cache)
	elif type(wkdir) == list:
		if txtdir == None: txtdir = [None for _ in wkdir]

		ftrs, labels, descriptions = [], [], []
		for wkdir_, txtdir_ in zip(wkdir, txtdir):
			pack = func(wkdir_, txtdir_, shuffle=False, cache=cache)  # shuffle at last
			# concatenate
			ftrs += pack.data
			labels += pack.labels
			descriptions += pack.names

		if shuffle == True:
			if random_seed is None: random_seed = time.time()
			for obj in ftrs, labels, descriptions:
				random.seed(random_seed)
				random.shuffle(obj)

		return DataPack(ftrs, labels, descriptions)
	else:
		raise TypeError('type of wkdir which equals %s is neither str nor list.' % type(wkdir))


def __load_ftr_from_wav_dir(wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False):
	'''
	dir -> ftr DataPack

	:param wkdir: has lots of wav files, named with date_time
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

	cached = True if path.exists('.ftrexist') else False  # cached
	files = suffix_filter(os.listdir('.'), '.ftr' if cached else '.wav')

	for file_name in files:
		ftr = io.load_from_file(file_name) if cached else mfcc.get_mfcc(file_name)
		if cache == True and cached == False:
			io.save_to_file(ftr, suffix_conv(file_name, '.ftr'))

		txt_path = path.join(txtdir, suffix_conv(file_name, '.txt'))
		with open(txt_path, 'r') as f:
			f.readline()
			description = f.readline().strip()
		label = label_dict[description]

		ftrs.append(ftr)
		labels.append(label)
		descriptions.append(description)

	if shuffle == True:
		if random_seed is None: random_seed = time.time()
		for obj in ftrs, labels, descriptions:
			random.seed(random_seed)
			random.shuffle(obj)

	if cache == True:
		with open('.ftrexist', 'w'): pass # a mark

	os.chdir(old_path)
	return DataPack(ftrs, labels, descriptions)


def load_ftr_from_wav_dir(wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False):
	''' entrance
	dir or dirs -> ftr DataPack

	:param wkdir: str or list, has lots of wav files, named with date_time
	:param txtdir: str or list, .txt files directory, default: list of wkdir.parent.original
	:param shuffle: whether to shuffle
	:param random_seed: random seed
	:param cache: whether to store ftr data as cache to expedite future loading
	:return: DataPack of ftrs, labels, descriptions
	'''
	return __load_sequential(__load_ftr_from_wav_dir, wkdir, txtdir, shuffle, random_seed, cache)


def __load_ftr_from_chunks_dir(wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False):
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
	wk_cached = True if path.exists('.ftrexist') else False  # wkdir cached

	chunk_dirs = filter(lambda x: path.isdir(x), os.listdir('.'))
	for chunk_dir in chunk_dirs:

		txt_path = path.join(txtdir, chunk_dir + '.txt')
		with open(txt_path, 'r') as f:
			f.readline()
			description = f.readline().strip()
		label = label_dict[description]

		cached = True if path.exists(path.join(chunk_dir, '.ftrexist')) else False
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
					with open(path.join(chunk_dir, '.ftrexist'), 'w'): pass # a mark
				ftrs.append(ftr)
				labels.append(label)
				descriptions.append(description)

	if shuffle == True:
		if random_seed is None: random_seed = time.time()
		for obj in ftrs, labels, descriptions:
			random.seed(random_seed)
			random.shuffle(obj)

	if cache == True:
		with open('.ftrexist', 'w'): pass # a mark

	os.chdir(old_path)
	return DataPack(ftrs, labels, descriptions)


def load_ftr_from_chunks_dir(wkdir, txtdir=None, shuffle=True, random_seed=None, cache=False):
	'''
	dir(s) -> ftr DataPack

	:param wkdir: str or list, has lots of chunk directories, named with date_time
	:param txtdir: str or list, .txt files directory, default: wkdir.parent.original
	:param shuffle: whether to shuffle
	:param random_seed: random seed
	:param cache: whether to store ftr data as cache to expedite future loading
	:return: DataPack of ftrs, labels, descriptions
	'''
	return __load_sequential(__load_ftr_from_chunks_dir, wkdir, txtdir, shuffle, random_seed, cache)


def load_ftr_from_pn_dir(wkdir, shuffle=True, random_seed=None):
	'''
	dir -> ftr data (DataPack)

    wkdir has '/Positive/' and '/Negative/' directory
    return ftrs, labels and descriptions
    '''
	old_path = os.getcwd()
	os.chdir(wkdir)
	assert path.exists('Positive')
	assert path.exists('Negative')

	print('loading from %s...' % wkdir)
	p_ftrs, p_labels, p_names = __scan_pn_dir('Positive', 1)
	n_ftrs, n_labels, n_names = __scan_pn_dir('Negative', 0)

	ftrs = p_ftrs + n_ftrs
	labels = p_labels + n_labels
	names = p_names + n_names

	if shuffle == True:
		if random_seed is None: random_seed = time.time()
		for obj in ftrs, labels, names:
			random.seed(random_seed)
			random.shuffle(obj)
		print('shuffled.')

	print('loaded.')
	os.chdir(old_path)
	return DataPack(ftrs, labels, names)


def subsampling(ftr, offset, duration, window, stride):
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
	units = []
	high = offset + duration
	left = offset
	right = left + window
	while right <= high:
		units.append(ftr[:, left: right])
		left += stride
		right += stride
	return units


def grouping(units, group_size):
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


def extend_labels_names(data, label, name):
	'''
	.ftr 数据经过 subsampling 或者 grouping 处理后会变成多份，此函数可以将 label, name 也补齐

	:param data: a list of units or groups generated from one .ftr data
	:return: DataPack of (data, labels, names)
	'''
	return DataPack(data, [label for _ in data], [name for _ in data])


def apply_subsampling(ftrs, labels, names, offset, duration, window, stride, shuffle=False, random_seed=None):
	'''
	对 DataPack 施用采样，并保持labels，names长度平齐

	:return: new DataPack after conversion
	'''
	new_data = []
	new_labels = []
	new_names = []
	for ftr, label, name in zip(ftrs, labels, names):
		new_elem = subsampling(ftr, offset, duration, window, stride)
		new_data += new_elem
		extended = extend_labels_names(new_elem, label, name)
		new_labels += extended.labels
		new_names += extended.names

	if shuffle == True:
		if random_seed is None: random_seed = time.time()
		for obj in new_data, new_labels, new_names:
			random.seed(random_seed)
			random.shuffle(obj)

	return DataPack(new_data, new_labels, new_names)


def apply_subsampling_grouping(ftrs, labels, names, offset, duration, window, stride, group_size, shuffle=False,
							   random_seed=None):
	'''
	对 DataPack 施用子采样和重组，并保持labels，names长度平齐

	:return: new DataPack after conversion
	'''
	new_data = []
	new_labels = []
	new_names = []
	for ftr, label, name in zip(ftrs, labels, names):
		units = subsampling(ftr, offset, duration, window, stride)
		groups = grouping(units, group_size)
		new_data += groups
		extended = extend_labels_names(groups, label, name)
		new_labels += extended.labels
		new_names += extended.names

	if shuffle == True:
		if random_seed is None: random_seed = time.time()
		for obj in new_data, new_labels, new_names:
			random.seed(random_seed)
			random.shuffle(obj)

	return DataPack(new_data, new_labels, new_names)


def train_test_split(data, labels, names, test_size):
	'''
	files or groups (DataPack) -> train_pack + test_pack

	:param test_size: test size ratio, float number
	:return: train_pack, test_pack
	'''
	assert 0.0 <= test_size <= 1.0
	cut = int(len(data) * test_size)
	return DataPack(data[cut:], labels[cut:], names[cut:]), \
		   DataPack(data[:cut], labels[:cut], names[:cut])


if __name__ == '__main__':
	from configs.subsampling_config import subsampling_config

	#
	# os.chdir('..')
	# wkdir = 'Data/Sounds/yzc/'
	# data_pack = load_ftr_from_pn_dir(wkdir)
	#
	# data_pack = apply_subsampling_grouping(*data_pack, **subsampling_config, group_size=11)
	# # data_pack = apply_subsampling(*data_pack, **subsampling_config)
	# show_shape(data_pack.data)
	# show_shape(data_pack.labels)
	# show_shape(data_pack.names)
	#
	# train_pack, test_pack = train_test_split(*data_pack, test_size=0.1)
	# # print(len(test_pack.names), len(train_pack.names))
	#
	# show_shape(test_pack.data)
	# show_shape(train_pack.data)
	#
	# # show_shape(subsampling(test_pack.data[0], **subsampling_config))
	# # show_shape(subsampling(test_pack.data[1], **subsampling_config))
	wkdirs = [
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/xy/trimmed',
		# '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/gfz/trimmed',
		# '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/wty/trimmed'
	]
	# wkdir2 = '/Users/james/MobileProximateSpeech/Analysis/Data/Sounds/yzc'
	pack = load_ftr_from_wav_dir(wkdirs, shuffle=True, random_seed=1, cache=True)
	# pack = load_ftr_from_pn_dir(wkdir2)
	pack = apply_subsampling(*pack, **subsampling_config, shuffle=True)
	print('loaded.')
	print(len(pack.data))
	print(len(pack.labels))
	print(len(pack.names))
	pack = apply_subsampling(*pack, **subsampling_config, shuffle=True)
	print('applied.')
	show_shape(pack.data)
	print(len(pack.labels))
	print(len(pack.names))
	pass
