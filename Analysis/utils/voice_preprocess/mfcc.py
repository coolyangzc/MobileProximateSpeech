# 将mp3音频转换成MFCC向量
## （频率x时间）

import librosa.display
import matplotlib.pyplot as plt
# from speechpy import feature, processing
import os

import librosa
from tqdm import tqdm
from numpy import array, shape, ndim
from configs.subsampling_config import SAMPLE_RATE_1_CHANNEL, SAMPLE_RATE_2_CHANNEL, N_MFCC


def normalize(y, axis):
	'''
	归一化
	normalize y by eliminating its mean and std
	'''
	z = array(y)
	E = z.mean(axis=axis, keepdims=True)
	S = z.std(axis=axis, keepdims=True)
	return (z - E) / S


def get_mfcc(filename, mono=True, sr=None):
	if mono == True:
		return __get_mfcc_1_channel(filename, sr)
	else:
		return __get_mfcc_2_channel(filename, sr)


def __get_mfcc_1_channel(filename, sr=None):
	if sr is None: sr = SAMPLE_RATE_1_CHANNEL
	y, sr = librosa.load(filename, sr=sr, mono=True)
	# <del>这里要对频率归一化处理，因为不同人说话频率不同，归一化后的迁移效果斐然！</del>
	# return librosa.core.stft(y)
	return librosa.feature.mfcc(y, sr=sr, n_mfcc=N_MFCC)


# mfcc = feature.mfcc(y, sr, frame_length=0.020, frame_stride=0.010)
# return rollaxis(processing.cmvnw(mfcc, win_size=301, variance_normalization=True), 0, 2)


def __get_mfcc_2_channel(filename, sr=None):
	'''
	:return: two mfcc feature (of 2 channels), tuple
	'''
	if sr is None: sr = SAMPLE_RATE_2_CHANNEL
	y, sr = librosa.load(filename, sr=sr, mono=False)
	if ndim(y) != 2 or shape(y)[0] != 2:
		raise AttributeError('the audio file %s is not 2 channel.' % filename)
	# return librosa.core.stft(y)
	return librosa.feature.mfcc(y[0], sr=sr, n_mfcc=N_MFCC), librosa.feature.mfcc(y[1], sr=sr, n_mfcc=N_MFCC)


# 定义返回并可视化MFCC的函数
def visualize_mfcc_two_channels(filename, sr=SAMPLE_RATE_2_CHANNEL):
	mfccs = __get_mfcc_2_channel(filename, sr)
	print('mfcc:', shape(mfccs))
	title = os.path.basename(filename)
	plt.title('%s MFCC' % title)
	plt.subplot(2, 1, 1)
	librosa.display.specshow(mfccs[0], x_axis='time')
	plt.subplot(2, 1, 2)
	librosa.display.specshow(mfccs[1], x_axis='time')
	plt.tight_layout()
	plt.show()
	return mfccs


def compute_frame_ms_ratio(wkdir, sr):
	old_path = os.getcwd()
	os.chdir(wkdir)
	res = []
	files = list(filter(lambda x: x.endswith('.wav'), os.listdir('.')))
	for file in tqdm(files):
		y, sr = librosa.load(file, sr=sr, mono=True)
		duration = len(y) / sr
		# print('duration: %.2fs' % duration)
		mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
		# mfcc = rollaxis(feature.mfcc(y, sr), 0, 2)
		# print('frames: ', shape(mfcc))
		ratio = shape(mfcc)[-1] / (duration * 1000)
		res.append(ratio)
	# print('ratio: %.5f' % ratio)
	os.chdir(old_path)
	return res


if __name__ == '__main__':
	cwd = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects copy/cjr/wav2channel'
	os.chdir(cwd)
	visualize_mfcc_two_channels('190305 18_47_10.wav', sr=32000)
