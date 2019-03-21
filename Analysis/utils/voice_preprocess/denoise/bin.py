# final version of noise reducer
import os

import librosa
import numpy as np
from utils.voice_preprocess.denoise.RNNoise import reduce_noise_rnn

__denoise_kernel = reduce_noise_rnn  # todo, denoise backend, should take (y, sr) and returns y_clean (all ndarray)


def denoise(y, sr, **kwargs):
	'''
	receive a wav time series, return a denoised wav time series

	:param y: wav time series, mono or multichannel, 1d or 2d array, float32
	:param sr: sample rate
	:return: y_clean, 1d or 2d array
	'''
	ndim = np.ndim(y)
	if ndim == 1:  # mono
		return __denoise_kernel(y, sr, **kwargs)
	elif ndim == 2:  # stereo
		return np.array([__denoise_kernel(yi, sr, **kwargs) for yi in y], dtype=np.float32)
	else:
		raise ValueError('ndim = %d of y is invalid for noise reduction.' % ndim)


def denoise_from_path(audio_path, sr=16000, mode='mono', out_path=None, **kwargs):
	'''
	receive a audio_path, load it into wav time series,
	return a denoised wav time series, output the denoised .wav optionally

	:param audio_path: path to access audio file, .mp4, .wav ...
	:param sr: sample rate
	:param mode: str, 'mono' or 'stereo'
	:param out_path: output path for denoised wav file, optional
	:return: y_clean, shape like ([n_channel,] n_frame), float32
	'''
	if mode == 'mono':
		y, sr = librosa.load(audio_path, sr=sr, mono=True)
	elif mode == 'stereo':
		y, sr = librosa.load(audio_path, sr=sr, mono=False)
	else:
		raise ValueError('mode %s is invalid for noise reduction.' % mode)

	y_clean = denoise(y, sr, **kwargs)  # ([n_channel,] n_frame)
	if out_path: librosa.output.write_wav(out_path, y_clean, sr, norm=True)
	return y_clean


if __name__ == '__main__':
	from utils.tools import suffix_filter
	from utils.voice_preprocess.denoise import noise_adder
	from tqdm import tqdm
	import time

	cwd = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/test/denoise/stereo/'
	os.chdir(cwd)

	audios = suffix_filter(os.listdir('.'), '.wav')

	for audio_org in audios:
		print(audio_org)
		# add noise to simulate
		# noise_adder.superpose_from_path(audio_org, 'noise/cafe.wav', sr=32000, mode='stereo', ratio=0.5, out_path='out/cafe noise %s' % audio_org)
		# noise_adder.white_noised_from_path(audio_org, sr=32000, ratio=0.03, out_path='out/white noise %s' % audio_org)
		# denoise from data
		# y_clean = denoise(y, sr)
		# denoise_from_path('out/cafe noise %s' % audio_org, sr=48000, mode='stereo', out_path='out/cafe clean %s' % audio_org)
		# output
		# librosa.output.write_wav('out/d %s' % audio_org, y=y_clean, sr=sr, norm=True)
		'''
		below is a simulation of denoising a 32000Hz, 16bit, stereo pcm wav data
		receives: y, sr
		return: y_clean (np.float32)
		'''
		y, sr = librosa.load('out/cafe noise %s' % audio_org, sr=32000, mono=False)
		y = np.array(y * 32768.0, order='C', dtype=np.int16)

		# begin denoising
		since = time.time()

		y_clean = denoise(y, sr, res_type='none')

		now = time.time()
		print('total   time = %f s\n' % (now - since))
		# output
		librosa.output.write_wav('out/cafe clean %s' % audio_org, y=y_clean, sr=sr, norm=True)
