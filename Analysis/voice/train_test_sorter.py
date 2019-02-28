# 将`.ftr`文件分离到子目录 /Train 和 /Test

import os
import os.path as path
import random
import shutil
from collections import namedtuple
from tqdm import tqdm as progress


def train_test_sort(wkdir, test_ratio, random_state=None):
	'''
	split train test and copy .ftr files to subordinates
	:param wkdir: working directory
	'''
	random.seed(random_state)
	old_path = os.getcwd()
	os.chdir(wkdir)
	if path.exists('Train'): os.rmdir('Train')
	if path.exists('Test'): os.rmdir('Test')
	assert path.exists('Positive')
	assert path.exists('Negative')

	Ftr = namedtuple('Ftr', 'filename label')
	data = []
	print('Scanning...')

	files = filter(lambda x: x.endswith('.ftr'), os.listdir('Positive'))
	data += [Ftr(path.join('./Positive', filename), '+') for filename in files]

	files = filter(lambda x: x.endswith('.ftr'), os.listdir('Negative'))
	data += [Ftr(path.join('./Negative', filename), '-') for filename in files]

	random.shuffle(data)

	os.mkdir('Train')
	os.mkdir('Train/Positive')
	os.mkdir('Train/Negative')
	os.mkdir('Test')
	os.mkdir('Test/Positive')
	os.mkdir('Test/Negative')

	print('Copying...')
	test_size = int(len(data) * test_ratio)
	for ftr in progress(data[:test_size]):
		shutil.copyfile(ftr.filename, './Test/%s/%s' %
						('Positive' if ftr.label == '+' else 'Negative', path.basename(ftr.filename)))

	for ftr in progress(data[test_size:]):
		shutil.copyfile(ftr.filename, './Train/%s/%s' %
						('Positive' if ftr.label == '+' else 'Negative', path.basename(ftr.filename)))

	os.chdir(old_path)
	print('Done.')


if __name__ == '__main__':
	os.chdir('..')
	wkdir = 'Data/Sounds/yzc'
	train_test_sort(wkdir, 0.1)
