import os
import random
import re
import shutil
import time

import numpy as np
from PIL import Image
from tqdm import tqdm

from utils import io
from utils.tools import suffix_filter

label_dict = {  # todo 分类字典, -1 表示舍弃这个特征的所有数据，0 表示负例
	'大千世界': 0,
	'易混淆': 0,
	'耳旁打电话': 0,
	'右耳打电话（不碰）': 0,
	'右耳打电话（碰触）': 0,
	'左耳打电话（不碰）': 0,
	'左耳打电话（碰触）': 0,
	'倒着拿手机': 0,
	'自拍': 0,
	'竖直对脸，碰触鼻子': 1,
	'竖直对脸，不碰鼻子': 2,
	'竖屏握持，上端遮嘴': 3,
	'水平端起，倒话筒': -1,
	'话筒': 4,
	'横屏': 5,
}
doc_dict = [  # todo 每一类对应的描述
	'负例',
	'竖直对脸，碰触鼻子',
	'竖直对脸，不碰鼻子',
	'竖屏握持，上端遮嘴',
	# '水平端起，倒话筒',
	'话筒',
	'横屏',
]
N_CLASS = len(doc_dict)

description_pattern = re.compile('(.*) Study2', re.U)


def show_shape(iterable):
	try:
		print(np.array(iterable).shape)
	except ValueError:
		print('the shape is not standard, len = %d.' % len(iterable))


def get_description(folder):
	'''
	get the description
	cwd: .../xxx/resized/

	:param folder: xxx/resized
	:return: description str
	'''
	txt_path = os.path.join('../original', folder) + '.txt'
	with open(txt_path, 'r', encoding='utf-8') as f:
		line = f.readline()
	mt = description_pattern.match(line)
	try:
		name = mt.group(1)
		return name
	except AttributeError:
		raise AttributeError('Unidentified description in: %s\n%s' % (os.path.abspath(txt_path), line))


