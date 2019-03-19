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
	try:
		y, sr = librosa.load(src_path, sr=sample_rate, mono=mono)
	except:
		raise AttributeError('cannot open %s.' % os.path.abspath(src_path))

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


def re_encode_in_dir(wk_dir, out_dir=None, audio_format='mp4', sample_rate=32000, mono=False, suffix=True, n_jobs=2):
	'''
	batch re-encode
	:param wk_dir: a directory, should include many wav files.
	:param out_dir: if none, == wk_dir
	:param audio_format:
	:param sample_rate:
	:param mono: True - 1 channel, False - n channels
	:param suffix: whether to have -1 or -2 as suffix to imply the n_channel
	:param n_jobs: number of threads to work
	'''
	if out_dir is not None:
		out_dir = os.path.abspath(out_dir)
		if not os.path.exists(out_dir):
			os.mkdir(out_dir)
	owd = os.getcwd()
	os.chdir(wk_dir)
	files = suffix_filter(os.listdir('.'), suffix=audio_format)

	n_file = len(files)
	progress = tqdm(total=n_file)
	threads = [
		ReEncodeThread(files[i * n_file // n_jobs: (i + 1) * n_file // n_jobs],
					   out_dir, sample_rate, mono, suffix, progress)
		for i in range(n_jobs)
	]
	for thread in threads: thread.start()
	for thread in threads: thread.join()

	os.chdir(owd)


class ReEncodeThread(threading.Thread):
	def __init__(self, files, out_dir, sample_rate, mono, suffix, progress):
		self.files = files
		self.out_dir = out_dir
		self.sample_rate = sample_rate
		self.mono = mono
		self.suffix = suffix
		self.progress = progress
		super().__init__()

	def run(self):
		for file in self.files:
			self.progress.update()
			try:
				name = os.path.basename(
					re_encode(file, sample_rate=self.sample_rate, mono=self.mono, suffix=self.suffix))
			except AttributeError as e:
				print(e)
				continue
			if self.out_dir is not None:
				shutil.move(name, os.path.join(self.out_dir, name))


if __name__ == '__main__':
	# from utils.voice_preprocess.VAD import get_voice_chunks

	cwd = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/problem'
	os.chdir(cwd)
	for subject in ['wj', 'wwn', 'zfs']:
		os.chdir(subject)
		re_encode_in_dir('trimmed1channel/', out_dir='trimmed1channel(16000)/', audio_format='wav', sample_rate=16000, mono=True, suffix=False, n_jobs=3)

		os.chdir('..')
# re_encode_in_dir('original/', sample_rate=16000, mono=True, suffix=False, n_jobs=4)
# dst = re_encode(path, sample_rate=32000, mono=True, suffix=False)
# get_voice_chunks(dst, aggressiveness=3)
