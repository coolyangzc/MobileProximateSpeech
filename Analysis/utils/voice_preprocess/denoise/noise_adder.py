import os
import time

import librosa
import numpy as np


def white_noised_from_path(audio_path, sr=16000, mode='mono', ratio=0.1, out_path=None):
	if mode == 'mono':
		y, sr = librosa.load(audio_path, sr=sr, mono=True)
		y = white_noised(y, ratio)
	elif mode == 'stereo':
		y, sr = librosa.load(audio_path, sr=sr, mono=False)
		y[0] = white_noised(y[0], ratio)
		y[1] = white_noised(y[1], ratio)
	else:
		raise ValueError('mode %s is invalid.' % mode)

	if out_path: librosa.output.write_wav(out_path, y, sr, norm=True)
	return y, sr


def superpose_from_path(audio_path1, audio_path2, sr=16000, mode='mono', ratio=0.1, out_path=None):
	# assume audio2 is environ which is a lot longer than audio1, and is mono
	if mode == 'mono':
		y1, sr = librosa.load(audio_path1, sr=sr, mono=True)
		y2, sr = librosa.load(audio_path2, sr=sr, mono=True)
		y1 = superpose(y1, y2, ratio)
	elif mode == 'stereo':
		y1, sr = librosa.load(audio_path1, sr=sr, mono=False)
		y2, sr = librosa.load(audio_path2, sr=sr, mono=True)
		np.random.seed(int(time.time()))
		y1[0] = superpose(y1[0], y2, ratio)
		np.random.seed(int(time.time()))
		y1[1] = superpose(y1[1], y2, ratio)
	else:
		raise ValueError('mode %s is invalid.' % mode)

	if out_path: librosa.output.write_wav(out_path, y1, sr, norm=True)
	return y1, sr


def white_noised(y, ratio=0.1):
	'''
	add white noise to wav time series

	:return: noised series
	'''
	return y + ratio * np.random.rand(len(y))


def superpose(y1, y2, ratio=1.0):
	'''
	add noise to wav time series from another wav time series

	:return: noised series
	'''
	l1, l2 = len(y1), len(y2)
	start = np.random.randint(0, l2 - l1)
	y2 = y2[start: start + l1]
	return y1 + ratio * y2


if __name__ == '__main__':
	wkdir = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/test/denoise/'
	os.chdir(wkdir)
	audio_path = '190304 20_27_18.wav'
	out_path = 'white 190304 20_27_18.wav'
	white_noised_from_path(audio_path, ratio=0.01, sr=16000, out_path=out_path)
