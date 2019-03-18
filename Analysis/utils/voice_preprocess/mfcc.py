# 将mp3音频转换成MFCC向量
## （频率x时间）

import librosa.display
import matplotlib.pyplot as plt
# from speechpy import feature, processing
import os

import librosa
from tqdm import tqdm
from numpy import array, shape, rollaxis

SAMPLE_RATE = 16000


def normalize(y, axis):
	'''
	归一化
	normalize y by eliminating its mean and std
	'''
	z = array(y)
	E = z.mean(axis=axis, keepdims=True)
	S = z.std(axis=axis, keepdims=True)
	return (z - E) / S


def get_mfcc(filename, sr=SAMPLE_RATE):
	y, sr = librosa.load(filename, sr=sr)
	# 这里要对频率归一化处理，因为不同人说话频率不同，归一化后的迁移效果斐然！
	return librosa.core.stft(y)
	# mfcc = feature.mfcc(y, sr, frame_length=0.020, frame_stride=0.010)
	# return rollaxis(processing.cmvnw(mfcc, win_size=301, variance_normalization=True), 0, 2)


# 定义返回并可视化MFCC的函数
def visualize_mfcc(filename, sr=SAMPLE_RATE, loc=None):
	mfccs = get_mfcc(filename, sr)
	plt.subplot(loc)
	librosa.display.specshow(mfccs, x_axis='time')
	plt.colorbar()
	title = os.path.basename(filename)
	plt.title('%s MFCC' % title)
	plt.tight_layout()
	return mfccs


def compute_frame_ms_ratio(wkdir):
	old_path = os.getcwd()
	os.chdir(wkdir)
	res = []
	files = list(filter(lambda x: x.endswith('.wav'), os.listdir('.')))
	for file in tqdm(files):
		y, sr = librosa.load(file, sr=SAMPLE_RATE)
		duration = len(y) / sr
		# print('duration: %.2fs' % duration)
		mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=24)
		# mfcc = rollaxis(feature.mfcc(y, sr), 0, 2)
		# print('frames: ', shape(mfcc))
		ratio = shape(mfcc)[-1] / (duration * 1000)
		res.append(ratio)
	# print('ratio: %.5f' % ratio)
	os.chdir(old_path)
	return res


if __name__ == '__main__':
	os.chdir('/Users/james/MobileProximateSpeech/Analysis/Data/Study3/test/compare')
	plt.figure(figsize=(20, 16))
	visualize_mfcc('female/gfz0.wav', loc=421)
	visualize_mfcc('female/gfz1.wav', loc=423)
	visualize_mfcc('female/mq0.wav', loc=425)
	visualize_mfcc('female/mq1.wav', loc=427)
	visualize_mfcc('male/wj0.wav', loc=422)
	visualize_mfcc('male/wj1.wav', loc=424)
	visualize_mfcc('male/wwn0.wav', loc=426)
	visualize_mfcc('male/wwn1.wav', loc=428)
	plt.show()
