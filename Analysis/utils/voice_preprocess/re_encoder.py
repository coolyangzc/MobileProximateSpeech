# 对 wav 文件重新编码，得到不同的采样率、通道数
import os

import librosa
import numpy as np
from scipy.io import wavfile

from utils.tools import suffix_conv


def re_encode(src_path, dst_path=None, sample_rate=32000, mono=False, suffix=True):
	'''
	re-encode the source audio file into valid format which is recognisable for VAD.py

	:param src_path: source audio path, can be mp4, mp3, or wav file
	:param dst_path: destined path for output, if None, the output will be generated in place, auto-named with
		whether `mono` is True or False.
	:param sample_rate:
	:param mono: True - 1 channel, False - n channels
	:param suffix: whether to have -1 or -2 as suffix to imply the n_channel
	:return: `dst_path`
	'''
	y, sr = librosa.load(src_path, sr=sample_rate, mono=mono)
	dim = np.ndim(y)
	if dim == 1:
		n_channel = 1
	elif dim == 2:
		n_channel = np.shape(y)[0]
		y = np.rollaxis(y, 0, 2)
	else:
		raise AttributeError

	if dst_path is None:
		dir = os.path.dirname(os.path.abspath(src_path))
		name = os.path.basename(src_path)
		if suffix == True:
			name = name.split('.')[0]
			name += '-' + ('1' if mono == True else str(n_channel)) + '.wav'
		else:
			name = suffix_conv(name, '.wav')
		dst_path = os.path.join(dir, name)

	librosa.output.write_wav(dst_path, y, sr)
	y = np.asarray(y * 32768.0, dtype=np.int16)  # convert the wave data to 16-bit PCM format
	wavfile.write(dst_path, sr, y)

	return dst_path


if __name__ == '__main__':
	from utils.voice_preprocess.VAD import get_voice_chunks

	path = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/test/downsampling/190304 20_10_35.mp4'
	dst = re_encode(path, sample_rate=32000, mono=True, suffix=False)
	get_voice_chunks(dst, aggressiveness=3)