class ImagePack:
	'''
	Data structure for storing images, labels and descriptions
	'''

	def __init__(self, images=None, labels=None, names=None):
		self.images = np.array(images) if images else []
		self.labels = labels if labels else []
		self.names = names if names else []

	def __iter__(self):
		self.n_var = 0
		return self

	def __next__(self):
		n_var = self.n_var
		self.n_var += 1
		if n_var == 0:
			return self.images
		elif n_var == 1:
			return self.labels
		elif n_var == 2:
			return self.names
		else:
			raise StopIteration

	def show_shape(self):
		print('images: ', end='')
		show_shape(self.images)
		print('labels: ', end='')
		show_shape(self.labels)
		print('names: ', end='')
		show_shape(self.names)

	def shuffle_all(self, random_seed=None):
		if random_seed is None: random_seed = time.time()
		random.seed(random_seed)
		random.shuffle(self.images)
		random.seed(random_seed)
		random.shuffle(self.labels)
		random.seed(random_seed)
		random.shuffle(self.names)

	def select_class(self, selected_label):
		'''
		select all samples with label
		:param selected_label: 0 or 1
		:return: a sub DataPack
		'''
		images, labels, names = [], [], []
		if isinstance(selected_label, int):
			for image, label, name in zip(self.images, self.labels, self.names):
				if label == selected_label:
					images.append(image)
					labels.append(label)
					names.append(name)
		elif isinstance(selected_label, list):
			for image, label, name in zip(self.images, self.labels, self.names):
				if label in selected_label:
					images.append(image)
					labels.append(label)
					names.append(name)
		return ImagePack(images, labels, names)

	def crop(self, size: int):
		'''
		crop the datapack to the designated size ( ≤ len(self.data) )
		'''
		assert size <= len(self.images)
		self.images = self.images[:size]
		self.labels = self.labels[:size]
		self.names = self.names[:size]
		return self

	def __add__(self, other):
		'''
		concatenate another ImagePack
		:param other:  ImagePack
		'''
		return ImagePack(list(self.images) + list(other.images), list(self.labels) + list(other.labels),
						 self.names + other.names)

	def __iadd__(self, other):
		self.images = list(self.images)
		self.images += list(other.images)
		self.labels = list(self.labels)
		self.labels += list(other.labels)
		self.names += other.names
		return self

	def __from_subject(self, subject_dir, shuffle=True, random_seed=None, progressbar=False, cache=True, reload=False):
		'''
		load from a subject's folder

		:param subject_dir: subject's directory, should include a 'resized' subdirectory and a 'original' directory
		:param shuffle: whether to shuffle
		:param random_seed: random seed for shuffling, if none, use time.time()
		:param progressbar: whether to display a progressbar
		:param cache: whether to cache images into static numpy arrays
		:param reload: whether to reload images regardless of if cache folder exists
		:return: self
		'''
		old_path = os.getcwd()
		os.chdir(subject_dir)
		if not (os.path.exists('original') and os.path.exists('resized')):
			raise FileNotFoundError('Error in %s', subject_dir)

		# list all image folders
		os.chdir('resized')
		folders = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))

		for folder in tqdm(folders) if progressbar else folders:
			# get the description and label
			# cwd: .../xxx/resized/
			try:
				name = get_description(folder)
			except FileNotFoundError as e:
				mp4files = suffix_filter(os.listdir(folder), '.mp4')
				if len(mp4files) > 0:
					raise e
				else:
					continue

			try:
				label = label_dict[name]
			except KeyError:
				raise KeyError('Unidentified description %s in %s, %s' % (name, folder, subject_dir))
			if label == -1: continue

			# load .jpg images
			os.chdir(folder)

			if reload == True or not os.path.exists('cache.npimgs'):  # never cached numpy arrays before
				images = []
				for img_name in suffix_filter(os.listdir('.'), suffix='.jpg'):
					try:
						img = Image.open(img_name)
					except OSError:
						print('cannot open %s in %s, %s' % (img_name, folder, subject_dir))
						continue
					npimg = np.array(img)
					images.append(npimg)
				if cache == True:
					io.save_to_file(images, 'cache.npimgs')
			else:  # cached before
				images = io.load_from_file('cache.npimgs')

			self.images += images
			for _ in images:
				self.labels.append(label)
				self.names.append(name)

			os.chdir('..')

		if shuffle == True: self.shuffle_all(random_seed)

		os.chdir(old_path)
		return self

	def from_subject(self, subject_dirs, shuffle=True, random_seed=None, progressbar=False, cache=True, reload=False):
		'''
		load from subjects' folder

		:param subject_dirs: subjects' directories or subject's directory,
			should include a 'resized' subdirectory and a 'original' directory
		:param shuffle: whether to shuffle
		:param random_seed: random seed for shuffling, if none, use time.time()
		:param progressbar: whether to display a progressbar
		:param cache: whether to cache images into static numpy arrays
		:param reload: whether to reload images regardless of if cache folder exists
		:return: self
		'''
		if not isinstance(subject_dirs, list): subject_dirs = [subject_dirs]
		for i, subject_dir in enumerate(subject_dirs):
			if progressbar: print('%d / %d, loading from %s...' % (i + 1, len(subject_dirs), subject_dir))
			self.__from_subject(subject_dir, shuffle=False, progressbar=progressbar, cache=cache, reload=reload)
			if progressbar: print()
		if shuffle: self.shuffle_all(random_seed)
		# self.images = np.array(self.images)
		return self

	def from_data_dir(self, data_dir, format='jpg', shuffle=True, random_seed=None):
		'''
		load from data directory (train/val/test)
		:param data_dir: directory including 0~N_CLASS-1 subdirectories
		:param format: format of images
		:return: self
		'''
		old_path = os.getcwd()
		os.chdir(data_dir)
		for c in tqdm(range(N_CLASS)):
			os.chdir(str(c))
			for file in suffix_filter(os.listdir('.'), suffix=format):
				img = Image.open(file)
				self.images.append(np.array(img))
				self.labels.append(c)
				self.names.append(doc_dict[c])
			os.chdir('..')
		if shuffle == True: self.shuffle_all(random_seed)
		os.chdir(old_path)
		return self

	def train_test_split(self, test_size=None):
		'''
		files or groups (DataPack) -> train_pack + test_pack

		:param test_size: test size ratio, float number
		:return: train_pack, test_pack
		'''
		if test_size is None:  # auto
			if len(self.images) < 5000:
				test_size = 0.3
			elif len(self.images) < 10000:
				test_size = 0.2
			elif len(self.images) < 50000:
				test_size = 0.1
			else:
				test_size = 0.05
		else:
			assert 0.0 <= test_size <= 1.0
		cut = int(len(self.images) * test_size)
		return ImagePack(list(self.images)[cut:], list(self.labels)[cut:], list(self.names)[cut:]), \
			   ImagePack(list(self.images)[:cut], list(self.labels)[:cut], list(self.names)[:cut])

	def save_to_dir(self, dst_dir, overwrite=False):
		'''
		sort images with different labels and store them in dst_dir's subdirectories

		:param dst_dir: target directory
		:param overwrite: whether to cover subdirs which already exist
		'''
		print('saving to %s...' % dst_dir)
		assert os.path.exists(dst_dir)
		old_path = os.getcwd()
		os.chdir(dst_dir)
		for c in range(N_CLASS):
			c = str(c)
			if os.path.exists(c):
				if overwrite == True:
					shutil.rmtree(c)
				else:
					raise FileExistsError('class directory %s already exists.' % c)
			os.mkdir(c)

		cnt = {}
		for c in range(N_CLASS): cnt[c] = 0

		for image, label in tqdm(zip(self.images, self.labels)):
			img = Image.fromarray(image)
			img.save(os.path.join(str(label), str(cnt[label]) + '.jpg'))
			cnt[label] += 1

		os.chdir(old_path)


