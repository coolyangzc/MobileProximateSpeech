# 对 wav 文件重新编码，得到不同的采样率、通道数
import os
import threading

import librosa
import numpy as np
from scipy.io import wavfile
from tqdm import tqdm
import shutil

from utils.tools import suffix_conv, suffix_filter


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
		raise AttributeError('ndim error in %s' % src_path)

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


def re_encode_in_dir(wk_dir, out_dir=None, audio_format='mp4', sample_rate=32000, mono=False, suffix=True):
	'''
	batch re-encode
	:param wk_dir: a directory, should include many wav files.
	:param out_dir: if none, == wk_dir
	:param audio_format:
	:param sample_rate:
	:param mono: True - 1 channel, False - n channels
	:param suffix: whether to have -1 or -2 as suffix to imply the n_channel
	'''
	owd = os.getcwd()
	os.chdir(wk_dir)
	files = suffix_filter(os.listdir('.'), suffix=audio_format)
	for file in tqdm(files):
		name = os.path.basename(re_encode(file, sample_rate=sample_rate, mono=mono, suffix=suffix))
		if out_dir is not None:
			shutil.move(name, os.path.join(owd, out_dir, name))

	os.chdir(owd)


if __name__ == '__main__':
	from utils.voice_preprocess.VAD import get_voice_chunks

	cwd = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/test/downsampling/'
	os.chdir(cwd)
	re_encode_in_dir('original/', out_dir='wav2channel/', sample_rate=32000, mono=False, suffix=False)
	re_encode_in_dir('original/', sample_rate=16000, mono=True, suffix=False)
# dst = re_encode(path, sample_rate=32000, mono=True, suffix=False)
# get_voice_chunks(dst, aggressiveness=3)
