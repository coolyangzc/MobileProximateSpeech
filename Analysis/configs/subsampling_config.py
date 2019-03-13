# FRAME_MS_RATIO = 0.03131841960956445  # 帧 / 毫秒  这是当前 librosa 对应的数据
FRAME_MS_RATIO = 0.09967136928064096  # 帧 / 毫秒  这是当前 speechpy 对应的数据
# 和采样相关的参数
subsampling_config = {
	'offset': int(0 * FRAME_MS_RATIO),  # offset of subsampling, in frames (2s in this eg.) 偏移量
	'duration': int(10000 * FRAME_MS_RATIO),  # maximun length of subsampling range, in frames 持续时间
	'window': int(100 * FRAME_MS_RATIO),  # length of a single unit, in frames 单元窗口长度
	'stride': int(50 * FRAME_MS_RATIO),  # step in frames 移动窗口的步长
	'group_size': 5,
}

if __name__ == '__main__':
	from utils.voice_preprocess.mfcc import compute_frame_ms_ratio, get_mfcc
	from utils.voice_preprocess.mfcc_data_loader import _subsampling
	from numpy import shape, mean
	# from matplotlib import pyplot as plt

	# wkdirs = [
	# 	'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/yzc/trimmed',
	# 	'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/wzq/trimmed',
	# 	'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/zfs/trimmed',
	# ]
	# ratios = []
	# for wkdir in wkdirs:
	# 	ratios += compute_frame_ms_ratio(wkdir)
	# print(mean(ratios))
	# plt.hist(ratios, bins=30, facecolor='blue', edgecolor='black')
	# plt.show()

	path = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/wzq/original/190306 23_13_39.wav'
	mfccs = get_mfcc(path)
	print('mfccs:     ', shape(mfccs))
	del subsampling_config['group_size']
	print('subsamples:', shape(_subsampling(mfccs, **subsampling_config)))
