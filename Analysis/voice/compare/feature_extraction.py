import os

import librosa
import numpy as np

from utils.voice_preprocess.data_loader import DataPack
from utils.voice_preprocess.wav_loader import WavPack


def visualize_mono_curves(f_pack: DataPack, f_name, y_label=None, x_label=None, out_path=None, **kwargs):
	# f_pack.data : 2d array (n_segment, m)
	if y_label is None: y_label = f_name
	if x_label is None: x_label = 'frame'
	p = f_pack.select_classes(range(1, 10)).into_ndarray()
	n = f_pack.select_classes(range(-10, 0)).into_ndarray()

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
	p = f_pack.select_classes(range(1, 10)).into_ndarray()
	n = f_pack.select_classes(range(-10, 0)).into_ndarray()

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
	from utils import io

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
	def analyze_rms(pack: WavPack, show=False, mono=False, **kwargs):
		print('\nextract rms')
		f = pack.extract_feature(librosa.feature.rms).into_ndarray().squeeze_data()
		if mono: f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().apply_abs()
		f.show_shape()
		if show: visualize_curves(f, 'RMS', 'rms', **kwargs)
		return f


	# zero_crossing_rate
	def analyze_zcr(pack: WavPack, show=False, mono=False, **kwargs):
		print('\nextract zero_crossing_rate')
		f = pack.extract_feature(librosa.feature.zero_crossing_rate).into_ndarray().squeeze_data()
		if mono: f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().apply_abs()
		f.show_shape()
		if show: visualize_curves(f, 'ZCR', 'zcr', **kwargs)
		return f


	# spectral_centroid
	def analyze_spectral_centroid(pack: WavPack, show=False, mono=False, **kwargs):
		print('\nextract spectral_centroid')
		f = pack.extract_feature(librosa.feature.spectral_centroid, sr=pack.sr).squeeze_data()
		if mono: f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().apply_abs()
		f.show_shape()
		if show: visualize_curves(f, 'Spectral Centroid Frequency', 'freq / Hz', **kwargs)
		return f


	# spectral_contrast
	def analyze_spectral_contrast(pack: WavPack, show=False, mono=False, **kwargs):
		print('\nextract spectral_contrast')
		f = pack.extract_feature(librosa.feature.spectral_contrast, sr=pack.sr).into_ndarray()
		f.data = np.mean(f.data, axis=2).squeeze()
		if mono: f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().apply_abs()
		f.show_shape()
		if show: visualize_curves(f, 'Spectral Contrast', 'contrast', 'band', **kwargs)
		return f


	# spectral_rolloff
	def analyze_spectral_rolloff(pack: WavPack, show=False, mono=False, **kwargs):
		print('\nextract spectral_rolloff')
		f = pack.extract_feature(librosa.feature.spectral_rolloff, sr=pack.sr).into_ndarray().squeeze_data()
		if mono: f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().apply_abs()
		f.show_shape()
		if show: visualize_curves(f, 'Spectral Rolloff Frequency', 'freq / Hz', **kwargs)
		return f


	# spectral_flatness
	def analyze_spectral_flatness(pack: WavPack, show=False, mono=False, **kwargs):
		print('\nextract spectral_flatness')
		f = pack.extract_feature(librosa.feature.spectral_flatness).into_ndarray().squeeze_data()
		if mono: f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().apply_abs()
		f.show_shape()
		if show: visualize_curves(f, 'Spectral Flatness', 'flatness', **kwargs)
		return f


	# spectral_bandwidth
	def analyze_spectral_bandwidth(pack: WavPack, show=False, mono=False, **kwargs):
		print('\nextract spectral_bandwidth')
		f = pack.extract_feature(librosa.feature.spectral_bandwidth, sr=pack.sr).into_ndarray().squeeze_data()
		if mono: f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().apply_abs()
		f.show_shape()
		if show: visualize_curves(f, 'Spectral Bandwidth', 'bandwidth', **kwargs)
		return f


	# magnitude frequency
	def analyze_mag_freq(pack: WavPack, show=False, mono=False, **kwargs):
		print('\nextract magnitude frequency')
		f = pack.extract_feature(lambda y: librosa.magphase(librosa.stft(y=y))[0])
		f.data = np.mean(f.data, axis=3)
		if mono: f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().apply_abs()
		f.show_shape()
		if show: visualize_curves(f, 'Magnitude Frequency', 'magnitude', 'freq / Hz', **kwargs)
		return f


	# mfcc
	def analyze_mfcc(pack: WavPack, show=False, mono=False, **kwargs):
		print('\nextract MFCC difference between two channels')
		f = pack.extract_feature(lambda y: librosa.feature.mfcc(y, sr=pack.sr, n_mfcc=3))
		f.data = np.mean(f.data, axis=3)
		if mono: f = WavPack(None, 'stereo', f.data, f.labels, f.names).into_mono_diff().apply_abs()
		f.show_shape()
		if show: visualize_curves(f, 'MFCC', 'magnitude', 'mfcc', **kwargs)
		return f


	# draw wav curves
	def wav_plot(pack: WavPack):
		visualize_curves(pack, 'Wav', 'wav', 'frame')


	# import re
	# name_pattern = re.compile('(.*/\d{6} \d\d_\d\d_\d\d) [-#]', re.U)
	# def label_getter(txt_path):
	# 	txt_path = name_pattern.search(txt_path).group(1) + '.txt'
	# 	return get_label(txt_path)
	# f = DataPack().from_data_dir('cjr/features/zcr', 'cjr/original', '.ndarray', io.load_from_file, label_getter, desc='loading zcr')
	# f.show_shape()

	# todo build pipeline here...
	# pack = load_pack(['wrl', 'gfz', 'cjr', 'wzq'], mode='stereo', n_seg=100)
	# analyze_mfcc(pack, show=True, mono=True, alpha=0.2)
	# analyze_rms(pack, show=True, mono=True, alpha=0.2)
	# analyze_zcr(pack, show=True, mono=True, alpha=0.2)
	# analyze_spectral_centroid(pack, show=True, mono=True, alpha=0.2)
	# analyze_spectral_bandwidth(pack, show=True, mono=True, alpha=0.2)
	# analyze_spectral_flatness(pack, show=True, mono=True, alpha=0.2)
	# analyze_mag_freq(pack, show=True, mono=True, alpha=0.2)

	subjects = list(filter(lambda x: os.path.isdir(x), os.listdir('./')))
	print(subjects)
	for i, subject in enumerate(subjects):
		os.chdir(subject)
		print('\nWorking in  %s  %d / %d\n' % (subject, i + 1, len(subjects)))

		pack = WavPack(sr=32000, mode='stereo').from_chunks_dir('trimmed2channel/').apply_segmenting(
			**fe_config.segment)
		if not os.path.exists('features/'):
			os.mkdir('features/')
		os.chdir('features/')

		f = analyze_rms(pack, mono=True)
		io.save_to_file(f, 'rms_diff.DataPack')

		f = analyze_spectral_flatness(pack, mono=True)
		io.save_to_file(f, 'spectral_flatness_diff.DataPack')

		f = analyze_mfcc(pack, mono=True)
		io.save_to_file(f, 'mfcc_diff.DataPack')

		# f = analyze_rms(pack)
		# io.save_to_file(f, 'rms.DataPack')
		#
		# f = analyze_zcr(pack)
		# io.save_to_file(f, 'zcr.DataPack')
		#
		# f = analyze_spectral_rolloff(pack)
		# io.save_to_file(f, 'spectral_rolloff.DataPack')
		#
		# f = analyze_spectral_contrast(pack)
		# io.save_to_file(f, 'spectral_contrast.DataPack')
		#
		# f = analyze_spectral_bandwidth(pack)
		# io.save_to_file(f, 'spectral_bandwidth.DataPack')
		#
		# f = analyze_spectral_centroid(pack)
		# io.save_to_file(f, 'spectral_centroid.DataPack')
		#
		# f = analyze_mfcc(pack)
		# io.save_to_file(f, 'mfcc.DataPack')

		os.chdir('../../')

	# wav_plot(pack)
	# analyze_rms(pack)
	# analyze_spectral_flatness(pack)
	# analyze_rms(pack)
	# analyze_mag_freq_diff(pack)
	pass
