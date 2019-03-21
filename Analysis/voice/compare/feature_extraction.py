import os

import librosa
import numpy as np

from utils.voice_preprocess.data_loader import DataPack
from utils.voice_preprocess.wav_loader import WavPack


def visualize_mono_curves(f_pack: DataPack, f_name, y_label=None, x_label=None, out_path=None, **kwargs):
	if y_label is None: y_label = f_name
	if x_label is None: x_label = 'frame'
	p = f_pack.select_classes(range(1, 10)).into_data_ndarray()
	n = f_pack.select_classes(range(-10, 0)).into_data_ndarray()

	plt.figure()
	plt.plot(p.data[0, :], c='red', alpha=0.5, label='close', **kwargs)
	plt.plot(n.data[0, :], c='blue', alpha=0.5, label='far', **kwargs)
	for curve in p.data[1:, :]:
		plt.plot(curve, c='red', alpha=0.5, **kwargs)
	for curve in n.data[1:, :]:
		plt.plot(curve, c='blue', alpha=0.5, **kwargs)
	plt.title('%s distribution of p/n' % f_name)
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.legend()

	if out_path: plt.savefig(out_path)
	plt.show()


def visualize_stereo_curves(f_pack: DataPack, f_name, y_label=None, x_label=None, out_path=None, **kwargs):
	if y_label is None: y_label = f_name
	if x_label is None: x_label = 'frame'
	p = f_pack.select_classes(range(1, 10)).into_data_ndarray()
	n = f_pack.select_classes(range(-10, 0)).into_data_ndarray()

	plt.figure()
	for channel in 0, 1:
		plt.subplot(2, 1, channel + 1)
		plt.plot(p.data[0, channel, :], c='red', alpha=0.5, label='close', **kwargs)
		plt.plot(n.data[0, channel, :], c='blue', alpha=0.5, label='far', **kwargs)
		for curve in p.data[1:, channel, :]:
			plt.plot(curve, c='red', alpha=0.5, **kwargs)
		for curve in n.data[1:, channel, :]:
			plt.plot(curve, c='blue', alpha=0.5, **kwargs)

		plt.title('%s distribution of p/n channel %d' % (f_name, channel + 1))
		plt.xlabel(x_label)
		plt.ylabel(y_label)
		plt.legend()

	if out_path: plt.savefig(out_path)
	plt.show()


if __name__ == '__main__':
	from matplotlib import pyplot as plt
	import librosa.display

	cwd = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects copy/'
	os.chdir(cwd)


	def load_pack(subjects: list, mode, n_seg) -> WavPack:
		print('loading wav pack')
		pack = WavPack(sr=32000, mode=mode)
		for subject in subjects:
			pack.from_audio_dir('%s/trimmed2channel/' % subject)
		print('\nsr =', pack.sr)
		print('all data:')
		pack.show_shape().shuffle_all()

		print('\napplying segmenting and cropping')
		pack.apply_segmenting(window_size=0.100, stride=0.050)
		pack.shuffle_all().crop(n_seg).show_shape()
		print('\ne.g. labels and paths:')
		print(pack.labels[:5])
		print(pack.names[:5])
		return pack


	# spectral_centroid
	def analyze_spectral_centroid(pack: WavPack):
		print('\nextract spectral_centroid')
		f = pack.extract_feature(librosa.feature.spectral_centroid, sr=pack.sr).squeeze_data()
		f.show_shape()
		visualize_stereo_curves(f, 'Spectral Centroid Frequency', 'freq / Hz')


	# rms
	def analyze_rms(pack: WavPack):
		print('\nextract rms')
		f = pack.extract_feature(librosa.feature.rms).into_data_ndarray().squeeze_data()
		f.show_shape()
		visualize_stereo_curves(f, 'RMS', 'rms')


	# zero_crossing_rate
	def analyze_zero_crossing_rate(pack: WavPack):
		print('\nextract zero_crossing_rate')
		f = pack.extract_feature(librosa.feature.zero_crossing_rate).into_data_ndarray().squeeze_data()
		f.show_shape()
		visualize_stereo_curves(f, 'ZCR', 'zcr')


	# spectral_contrast
	def analyze_spectral_contrast(pack: WavPack):
		print('\nextract spectral_contrast')
		f = pack.extract_feature(librosa.feature.spectral_contrast, sr=pack.sr).into_data_ndarray()
		f.data = np.mean(f.data, axis=2).squeeze()
		f.show_shape()
		visualize_stereo_curves(f, 'Spectral Contrast', 'contrast', 'band')


	# spectral_rolloff
	def analyze_spectral_rolloff(pack: WavPack):
		print('\nextract spectral_rolloff')
		f = pack.extract_feature(librosa.feature.spectral_rolloff, sr=pack.sr).into_data_ndarray().squeeze_data()
		f.show_shape()
		visualize_stereo_curves(f, 'Spectral Rolloff Frequency', 'freq / Hz')


	# spectral_flatness
	def analyze_spectral_flatness(pack: WavPack):
		print('\nextract spectral_flatness')
		f = pack.extract_feature(librosa.feature.spectral_flatness).into_data_ndarray().squeeze_data()
		f.show_shape()
		visualize_stereo_curves(f, 'Spectral Flatness', 'flatness')


	# spectral_bandwidth
	def analyze_spectral_bandwidth(pack: WavPack):
		print('\nextract spectral_bandwidth')
		f = pack.extract_feature(librosa.feature.spectral_bandwidth, sr=pack.sr).into_data_ndarray().squeeze_data()
		f.show_shape()
		visualize_stereo_curves(f, 'Spectral Bandwidth', 'bandwidth')


	# magnitude frequency
	def analyze_mag_freq(pack: WavPack):
		print('\nextract magnitude frequency')
		f = pack.extract_feature(lambda y: librosa.magphase(librosa.stft(y=y))[0])
		f.data = np.mean(f.data, axis=3)
		f.show_shape()
		# f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().into_data_ndarray()
		visualize_stereo_curves(f, 'Magnitude Frequency', 'magnitude', 'freq / Hz')


	# magnitude frequency difference
	def analyze_mag_freq_diff(pack: WavPack):
		print('\nextract magnitude frequency difference between two channels')
		f = pack.extract_feature(lambda y: librosa.magphase(librosa.stft(y=y))[0])
		f.data = np.mean(f.data, axis=3)
		f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().into_data_ndarray()
		f.show_shape()
		visualize_mono_curves(f, 'Magnitude Frequency Difference of Two Channels', 'magnitude', 'freq / Hz')


	# todo build pipeline here...
	pack = load_pack(['wrl', 'gfz', 'cjr', 'wzq'], mode='stereo', n_seg=100)
	analyze_zero_crossing_rate(pack)
	analyze_spectral_flatness(pack)
	analyze_rms(pack)
	analyze_mag_freq_diff(pack)
