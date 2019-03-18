import numpy as np
import matplotlib.pyplot as plt
from utils.voice_preprocess.mfcc_data_loader import DataPack
import os
from tqdm import tqdm
import librosa

def subsample(a, stride):
	b = []
	for i, x in enumerate(a):
		if i % stride == 0:
			b.append(x)
	return b


if __name__ == '__main__':
	CWD = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/'
	os.chdir(CWD)
	subjects = filter(lambda x: os.path.isdir(x), os.listdir('.'))
	subjects = list(map(lambda x: os.path.join(x, 'trimmed'), subjects))[:5]

	pack = DataPack()
	pack.from_chunks_dir(subjects, shuffle=True, reload=False, cache=True)
	pack.apply_subsampling(shuffle=True)
	pack.show_shape()
	pack.roll_f_as_last()
	pack.state.add('group')
	p, n = pack.select_class(1), pack.select_class(0)
	p._ungroup(extend_labels=True, extend_names=True)
	n._ungroup(extend_labels=True, extend_names=True)

	# p.crop(10000)
	# n.crop(10000)
	p.show_shape()
	n.show_shape()

	p_mfcc = subsample(np.mean(librosa.amplitude_to_db(np.abs(p.data)), axis=0), 20)
	n_mfcc = subsample(np.mean(librosa.amplitude_to_db(np.abs(n.data)), axis=0), 20)
	p_0 = subsample(librosa.amplitude_to_db(np.abs(p.data[-1])), 20)
	n_0 = subsample(librosa.amplitude_to_db(np.abs(n.data[-1])), 20)

	plt.figure()
	width = 0.2
	x = np.arange(len(p_mfcc))
	plt.bar(x, p_mfcc, width=width, fc='red', label='close')
	plt.bar(x + width, n_mfcc, width=width, fc='blue', label='distant')
	plt.plot(x + 2 * width, p_0, color='red', label='one close')
	plt.plot(x + 3 * width, n_0, color='blue', label='one distant')
	plt.legend()
	plt.show()

