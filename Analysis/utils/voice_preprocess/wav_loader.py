import os

import librosa
import numpy as np
from tqdm import tqdm

from utils.tools import suffix_filter, dir_filter, reverse_dict
from utils.voice_preprocess.data_loader import DataPack

label_dict = {  # 正负例分类字典, 0 表示舍弃这个特征的所有数据
	'竖直对脸，碰触鼻子': 1,
	'竖直对脸，不碰鼻子': 2,
	'竖屏握持，上端遮嘴': 3,
	'水平端起，倒话筒': 4,
	'话筒': 5,
	'横屏': 6,
	'耳旁打电话': 7,

	'桌上正面': -1,
	'手上正面': -2,
	'桌上反面': -3,
	'手上反面': -4,
	'裤兜': -5,
}

doc_dict = reverse_dict(label_dict)
try:
	del doc_dict[0]
except KeyError:
	pass


def get_label(txt_path):
	with open(txt_path) as f:
		f.readline()
		doc = f.readline().strip()
	return label_dict[doc]


class WavPack(DataPack):
	def __init__(self, sr, mode, data=None, labels=None, names=None):
		self.sr = sr
		if mode == 'mono':
			self.mono = True
		elif mode == 'stereo':
			self.mono = False
		else:
			raise ValueError('mode \'%s\' is invalid.' % mode)
		super().__init__(data, labels, names)

	def from_audio_dir(self, wav_dir, txt_dir=None, format='wav'):
		'''
		load from audio directory, e.g. 'cjr/trimmed2channel/'

		:param wav_dir: directory including lots of audio files
		:param txt_dir: directory including lots of .txt
		:param format: 'wav', 'mp4' and so on...
		:return: self, data shape like (n_audio, [n_channel,] n_frame[i])
		'''
		if txt_dir is None:
			txt_dir = os.path.join(wav_dir, '../original/')
		return self.from_data_dir(wav_dir, txt_dir, format,
								  data_getter=lambda path: librosa.load(path, sr=self.sr, mono=self.mono)[0],
								  label_getter=get_label, desc='loading audios')

	def from_chunks_dir(self, wav_dir, txt_dir=None, format='wav'):
		'''
		load from audio chunks directory, e.g. 'cjr/trimmed2channel/.../'

		:param wav_dir: directory including lots of audio chunks dirs
		:param txt_dir: directory including lots of .txt
		:param format: 'wav', 'mp4' and so on...
		:return: self, data shape like (n_chunk, [n_channel,] n_frame[i])
		'''
		if txt_dir is None:
			txt_dir = os.path.join(wav_dir, '../original/')
		txt_dir = os.path.abspath(txt_dir)

		owd = os.getcwd()
		os.chdir(wav_dir)
		chunk_folders = dir_filter(os.listdir('.'))

		for chunk_folder in tqdm(chunk_folders, desc='loading chunks', leave=False):
			txt_path = os.path.join(txt_dir, chunk_folder + '.txt')
			try:
				label = get_label(txt_path)
			except FileNotFoundError as e:
				print(e)
				continue

			if len(os.listdir(chunk_folder)) == 0:
				# load from outter folder
				audio_name = chunk_folder + '.' + format
				try:
					y, sr = librosa.load(audio_name, sr=self.sr, mono=self.mono)
				except FileNotFoundError as e:
					print(e)
					continue
				self.data.append(y)
				self.labels.append(label)
				self.names.append(os.path.abspath(audio_name))
			else:
				# load from chunk folder
				os.chdir(chunk_folder)
				audio_names = suffix_filter(os.listdir('.'), format)
				for audio_name in audio_names:
					y, sr = librosa.load(audio_name, sr=self.sr, mono=self.mono)
					self.data.append(y)
					self.labels.append(label)
					self.names.append(os.path.abspath(audio_name))
				os.chdir('../')

		os.chdir(owd)
		return self

	def apply_segmenting(self, **kwargs):
		'''
		apply segmenting to all audio data

		:param kwargs: segmenting params
		:return: self, data shape like (n_segment, [n_channel,] n_frame)
		'''
		data, labels, names = [], [], []
		progress = tqdm(total=len(self.labels), desc='segmenting', leave=False)
		for y, label, name in zip(self.data, self.labels, self.names):
			progress.update()
			for segment in segmenting(y, self.sr, **kwargs):
				data.append(segment)
				labels.append(label)
				names.append(name)

		self.data, self.labels, self.names = data, labels, names
		return self

	def extract_feature(self, librosa_method: callable, **kwargs) -> DataPack:
		'''
		extract features of each y from data and return a new DataPack
		!! use this method after segmenting, data should shape like (n_segment, [n_channel,] n_frame)

		:param librosa_method: callable, a librosa feature extraction method
		:param kwargs: params passed to librosa_method
		:return: DataPack(features, labels, audio_names), features shape like (n_segment, [n_channel,] ,...)
		'''
		features = []

		for y in tqdm(self.data, desc='extracting', leave=False):
			ndim = np.ndim(y)
			if ndim == 1:
				features.append(librosa_method(y=y, **kwargs))
			elif ndim == 2:
				features.append([librosa_method(y=yi, **kwargs) for yi in y])
			else:
				raise AttributeError('ndim of y: %d, is not valid for feature extraction.' % ndim)

		return DataPack(features, self.labels, self.names)

	def into_mono_mean(self):
		'''
		make data into mono channel by calculating the mean of two channels

		:return: self, data shape like (n_segment, n_frame)
		'''
		if self.mono == True: return self
		self.data = np.mean(self.data, axis=1)
		self.mono = True
		return self

	def into_mono_diff(self):
		'''
		make data into mono channel by calculating the difference between two channels

		:return: self, data shape like (n_segment, n_frame)
		'''
		if self.mono == True: return self
		self.into_ndarray()
		self.data = self.data[:, 0, :] - self.data[:, 1, :]
		self.mono = True
		return self

	def into_mono_div(self):
		'''
		make data into mono channel by calculating the ratio between two channels

		:return: self, data shape like (n_segment, n_frame)
		'''
		if self.mono == True: return self
		self.into_ndarray()
		self.data = self.data[:, 0, :] / self.data[:, 1, :]
		self.mono = True
		return self

	def apply_abs(self):
		self.data = np.abs(self.data)
		return self


def segmenting(y, sr, start=0., duration=10., window_size=0.020, stride=0.010):
	'''
	从帧的波形数据进行子采样，得到一系列子样本单元。可为多通道  sliding window algorithm

	:param y: wave data, shape like mono (n_frame, ), or stereo (n_channel, n_frame)
	:param sr: sample rate, fps
	:param start: 偏移量，sec
	:param duration: 采样长度，sec
	:param window_size: 采样单元长度, sec
	:param stride: 每次采样的步长, sec
	:return: list of segments, shape like (n_segment, n_frame), or (n_segment, n_channel, n_frame)
	'''
	ndim = np.ndim(y)
	if ndim == 1:
		segments = []
		start = int(start * sr)
		duration = int(duration * sr)
		window_size = int(window_size * sr)
		stride = int(stride * sr)
		high = min(start + duration, len(y))

		left = start
		right = left + window_size
		while right <= high:
			segments.append(y[left: right])
			left += stride
			right += stride

		return segments  # (n_segment, n_frame)

	elif ndim == 2:
		segments = np.array([segmenting(y[channel], sr, start, duration, window_size, stride)
							 for channel in range(len(y))])
		return np.rollaxis(segments, 1, 0)  # (n_segment, n_channel, n_frame)

	else:
		raise AttributeError('ndim of y: %d, is not valid for segmenting.' % ndim)
