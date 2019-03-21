import os
import warnings

import numpy as np
import librosa

from utils.tools import date_time
import time

# 此代码需要先配置好 RNNoise 的环境，生成可执行文件，并把可执行文件的路径放在下面
SCRIPT_PATH = '/Users/james/Test/rnnoise-master/examples/rnnoise_demo'
OPTIMAL_SR = 48000


def reduce_noise_rnn(y: np.ndarray, sr: int = OPTIMAL_SR, res_type='none'):
	'''
	denoise using a trained rnn - see rnnoise

	:param y: mono wav time series data(pcm data), ndarray, float or int16
	:param sr: sample rate, should be exactly OPTIMAL_SR
	:param res_type: str, 'none': no resampling, 'kaiser_fast': fast resampling, 'kaiser_best': best resampling
	:return: y_clean, mono wav time series data(pcm data), ndarray, float32
	'''
	t0 = time.time()

	if y.dtype == 'float32':
		if res_type != 'none':
			y = librosa.resample(y, orig_sr=sr, target_sr=OPTIMAL_SR, res_type=res_type)
		y = (y * 32768.0).astype(np.int16, order='C')
	elif y.dtype == 'int16':
		if res_type != 'none':
			y = y.astype(np.float32, order='C') / 32768.0
			y = librosa.resample(y, orig_sr=sr, target_sr=OPTIMAL_SR, res_type=res_type)
			y = (y * 32768.0).astype(np.int16, order='C')
	else:
		raise TypeError('y.dtype %s is invalid.' % y.dtype)

	temp_path = '%s- temp.pcm' % date_time()
	clean_path = '%s- clean.pcm' % date_time()
	y.tofile(temp_path)

	# execute rnn noise reduction
	t1 = time.time()
	command = '%s  \'%s\'  \'%s\'' % (SCRIPT_PATH, temp_path, clean_path)
	os.system(command)
	t2 = time.time()

	with open(clean_path, 'rb') as f:
		y = np.fromfile(f, dtype=np.int16)
	y_clean = y.astype(dtype=np.float32, order='C') / 32768.0

	if res_type != 'none':
		y_clean = librosa.resample(y_clean, orig_sr=OPTIMAL_SR, target_sr=sr, res_type=res_type)

	os.remove(temp_path)
	os.remove(clean_path)
	print('execute time = %f s' % (t2 - t1))
	print('backend time = %f s' % (time.time() - t0))
	return y_clean
