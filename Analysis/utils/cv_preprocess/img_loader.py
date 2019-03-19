import os
import random
import re
import shutil
import time
from collections import Counter

import numpy as np
from PIL import Image
from tqdm import tqdm

from utils import io
from utils.tools import suffix_filter, inverse_dict

label_dict = {  # todo 分类字典, 0 表示舍弃这个特征的所有数据，- 表示负例
	'大千世界': -1,
	'易混淆': -2,
	'耳旁打电话': -3,
	'右耳打电话（不碰）': -4,
	'右耳打电话（碰触）': -5,
	'左耳打电话（不碰）': -6,
	'左耳打电话（碰触）': -7,
	'倒着拿手机': -8,
	'自拍': -9,

	'竖直对脸，碰触鼻子': +1,
	'竖直对脸，不碰鼻子': +2,
	'竖屏握持，上端遮嘴': +3,
	'水平端起，倒话筒': +4,
	'话筒': +5,
	'横屏': +6,
}
doc_dict = inverse_dict(label_dict)  # 每一类对应的描述
try:
	del doc_dict[0]
except:
	pass
CLASSES = label_dict.values()
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
		desc = mt.group(1)
		return desc
	except AttributeError:
		raise AttributeError('Unidentified description in: %s\n%s' % (os.path.abspath(txt_path), line))


