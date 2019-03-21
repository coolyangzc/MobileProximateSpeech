import os

import librosa
import numpy as np

from utils.voice_preprocess.data_loader import DataPack
from utils.voice_preprocess.wav_loader import WavPack


def visualize_mono_curves(f_pack: DataPack, f_name, y_label=None, x_label=None, out_path=None, **kwargs):
	# f_pack.data : 2d array (n_segment, m)
	if y_label is None: y_label = f_name
	if x_label is None: x_label = 'frame'
	p = f_pack.select_classes(range(1, 10)).into_data_ndarray()
	n = f_pack.select_classes(range(-10, 0)).into_data_ndarray()

	plt.figure()
	try:
		plt.plot(p.data[0, :], c='red', label='close', **kwargs)
	except IndexError:
		pass
	try:
		plt.plot(n.data[0, :], c='blue', label='far', **kwargs)
	except IndexError:
		pass
	try:
		for curve in p.data[1:, :]:
			plt.plot(curve, c='red', **kwargs)
	except IndexError:
		pass
	try:
		for curve in n.data[1:, :]:
			plt.plot(curve, c='blue', **kwargs)
	except IndexError:
		pass
	plt.title('%s distribution of p/n' % f_name)
	plt.xlabel(x_label)
	plt.ylabel(y_label)
	plt.legend()

	if out_path: plt.savefig(out_path)
	plt.show()


def visualize_stereo_curves(f_pack: DataPack, f_name, y_label=None, x_label=None, out_path=None, **kwargs):
	# f_pack.data : 3d array (n_segment, 2, m)
	if y_label is None: y_label = f_name
	if x_label is None: x_label = 'frame'
	p = f_pack.select_classes(range(1, 10)).into_data_ndarray()
	n = f_pack.select_classes(range(-10, 0)).into_data_ndarray()

	plt.figure()
	for channel in 0, 1:
		plt.subplot(2, 1, channel + 1)
		try:
			plt.plot(p.data[0, channel, :], c='red', label='close', **kwargs)
		except IndexError:
			pass
		try:
			plt.plot(n.data[0, channel, :], c='blue', label='far', **kwargs)
		except IndexError:
			pass
		try:
			for curve in p.data[1:, channel, :]:
				plt.plot(curve, c='red', **kwargs)
		except IndexError:
			pass
		try:
			for curve in n.data[1:, channel, :]:
				plt.plot(curve, c='blue', **kwargs)
		except IndexError:
			pass

		plt.title('%s distribution of p/n channel %d' % (f_name, channel + 1))
		plt.xlabel(x_label)
		plt.ylabel(y_label)
		plt.legend()

	if out_path: plt.savefig(out_path)
	plt.show()


def visualize_curves(f_pack: DataPack, f_name, y_label=None, x_label=None, out_path=None, **kwargs):
	# f_pack.data : 2d or 3d array (n_segment, [2,] m)
	ndim = np.ndim(f_pack.data)
	if not kwargs.get('alpha'):
		kwargs['alpha'] = 0.5
	if ndim == 2:
		visualize_mono_curves(f_pack, f_name, y_label, x_label, out_path, **kwargs)
	elif ndim == 3:
		visualize_stereo_curves(f_pack, f_name, y_label, x_label, out_path, **kwargs)
	else:
		raise AttributeError('ndim of f_pack.data %d is invalid.' % ndim)


