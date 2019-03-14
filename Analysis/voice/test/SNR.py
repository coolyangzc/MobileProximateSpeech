import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
from utils.voice_preprocess.mfcc_data_loader import suffix_filter, label_dict
import os
from tqdm import tqdm


def snr(a, axis, ddof=0):
	a = np.asanyarray(np.abs(a))
	m = a.mean(axis)
	sd = a.std(axis=axis, ddof=ddof)
	return np.where(sd == 0, 0, m / sd)


def compare(file1, file2):
	y1, sr1 = librosa.load(file1)
	y2, sr2 = librosa.load(file2)

	plt.figure(0)
	plt.subplot(2, 1, 1)
	librosa.display.waveplot(y1, sr1)
	plt.title('close')

	plt.subplot(2, 1, 2)
	librosa.display.waveplot(y2, sr2)
	plt.title('pocket')
	plt.show()

	s1 = snr(y1, axis=0)
	s2 = snr(y2, axis=0)

	print('close snr')
	print(s1)

	print('distant snr')
	print(s2)
	print()

	return s1, s2


def search_for_gesture(filename):
	old_path = os.getcwd()
	os.chdir('../original')
	with open(filename + '.txt', 'r') as f:
		f.readline()
		gesture = f.readline().strip()
	os.chdir(old_path)
	return gesture


def snr_from_dir(dir):
	old_path = os.getcwd()
	os.chdir(dir)
	p, n = [], []
	folders = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	for folder in tqdm(folders):
		gesture = search_for_gesture(folder)
		label = label_dict[gesture]
		if label == -1: continue
		os.chdir(folder)
		files = suffix_filter(os.listdir('.'), '.wav')
		for file in files:
			y, sr = librosa.load(file)
			(p if label == 1 else n).append(snr(y, axis=0))
		os.chdir('..')
	os.chdir(old_path)
	return p, n


if __name__ == '__main__':
	CWD = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects'
	os.chdir(CWD)

	p, n = [], []
	subjects = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	subjects = list(map(lambda x: os.path.join(x, 'trimmed'), subjects))

	for subject in subjects:
		res = snr_from_dir(subject)
		p += res[0]
		n += res[1]

	plt.figure()
	plt.hist(p, bins=30, facecolor='red', edgecolor='black', label='close')
	plt.hist(n, bins=30, facecolor='blue', edgecolor='black', label='distant')
	plt.legend()
	plt.show()
	print('p', np.mean(p))
	print('n', np.mean(n))