class ImagePack:
	'''
	Data structure for storing images, labels and names
	'''

	def __init__(self, images=None, labels=None, names=None, subjects=None):
		self.images = np.array(images) if images else []
		self.labels = labels if labels else []
		self.names = names if names else []
		self.subjects = subjects if subjects else []

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
		elif n_var == 3:
			return self.subjects
		else:
			raise StopIteration

	def show_shape(self):
		print('images: ', end='')
		show_shape(self.images)
		print('labels: ', end='')
		show_shape(self.labels)
		print('names: ', end='')
		show_shape(self.names)
		print('subjects: ', end='')
		show_shape(self.subjects)

	def shuffle_all(self, random_seed=None):
		if random_seed is None: random_seed = time.time()
		random.seed(random_seed)
		random.shuffle(self.images)
		random.seed(random_seed)
		random.shuffle(self.labels)
		random.seed(random_seed)
		random.shuffle(self.names)
		random.seed(random_seed)
		random.shuffle(self.subjects)

	def select_class(self, selected_label):
		'''
		select all samples with label
		:param selected_label: class label
		:return: a sub DataPack
		'''
		images, labels, names, subjects = [], [], [], []
		if isinstance(selected_label, int):
			for image, label, name, subject in zip(self.images, self.labels, self.names, self.subjects):
				if label == selected_label:
					images.append(image)
					labels.append(label)
					names.append(name)
					subjects.append(subject)
		elif isinstance(selected_label, list):
			for image, label, name, subject in zip(self.images, self.labels, self.names, self.subjects):
				if label in selected_label:
					images.append(image)
					labels.append(label)
					names.append(name)
					subjects.append(subject)

		return ImagePack(images, labels, names, subjects)

	def crop(self, size: int):
		'''
		crop the datapack to the designated size ( ≤ len(self.data) else all )
		'''
		self.images = self.images[:size]
		self.labels = self.labels[:size]
		self.names = self.names[:size]
		self.subjects = self.subjects[:size]
		return self

	def __add__(self, other):
		'''
		concatenate another ImagePack
		:param other:  ImagePack
		'''
		return ImagePack(list(self.images) + list(other.images), list(self.labels) + list(other.labels),
						 self.names + other.names, self.subjects + other.subjects)

	def __iadd__(self, other):
		self.images = list(self.images)
		self.images += list(other.images)
		self.labels = list(self.labels)
		self.labels += list(other.labels)
		self.names += other.names
		self.subjects += other.subjects
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
			raise FileNotFoundError('folder original/ or resized/ not found in %s', subject_dir)

		# list all image folders
		os.chdir('resized')
		folders = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))

		for folder in tqdm(folders) if progressbar else folders:
			# get the description and label
			# cwd: .../xxx/resized/
			try:
				desc = get_description(folder)
			except FileNotFoundError as e:
				mp4files = suffix_filter(os.listdir(folder), '.mp4')
				if len(mp4files) > 0:
					raise e
				else:
					continue

			try:
				label = label_dict[desc]
			except KeyError:
				raise KeyError('Unidentified description %s in %s, %s' % (desc, folder, subject_dir))
			if label == 0: continue

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
				self.names.append(folder)  # keep track of image name
				self.subjects.append(os.path.basename(subject_dir))

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
		for c in tqdm(CLASSES):
			os.chdir(str(c))
			for file in suffix_filter(os.listdir('.'), suffix=format):
				img = Image.open(file)
				self.images.append(np.array(img))
				self.labels.append(c)
				self.names.append(file.split('.')[0])
				self.subjects.append('')  # unknown
			os.chdir('..')
		if shuffle == True: self.shuffle_all(random_seed)
		os.chdir(old_path)
		return self

	def train_val_split(self, val_size=None):
		'''
		files or groups (DataPack) -> train_pack + val_pack

		:param val_size: test size ratio, float number
		:return: train_pack, test_pack
		'''
		if val_size is None:  # auto
			if len(self.images) < 5000:
				val_size = 0.3
			elif len(self.images) < 10000:
				val_size = 0.2
			elif len(self.images) < 50000:
				val_size = 0.1
			else:
				val_size = 0.05
		else:
			if not 0.0 <= val_size <= 1.0:
				raise ValueError('val_size %f is invalid.' % val_size)
		cut = int(len(self.images) * val_size)
		return ImagePack(list(self.images)[cut:], list(self.labels)[cut:], self.names[cut:], self.subjects[cut:]), \
			   ImagePack(list(self.images)[:cut], list(self.labels)[:cut], self.names[:cut], self.subjects[:cut])

	def save_to_dir(self, src_dir, dst_dir):
		'''
		sort images with different labels and store them in dst_dir's subdirectories
		it will supplement the dst_dir unless files with the same name exist, that way, will be overwritten.
		todo, dir tree like: dst_dir / class_number / subject / jpg, mp4, txt

		:param src_dir: source directory to look for stores subjects' original files, should include 'cjr', 'hsd' ...
		:param dst_dir: target directory
		'''
		if not os.path.exists(dst_dir):
			os.mkdir(dst_dir)
		# prepare for class directories
		for c in CLASSES:
			if c == 0: continue
			class_dir = os.path.join(dst_dir, str(c))
			if not os.path.exists(class_dir):
				os.mkdir(class_dir)

		# sort all pack data to class directories
		subject_counter = Counter()
		for image, label, name, subject in tqdm(zip(self.images, self.labels, self.names, self.subjects)):
			img = Image.fromarray(image)
			trg_dir = os.path.join(dst_dir, str(label), subject)
			if not os.path.exists(trg_dir):
				os.mkdir(trg_dir)

			# save img
			trg_path = os.path.join(trg_dir, name)
			img_path = trg_path + ' - %d.jpg' % subject_counter[subject]
			subject_counter.update([subject])
			img.save(img_path)

			# copy mp4 and txt from src_dir to dst_dir
			src_path = os.path.join(src_dir, subject, 'original', name)

			mp4_path = trg_path + '.mp4'
			if not os.path.exists(mp4_path): # only copy once
				shutil.copyfile(src_path + '.mp4', mp4_path)  # possible to raise FileNotFoundError

			txt_path = trg_path + '.txt'
			if not os.path.exists(txt_path): # only copy once
				shutil.copyfile(src_path + '.txt', trg_path + '.txt')  # possible to raise FileNotFoundError


	def clear(self):
		del self.images, self.labels, self.names


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
	os.chdir('..')
	neg_train_val, neg_test = neg.train_val_split(val_size=0.1)

	train_val += neg_train_val
	test += neg_test
	train_val.shuffle_all()
	test.shuffle_all()
	train, val = train_val.train_val_split(val_size=0.2)

	print('train:')
	train.show_shape()
	print('\nval:')
	val.show_shape()
	print('\ntest:')
	test.show_shape()

	os.chdir(dst_dir)
	for which in 'train', 'val', 'test':
		if not os.path.exists(which):
			os.mkdir(which)
	# train.save_to_dir('train', overwrite=True)
	# val.save_to_dir('val', overwrite=True)
	# test.save_to_dir('test', overwrite=True)

	os.chdir(old_path)


if __name__ == '__main__':
	# 以下将对 Study2 的所有图片进行归类，分为训练、开发、测试三堆，分别储存在 train, val, test 目录，注意测试集的正例是被 leave one out 得到的
	# CWD = '/Volumes/TOSHIBA EXT/Analysis/Data/Study2'
	# train_val_test_sorter(CWD)
	cwd = '/Users/james/MobileProximateSpeech/Analysis/Data/Study2/subjects'
	os.chdir(cwd)
	imgpack = ImagePack()
	imgpack.from_subject(['hsd', 'cjr'], cache=True)
	imgpack.save_to_dir(src_dir='.', dst_dir='../classes')
# pack = ImagePack()
# os.chdir('subjects')
# subjects = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
# pack.from_subject(subjects, progressbar=True, shuffle=True, cache=True, reload=False)
# pack.show_shape()
