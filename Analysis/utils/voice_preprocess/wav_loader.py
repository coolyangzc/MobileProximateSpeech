import os
import numpy as np
from tqdm import tqdm
import librosa
from utils.tools import suffix_filter, suffix_conv, dir_filter, reverse_dict
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


def get_doc(txt_dir, txt_name):
	with open(os.path.join(txt_dir, txt_name)) as f:
		f.readline()
		doc = f.readline().strip()
	return doc


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
		txt_dir = os.path.abspath(txt_dir)

		owd = os.getcwd()
		os.chdir(wav_dir)
		audio_names = suffix_filter(os.listdir('.'), format)
		for audio_name in tqdm(audio_names):
			try:
				label = label_dict[get_doc(txt_dir, suffix_conv(audio_name, '.txt'))]
			except FileNotFoundError as e:
				print(e)
				continue
			y, sr = librosa.load(audio_name, sr=self.sr, mono=self.mono)

			self.data.append(y)
			self.labels.append(label)
			self.names.append(os.path.abspath(audio_name))

		os.chdir(owd)
		return self

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

		for chunk_folder in tqdm(chunk_folders):
			try:
				label = label_dict[get_doc(txt_dir, chunk_folder + '.txt')]
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
		for y, label, name in zip(self.data, self.labels, self.names):
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

		for y in self.data:
			ndim = np.ndim(y)
			if ndim == 1:
				features.append(librosa_method(y=y, **kwargs))
			elif ndim == 2:
				features.append([librosa_method(y=yi, **kwargs) for yi in y])
			else:
				raise AttributeError('ndim of y: %d, is not valid for feature extraction.' % ndim)

		return DataPack(features, self.labels, self.names)


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


if __name__ == '__main__':
	from matplotlib import pyplot as plt
	import librosa.display

	cwd = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects copy/'
	os.chdir(cwd)

	def load_pack(subjects: list, mode, n_seg) -> WavPack:
		pack = WavPack(sr=32000, mode=mode)
		for subject in subjects:
			pack.from_audio_dir('%s/trimmed2channel/' % subject)
		print('\nsr =', pack.sr)
		print('all data:')
		pack.show_shape().shuffle_all()
		print()

		print('\napplying segmenting and cropped')
		pack.apply_segmenting(window_size=0.100, stride=0.050)
		pack.shuffle_all().crop(n_seg).show_shape()
		print(pack.labels[:5])
		print(pack.names[:5])
		return pack

	# spectral_centroid
	def analyze_spectral_centroid(pack: WavPack):
		print('\nextract spectral_centroid')
		f = pack.extract_feature(librosa.feature.spectral_centroid, sr=pack.sr).squeeze_data()
		f.show_shape()
		p = f.select_classes(range(1, 10)).into_data_ndarray()
		n = f.select_classes(range(-10, 0)).into_data_ndarray()

		plt.figure()
		for channel in 0, 1:
			plt.subplot(2, 1, channel + 1)
			plt.plot(p.data[0, channel, :], c='red', alpha=0.5, label='close')
			plt.plot(n.data[0, channel, :], c='blue', alpha=0.5, label='far')
			for curve in p.data[1:, channel, :]:
				plt.plot(curve, c='red', alpha=0.5)
			for curve in n.data[1:, channel, :]:
				plt.plot(curve, c='blue', alpha=0.5)
			plt.title('Spectral Centroid distribution of p/n channel %d' % channel)
			plt.ylabel('Freq')
			plt.xlabel('Frame')
			plt.legend()
		plt.show()

	# rms
	def analyze_rms(pack: WavPack):
		print('\nextract rms')
		f = pack.extract_feature(librosa.feature.rms).into_data_ndarray().squeeze_data()
		f.show_shape()

		p = f.select_classes(range(1, 10)).into_data_ndarray()
		n = f.select_classes(range(-10, 0)).into_data_ndarray()

		plt.figure()
		for channel in 0, 1:
			plt.subplot(2, 1, channel + 1)
			plt.plot(p.data[0, channel, :], c='red', alpha=0.5, label='close')
			plt.plot(n.data[0, channel, :], c='blue', alpha=0.5, label='far')
			for curve in p.data[1:, channel, :]:
				plt.plot(curve, c='red', alpha=0.5)
			for curve in n.data[1:, channel, :]:
				plt.plot(curve, c='blue', alpha=0.5)
			plt.title('RMS distribution of p/n channel %d' % channel)
			plt.ylabel('RMS')
			plt.xlabel('Frame')
			plt.legend()
		plt.show()

	# zero_crossing_rate
	def analyze_zero_crossing_rate(pack: WavPack):
		print('\nextract zero_crossing_rate')
		f = pack.extract_feature(librosa.feature.zero_crossing_rate).into_data_ndarray().squeeze_data()
		f.show_shape()

		p = f.select_classes(range(1, 10)).into_data_ndarray()
		n = f.select_classes(range(-10, 0)).into_data_ndarray()

		plt.figure()
		for channel in 0, 1:
			plt.subplot(2, 1, channel + 1)
			plt.plot(p.data[0, channel, :], c='red', alpha=0.5, label='close')
			plt.plot(n.data[0, channel, :], c='blue', alpha=0.5, label='far')
			for curve in p.data[1:, channel, :]:
				plt.plot(curve, c='red', alpha=0.5)
			for curve in n.data[1:, channel, :]:
				plt.plot(curve, c='blue', alpha=0.5)
			plt.title('ZCR distribution of p/n channel %d' % channel)
			plt.ylabel('ZCR')
			plt.xlabel('Frame')
			plt.legend()
		plt.show()

	# todo build pipeline here...
	pack = load_pack(['wrl', 'gfz', 'cjr', 'wzq'], mode='stereo', n_seg=100)
	analyze_rms(pack)
