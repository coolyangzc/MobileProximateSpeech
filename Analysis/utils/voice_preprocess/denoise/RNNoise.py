import os
import warnings

import numpy as np

from utils.tools import date_time
import time

# 此代码需要先配置好 RNNoise 的环境，生成可执行文件，并把可执行文件的路径放在下面
SCRIPT_PATH = '/Users/james/Test/rnnoise-master/examples/rnnoise_demo'


def reduce_noise_rnn(y, sr=48000):
	'''
	denoise using a trained rnn - see rnnoise

	:param y: mono wav time series data(pcm data), np.float32
	:param sr: sample rate, should be exactly 48000
	:return: y_clean, mono wav time series data(pcm data), np.float32
	'''
	t0 = time.time()
	if sr != 48000:
		warnings.warn('RNNoise performs best at sr = 48000Hz, got %dHz instead.' % sr)

	y = np.array(y, dtype=np.float32) * 32768.0
	data = y.astype(np.int16, order='C')

	temp_path = '%s- temp.pcm' % date_time()
	clean_path = '%s- clean.pcm' % date_time()
	data.tofile(temp_path)

	# execute rnn noise reduction
	t1 = time.time()
	command = '%s  \'%s\'  \'%s\'' % (SCRIPT_PATH, temp_path, clean_path)
	os.system(command)
	t2 = time.time()

	with open(clean_path, 'rb') as f:
		data = np.fromfile(f, dtype=np.int16)
	y_clean = data.astype(np.float32, order='C') / 32768.0

	os.remove(temp_path)
	os.remove(clean_path)
	print('exec time = %f s' % (t2 - t1))
	print('call time = %f s\n' % (time.time() - t2 + t1 - t0))
	return y_clean
