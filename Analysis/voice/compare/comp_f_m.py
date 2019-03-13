from utils.voice_preprocess.mfcc_data_loader import DataPack
from matplotlib import pyplot as plt
import numpy as np
import os
import random
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise_distances


def load_data(subjects):
	if not isinstance(subjects, list): subjects = [subjects]
	dirs = list(map(lambda x: os.path.join('Data/Study3/subjects', x, 'trimmed'), subjects))
	dataset = DataPack()
	dataset.from_chunks_dir(dirs)
	dataset.apply_subsampling()
	# dataset.to_flatten()
	dataset.crop(1000)
	dataset.roll_f_as_last()
	dataset.state.add('group')
	dataset._ungroup()
	# dataset.data = list(dataset.data)
	return dataset

def draw_which(dataset: DataPack, dim1, dim2, color, label=None):
	plt.scatter(dataset.data[:, dim1], dataset.data[:, dim2], c=color, s=1, alpha=0.2, label=label)
	plt.xlabel(dim1)
	plt.ylabel(dim2)

def compute_separability(X, Y):
	return np.mean(pairwise_distances(X, Y, n_jobs=2))

if __name__ == '__main__':
	CWD = '/Users/james/MobileProximateSpeech/Analysis'
	os.chdir(CWD)

	females = ['lgh', 'gfz', 'jwy', 'mq', 'wrl']
	males = ['wwn', 'wj', 'wty', 'wzq', 'yzc', 'xy', 'gyz', 'cjr', 'zfs']

	random.shuffle(females)
	random.shuffle(males)

	# f, m = load_data(females[:4]), load_data(males[:4])
	# pca = PCA(n_components=2)
	# pca.fit((f + m).data)
	# f.data = pca.transform(f.data)
	# m.data = pca.transform(m.data)

	# print('\nfemales:')
	# f.show_shape()
	# print('\nmales:')
	# m.show_shape()

	# print()
	# print('dist between f and f: ', compute_separability(f.data, f.data), '\n')
	# print('dist between f and m: ', compute_separability(f.data, m.data), '\n')
	# print('dist between m and m: ', compute_separability(m.data, m.data), '\n')

	f, m = [], []
	for female in females:
		f.append(load_data(female))
	for male in males:
		m.append(load_data(male))

	dim1, dim2 = 22, 23
	draw_which(f[0], dim1, dim2, 'red', 'female 1')
	draw_which(f[1], dim1, dim2, 'magenta', 'female 2')
	draw_which(f[2], dim1, dim2, 'orange', 'female 3')
	plt.legend()
	plt.show()

	draw_which(m[0], dim1, dim2, 'blue', 'male 1')
	draw_which(m[1], dim1, dim2, 'cyan', 'male 2')
	draw_which(m[2], dim1, dim2, 'navy', 'male 3')
	plt.legend()
	plt.show()
