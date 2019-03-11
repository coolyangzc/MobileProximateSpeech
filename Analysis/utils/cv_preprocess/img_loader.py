import os
import random
import re
import time

import numpy as np
from PIL import Image
from tqdm import tqdm

from utils.tools import suffix_filter

label_dict = {  # 正负例分类字典, -1 表示舍弃这个特征的所有数据
	'竖直对脸，碰触鼻子': 1,
	'竖直对脸，不碰鼻子': 1,
	'竖屏握持，上端遮嘴': 1,
	'水平端起，倒话筒': 1,
	'话筒': 1,
	'横屏': 1,
}

description_pattern = re.compile('(\w+，?\w+) Study2', re.U)


def show_shape(iterable):
	try:
		print(np.array(iterable).shape)
	except ValueError:
		print('the shape is not standard, len = %d.' % len(iterable))


class ImagePack:
	'''
	Data structure for storing images, labels and descriptions
	'''

	def __init__(self, images=None, labels=None, names=None):
		self.images = images if images else []
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
		print('data: ', end='')
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

	def select_class(self, selected_label: int):
		'''
		select all samples with label
		:param selected_label: 0 or 1
		:return: a sub DataPack
		'''
		images, labels, names = [], [], []
		for image, label, name in zip(self.images, self.labels, self.names):
			if label == selected_label:
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

	def __add__(self, other):
		'''
		concatenate another ImagePack
		:param other:  ImagePack
		'''
		return ImagePack(self.images + other.images, self.labels + other.labels, self.names + other.names)

	def from_subject(self, subject_dir, shuffle=True, random_seed=None, progressbar=False):
		'''
		load from a subject's folder

		:param subject_dir: subject's directory, should include a 'trimmed' subdirectory and a 'original' directory
		:param shuffle: whether to shuffle
		:param random_seed: random seed for shuffling, if none, use time.time()
		:param progressbar: whether to display a progressbar
		:return: self
		'''
		old_path = os.getcwd()
		os.chdir(subject_dir)
		assert os.path.exists('original') and os.path.exists('trimmed')

		# list all image folders
		os.chdir('trimmed')
		folders = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))

		for folder in tqdm(folders) if progressbar else folders:
			# get the description and label
			# cwd: .../xxx/trimmed/
			txt_path = os.path.join('../original', folder) + '.txt'
			with open(txt_path, 'r') as f:
				line = f.readline()
			mt = description_pattern.match(line)
			try:
				name = mt.group(1)
			except AttributeError:
				print('Unidentified description in:')
				print(os.path.abspath(txt_path))
				print(line)
				name = None
				exit(1)
			label = label_dict[name]

			# load .jpg images
			os.chdir(folder)
			for img_name in suffix_filter(os.listdir('.'), suffix='.jpg'):
				img = Image.open(img_name)
				npimg = np.array(img)
				self.images.append(npimg)
				self.labels.append(label)
				self.names.append(name)
			os.chdir('..')

		if shuffle == True: self.shuffle_all(random_seed)

		os.chdir(old_path)
		return self


if __name__ == '__main__':
	subject_dir = '/Users/james/MobileProximateSpeech/Analysis/Data/Study2/subjects/zfs'
	imgset = ImagePack()
	imgset.from_subject(subject_dir, progressbar=True)
	print(imgset.labels[:3])
	print(imgset.names[:3])
	for img in imgset.images[:3]:
		show_shape(img)
