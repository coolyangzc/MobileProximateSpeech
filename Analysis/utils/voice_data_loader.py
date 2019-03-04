# load voice data from .ftr files

from utils.io import load_from_file
import os
import os.path as path
from collections import namedtuple
import random
import time
import numpy as np

DataPack = namedtuple('DataPack', 'data labels names')


def suffix_filter(files, suffix):
	'''
	return list of files with given suffix
	'''
	return filter(lambda x: x.endswith(suffix), files)


def show_shape(iterable):
	print(np.array(iterable).shape)


def __scan_dir(wkdir, label):
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
		ftrs.append(load_from_file(filename))
		names.append(filename)
	labels = [label for _ in ftrs]

	os.chdir(old_path)
	return DataPack(ftrs, labels, names)


def load_ftr_from_dir(wkdir, shuffle=True, random_seed=None):
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
	p_ftrs, p_labels, p_names = __scan_dir('Positive', 1)
	n_ftrs, n_labels, n_names = __scan_dir('Negative', 0)

	ftrs = p_ftrs + n_ftrs
	labels = p_labels + n_labels
	names = p_names + n_names

	if random_seed is None:
		random_seed = time.time()

	if shuffle:
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

	对单个.ftr文件进行子采样，得到一系列子样本单元

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


def apply_subsampling(ftrs, labels, names, offset, duration, window, stride):
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
	return DataPack(new_data, new_labels, new_names)


def apply_subsampling_grouping(ftrs, labels, names, offset, duration, window, stride, group_size):
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

	os.chdir('..')
	wkdir = 'Data/Sounds/yzc/'
	data_pack = load_ftr_from_dir(wkdir)

	data_pack = apply_subsampling_grouping(*data_pack, **subsampling_config, group_size=11)
	# data_pack = apply_subsampling(*data_pack, **subsampling_config)
	show_shape(data_pack.data)
	show_shape(data_pack.labels)
	show_shape(data_pack.names)

	train_pack, test_pack = train_test_split(*data_pack, test_size=0.1)
	# print(len(test_pack.names), len(train_pack.names))

	show_shape(test_pack.data)
	show_shape(train_pack.data)

	# show_shape(subsampling(test_pack.data[0], **subsampling_config))
	# show_shape(subsampling(test_pack.data[1], **subsampling_config))
	pass
