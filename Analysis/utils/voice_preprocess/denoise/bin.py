# final version of noise reducer
import os

import librosa
import numpy as np
from pysndfx import AudioEffectsChain
from utils.voice_preprocess.denoise.classic_demo import reduce_noise_power
from utils.voice_preprocess.denoise.RNNoise import reduce_noise_rnn

__denoise_kernel = reduce_noise_rnn # should takes (y, sr) and returns y_clean

def denoise(y, sr):
	'''
	receive a wav time series, return a denoised wav time series

	:param y: wav time series, mono or multichannel, 1d or 2d array
	:param sr: sample rate
	:return: y_clean, 1d or 2d array
	'''
	ndim = np.ndim(y)
	if ndim == 1: # mono
		return __denoise_kernel(y, sr)
	elif ndim == 2: # multichannel
		return [__denoise_kernel(yi, sr) for yi in y]
	else:
		raise ValueError('ndim = %d of y is invalid for noise reduction.' % ndim)


def denoise_from_path(audio_path, sr=16000, mode='mono', out_path=None):
	'''
	receive a audio_path, load it into wav time series,
	return a denoised wav time series, output the denoised .wav optionally

	:param audio_path: path to access audio file, .mp4, .wav ...
	:param sr: sample rate
	:param mode: str, 'mono' or 'stereo'
	:param out_path: output path for denoised wav file, optional
	:return: y_clean, shape like ([n_channel,] n_frame)
	'''
	if mode == 'mono':
		y, sr = librosa.load(audio_path, sr=sr, mono=True)
		y_clean = denoise(y, sr)  # (n_frame,)
	elif mode == 'stereo':
		y, sr = librosa.load(audio_path, sr=sr, mono=False)
		y_clean = denoise(y, sr)  # (n_channel, n_frame)
	else:
		raise ValueError('mode %s is invalid for noise reduction.' % mode)

	if out_path: librosa.output.write_wav(out_path, y_clean, sr, norm=True)
	return y_clean


if __name__ == '__main__':
	from utils.tools import suffix_filter
	from utils.voice_preprocess.denoise import noise_adder
	from tqdm import tqdm

	cwd = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/test/denoise/stereo/'
	os.chdir(cwd)

	audios = suffix_filter(os.listdir('.'), '.wav')

	for audio_org in audios:
		print(audio_org)
		# add noise to simulate
		# y, sr = noise_adder.superpose_from_path(audio_org, 'noise/cafe.wav', sr=48000, ratio=0.6, out_path='out/cafe noise %s' % audio_org)
		# noise_adder.white_noised_from_path(audio_org, sr=32000, ratio=0.03, out_path='out/white noise %s' % audio_org)
		# denoise from data
		# y_clean = denoise(y, sr)
		denoise_from_path('out/cafe noise %s' % audio_org, sr=48000, mode='stereo', out_path='out/cafe clean %s' % audio_org)
		# output
		# librosa.output.write_wav('out/d %s' % audio_org, y=y_clean, sr=sr, norm=True)