def train_val_test_sorter(src_dir, dst_dir=None):
	'''
	以下将对 Study2 的所有图片进行归类，分为训练、开发、测试三堆，分别储存在 train, val, test 目录，注意测试集的正例是被 leave one out 得到的

	:param src_dir: 包含 subjects 和 negatives 两个子目录的文件夹
	:param dst_dir: 输出目标目录，内含 train, val, test 三个文件夹
	'''
	old_path = os.getcwd()
	os.chdir(src_dir)
	if dst_dir is None: dst_dir = src_dir
	train_val = ImagePack()
	test = ImagePack()

	# from subjects
	os.chdir('subjects')
	subject_dirs = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	train_val.from_subject(subject_dirs[:-1], progressbar=True, shuffle=False, reload=False)  # leave one out
	test.from_subject(subject_dirs[-1], progressbar=True, shuffle=True, reload=False)

	# from negatives
	os.chdir('../negatives')
	subject_dirs = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	neg = ImagePack()
	neg.from_subject(subject_dirs, progressbar=True, shuffle=False, reload=False)
	os.chdir(CWD)
	neg_train_val, neg_test = neg.train_test_split(test_size=0.1)

	train_val += neg_train_val
	test += neg_test
	train_val.shuffle_all()
	test.shuffle_all()
	train, val = train_val.train_test_split(test_size=0.2)

	print('train:')
	train.show_shape()
	print('\nval:')
	val.show_shape()
	print('\ntest:')
	test.show_shape()

	train.save_to_dir('train', overwrite=True)
	val.save_to_dir('val', overwrite=True)
	test.save_to_dir('test', overwrite=True)

	os.chdir(old_path)


if __name__ == '__main__':
	# 以下将对 Study2 的所有图片进行归类，分为训练、开发、测试三堆，分别储存在 train, val, test 目录，注意测试集的正例是被 leave one out 得到的
	CWD = '/Volumes/TOSHIBA EXT/Analysis/Data/Study2'
	os.chdir(CWD)
	# train_val_test_sorter('.')
	pack = ImagePack()
	os.chdir('negatives')
	subjects = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	pack.from_subject(subjects, shuffle=True, cache=False)
	pack.show_shape()
