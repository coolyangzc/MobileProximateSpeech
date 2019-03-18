import numpy as np
import matplotlib.pyplot as plt
from utils.voice_preprocess.mfcc_data_loader import DataPack
import os
from tqdm import tqdm


if __name__ == '__main__':
	CWD = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/'
	os.chdir(CWD)

	pack = DataPack()
	pack.from_chunks_dir(['zfs/trimmed', 'wrl/trimmed', 'gfz/trimmed', 'mq/trimmed'], shuffle=True)
	pack.apply_subsampling(shuffle=True)
	pack.roll_f_as_last()
	pack.state.add('group')
	p, n = pack.select_class(1), pack.select_class(0)
	p._ungroup(extend_labels=True, extend_names=True)
	n._ungroup(extend_labels=True, extend_names=True)

	p.crop(10000)
	n.crop(10000)
	p.show_shape()
	n.show_shape()

	for dim in range(24):
		plt.figure()
		plt.hist(p.data[:, dim], bins=30, facecolor='red', edgecolor='black', alpha=0.7, label='close')
		plt.hist(n.data[:, dim], bins=30, facecolor='blue', edgecolor='black', alpha=0.7, label='distant')
		plt.legend()
		plt.title('Dim %s' % dim)
		plt.show()