if __name__ == '__main__':
	from matplotlib import pyplot as plt
	import librosa.display
	import configs.feature_extraction_config as fe_config

	cwd = '/Users/james/MobileProximateSpeech/Data/Study3/subjects copy/'
	os.chdir(cwd)


	def load_pack(subjects: list, mode, n_seg) -> WavPack:
		print('loading wav pack')
		pack = WavPack(sr=32000, mode=mode)
		for subject in subjects:
			pack.from_audio_dir('%s/trimmed2channel/' % subject)
		print('\nsr =', pack.sr)
		print('all data:')
		pack.show_shape().shuffle_all()

		print('\napplying segmenting')
		pack.apply_segmenting(window_size=0.100, stride=0.050).show_shape()
		print('\nafter cropping')
		pack.shuffle_all().crop(n_seg).show_shape()
		print('\ne.g. labels and paths:')
		print(pack.labels[:5])
		print(pack.names[:5])
		return pack


	# rms
	def analyze_rms(pack: WavPack, show=False):
		print('\nextract rms')
		f = pack.extract_feature(librosa.feature.rms).into_data_ndarray().squeeze_data()
		f.show_shape()
		if show: visualize_curves(f, 'RMS', 'rms')
		return f


	# zero_crossing_rate
	def analyze_zcr(pack: WavPack, show=False):
		print('\nextract zero_crossing_rate')
		f = pack.extract_feature(librosa.feature.zero_crossing_rate).into_data_ndarray().squeeze_data()
		f.show_shape()
		if show: visualize_curves(f, 'ZCR', 'zcr')
		return f


	# spectral_centroid
	def analyze_spectral_centroid(pack: WavPack, show=False):
		print('\nextract spectral_centroid')
		f = pack.extract_feature(librosa.feature.spectral_centroid, sr=pack.sr).squeeze_data()
		f.show_shape()
		if show: visualize_curves(f, 'Spectral Centroid Frequency', 'freq / Hz')
		return f


	# spectral_contrast
	def analyze_spectral_contrast(pack: WavPack, show=False):
		print('\nextract spectral_contrast')
		f = pack.extract_feature(librosa.feature.spectral_contrast, sr=pack.sr).into_data_ndarray()
		f.data = np.mean(f.data, axis=2).squeeze()
		f.show_shape()
		if show: visualize_curves(f, 'Spectral Contrast', 'contrast', 'band')
		return f


	# spectral_rolloff
	def analyze_spectral_rolloff(pack: WavPack, show=False):
		print('\nextract spectral_rolloff')
		f = pack.extract_feature(librosa.feature.spectral_rolloff, sr=pack.sr).into_data_ndarray().squeeze_data()
		f.show_shape()
		if show: visualize_curves(f, 'Spectral Rolloff Frequency', 'freq / Hz')
		return f


	# spectral_flatness
	def analyze_spectral_flatness(pack: WavPack, show=False):
		print('\nextract spectral_flatness')
		f = pack.extract_feature(librosa.feature.spectral_flatness).into_data_ndarray().squeeze_data()
		f.show_shape()
		if show: visualize_curves(f, 'Spectral Flatness', 'flatness')
		return f


	# spectral_bandwidth
	def analyze_spectral_bandwidth(pack: WavPack, show=False):
		print('\nextract spectral_bandwidth')
		f = pack.extract_feature(librosa.feature.spectral_bandwidth, sr=pack.sr).into_data_ndarray().squeeze_data()
		f.show_shape()
		if show: visualize_curves(f, 'Spectral Bandwidth', 'bandwidth')
		return f


	# magnitude frequency
	def analyze_mag_freq(pack: WavPack, show=False):
		print('\nextract magnitude frequency')
		f = pack.extract_feature(lambda y: librosa.magphase(librosa.stft(y=y))[0])
		f.data = np.mean(f.data, axis=3)
		f.show_shape()
		# f = WavPack, show=False(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().into_data_ndarray()
		if show: visualize_curves(f, 'Magnitude Frequency', 'magnitude', 'freq / Hz')
		return f


	# magnitude frequency difference
	def analyze_mag_freq_diff(pack: WavPack, show=False, **kwargs):
		print('\nextract magnitude frequency difference between two channels')
		f = pack.extract_feature(lambda y: librosa.magphase(librosa.stft(y=y, n_fft=1024))[0])
		f.data = np.mean(f.data, axis=3)
		f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().into_data_ndarray()
		f.show_shape()
		if show: visualize_curves(f, 'Magnitude Frequency Difference of Two Channels', 'magnitude', 'freq / Hz', **kwargs)
		return f

	# mfcc
	def analyze_mfcc(pack: WavPack, show=False, **kwargs):
		print('\nextract magnitude frequency difference between two channels')
		f = pack.extract_feature(lambda y: librosa.feature.mfcc(y, sr=pack.sr))
		f.data = np.mean(f.data, axis=3)
		# f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().into_data_ndarray()
		# f.show_shape()
		if show: visualize_curves(f, 'MFCC', 'magnitude', 'mfcc', **kwargs)
		return f


	# draw wav curves
	def wav_plot(pack: WavPack):
		visualize_curves(pack, 'Wav', 'wav', 'frame')


	# todo build pipeline here...
	# pack = load_pack(['wrl', 'gfz', 'cjr', 'wzq'], mode='stereo', n_seg=100)
	pack = WavPack(sr=32000, mode='stereo').from_chunks_dir('cjr/trimmed2channel/').apply_segmenting(**fe_config.segment)

	# f = analyze_rms(pack, show=True)
	# f.auto_save('feature/rms', suffix='.ndarray')
	#
	# f = analyze_zcr(pack)
	# f.auto_save('feature/zcr', suffix='.ndarray')
	#
	# f = analyze_spectral_rolloff(pack)
	# f.auto_save('feature/spectral_rolloff', suffix='.ndarray')
	#
	# f = analyze_spectral_contrast(pack)
	# f.auto_save('feature/spectral_contrast', suffix='.ndarray')
	#
	# f = analyze_spectral_bandwidth(pack)
	# f.auto_save('feature/spectral_bandwidth', suffix='.ndarray')
	#
	# f = analyze_spectral_centroid(pack)
	# f.auto_save('feature/spectral_centroid', suffix='.ndarray')

	# f = analyze_mag_freq_diff(pack, show=True, alpha=0.1)
	# f.auto_save('features/mag_freq_diff', suffix='.ndarray')

	# f = analyze_mfcc(pack, show=False, alpha=0.2)
	# f.auto_save('features/mfcc', suffix='.ndarray')


	# wav_plot(pack)
	# analyze_rms(pack)
	# analyze_spectral_flatness(pack)
	# analyze_rms(pack)
	# analyze_mag_freq_diff(pack)
	pass
