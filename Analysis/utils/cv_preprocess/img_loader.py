import os
import random
import shutil
import time
from collections import Counter

import numpy as np
from PIL import Image
from tqdm import tqdm

from utils import io
from utils.tools import suffix_filter
from configs import cv_config as config

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
	mt = config.description_pattern.match(line)
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

		for folder in tqdm(folders, desc='loading from subfolders', leave=False) if progressbar else folders:
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
				label = config.label_dict[desc]
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
		load from all image data in the directory (train/val/test)
		:param data_dir: directory including images or subdirectories including images
		:param format: format of images
		:return: self
		'''
		for dir_path, sub_dirs, file_names in os.walk(data_dir):
			image_names = suffix_filter(file_names, suffix=format)
			if len(image_names) == 0: continue
			try:
				label = int(os.path.split(dir_path)[-1])
			except ValueError as e:
				print(e, os.path.abspath(dir_path))
				continue
			for image_name in tqdm(image_names, desc='loading', leave=False):
				image_path = os.path.join(dir_path, image_name)
				img = Image.open(image_path)
				npimg = np.array(img)
				self.images.append(npimg)
				self.labels.append(label)
				self.names.append(image_name)

		if shuffle: self.shuffle_all(random_seed)
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

	def __sort_to_class_dirs(self, dst_dir, binary=False):
		'''
		sort images with different labels and store them in dst_dir's subdirectories
		todo, dir tree like: dst_dir / class_number / jpg   if binary==False
		todo or dst_dir / '1' or '0' / p_class_number or n_class_number   if binary==True

		:param dst_dir: target directory
		'''
		if not os.path.exists(dst_dir):
			os.mkdir(dst_dir)
		old_path = os.getcwd()
		os.chdir(dst_dir)
		if not os.path.exists('0'):
			os.mkdir('0')
		if not os.path.exists('1'):
			os.mkdir('1')
		for c in config.CLASSES:
			if c == 0: continue # filter out 0
			if c > 0:
				os.chdir('1')
			else:
				os.chdir('0')
			c = str(c)
			if not os.path.exists(c):
				os.mkdir(c)
			os.chdir('../')

		name_counter = Counter()
		progress = tqdm(total=len(self.names), desc='saving', leave=False)
		for image, label, name in zip(self.images, self.labels, self.names):
			progress.update()
			img = Image.fromarray(image)
			save_path = os.path.join('1' if label > 0 else '0', str(label), name + ' - %d.jpg' % name_counter[name])
			img.save(save_path)
			name_counter.update([name])

		os.chdir(old_path)

	def __sort_to_class_subject_dirs(self, src_dir, dst_dir):
		'''
		sort images with different labels, subjects and store them in dst_dir's sub-sub-directories
		it will supplement the dst_dir unless files with the same name exist, that way, will be overwritten.
		todo, dir tree like: dst_dir / class_number / subject / jpg, mp4, txt

		:param src_dir: source directory to look for stores subjects' original files, should include 'cjr', 'hsd' ...
		:param dst_dir: target directory
		'''
		if not os.path.exists(dst_dir):
			os.mkdir(dst_dir)
		# prepare for class directories
		for c in config.CLASSES:
			if c == 0: continue
			class_dir = os.path.join(dst_dir, str(c))
			if not os.path.exists(class_dir):
				os.mkdir(class_dir)

		# sort all pack data to class directories
		name_counter = Counter()
		progress = tqdm(total=len(self.names), desc='saving', leave=False)
		for image, label, name, subject in zip(self.images, self.labels, self.names, self.subjects):
			progress.update()
			img = Image.fromarray(image)
			trg_dir = os.path.join(dst_dir, str(label), subject)
			if not os.path.exists(trg_dir):
				os.mkdir(trg_dir)

			# save img
			trg_path = os.path.join(trg_dir, name)
			img_path = trg_path + ' - %d.jpg' % name_counter[name]
			name_counter.update([name])
			img.save(img_path)

			# copy mp4 and txt from src_dir to dst_dir
			src_path = os.path.join(src_dir, subject, 'original', name)

			mp4_path = trg_path + '.mp4'
			if not os.path.exists(mp4_path):  # only copy once
				try:
					shutil.copyfile(src_path + '.mp4', mp4_path)
				except FileNotFoundError:
					pass

			txt_path = trg_path + '.txt'
			if not os.path.exists(txt_path):  # only copy once
				try:
					shutil.copyfile(src_path + '.txt', trg_path + '.txt')
				except FileNotFoundError:
					pass

	def sort_to_dir(self, dst_dir, mode: str = 'class', src_dir=None, binary=False):
		'''
		sort images with different labels, subjects and store them in dst_dir's sub-sub-directories
		it will supplement the dst_dir unless files with the same name exist, that way, will be overwritten.
		todo, dir tree like:   dst_dir / class_number / subject / jpg, mp4, txt (mode == 'class subject')
		todo,       or like:   dst_dir / class_number / jpg (mode == 'class')

		:param dst_dir: target directory
		:param mode: either 'class' or 'class subject'
		:param src_dir: source directory to look for stores subjects' original files, should include 'cjr', 'hsd' ...
			(only needed when mode == 'class subject')
		:param binary: create a '1' and a '0' folder to restore all positive and negative images
		'''
		if mode == 'class':
			self.__sort_to_class_dirs(dst_dir=dst_dir, binary=binary)
		elif mode == 'class subject':
			if src_dir is None:
				raise AttributeError('You must specify `src_dst` if mode == \'class subject\'.')
			elif not os.path.exists(src_dir):
				raise FileNotFoundError('`src_dir` %s not found.' % os.path.abspath(src_dir))
			self.__sort_to_class_subject_dirs(src_dir=src_dir, dst_dir=dst_dir)
		else:
			raise ValueError('Got unidentified `mode` value: %s' % mode)

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
	train.sort_to_dir('train', mode='class')
	val.sort_to_dir('val', mode='class')
	test.sort_to_dir('test', mode='class')

	os.chdir(old_path)


if __name__ == '__main__':
	from utils.tools import dir_filter
	os.chdir(config.data_source)

	os.chdir('fixed subjects/')
	subjects = dir_filter(os.listdir('./'))
	tester = random.choice(subjects)
	subjects.remove(tester)
	positives, negatives, train, val, test = ImagePack(), ImagePack(), ImagePack(), ImagePack(), ImagePack()

	positives.from_subject(subjects, shuffle=True, progressbar=True).crop(2000)
	train_pos, val_pos = positives.train_val_split(val_size=0.2)
	train += train_pos
	val += val_pos
	test.from_subject(tester, progressbar=True)

	os.chdir('../negatives')

	negatives.from_subject(['zfs_confusing', 'zfs_confusing_iphone'], progressbar=True, shuffle=True)
	train_val_neg, test_neg = negatives.train_val_split(val_size=0.3)
	train_neg, val_neg = train_val_neg.train_val_split(val_size=0.2)

	train += train_neg
	val += val_neg
	test += test_neg

	# train_neg.show_shape()
	# train_pos.show_shape()
	# train.show_shape()
	# val.show_shape()
	# test.show_shape()

	train.sort_to_dir(os.path.join(config.data_directory, 'train/'), binary=True)
	val.sort_to_dir(os.path.join(config.data_directory, 'val/'), binary=True)
	test.sort_to_dir(os.path.join(config.data_directory, 'test/'), binary=True)

# pack = ImagePack()
# os.chdir('subjects')
# subjects = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
# pack.from_subject(subjects, progressbar=True, shuffle=True, cache=True, reload=False)
# pack.show_shape()
