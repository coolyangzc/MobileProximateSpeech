SAMPLE_RATE_2_CHANNEL = 32000
SAMPLE_RATE_1_CHANNEL = 16000
N_MFCC = 24
FRAME_TO_MS_2 = 0.06256306461585485  # 帧 / 毫秒  这是当前 librosa 32000Hz 对应的数据
# 和采样相关的参数
subsampling_config_2_channel = {
	'offset': int(1000 * FRAME_TO_MS_2),  # offset of subsampling, in frames (1s in this eg.) 偏移量
	'duration': int(6000 * FRAME_TO_MS_2),  # maximun length of subsampling range, in frames 持续时间
	'window': int(100 * FRAME_TO_MS_2),  # length of a single unit, in frames 单元窗口长度
	'stride': int(50 * FRAME_TO_MS_2),  # step in frames 移动窗口的步长
	'group_size': 5,
}

FRAME_TO_MS_1 = 0.03131841960956445  # 帧 / 毫秒  这是当前 librosa 16000Hz 对应的数据
subsampling_config_1_channel = {
	'offset': int(1000 * FRAME_TO_MS_1),  # offset of subsampling, in frames 偏移量
	'duration': int(6000 * FRAME_TO_MS_1),  # maximun length of subsampling range, in frames 持续时间
	'window': int(100 * FRAME_TO_MS_1),  # length of a single unit, in frames 单元窗口长度
	'stride': int(50 * FRAME_TO_MS_1),  # step in frames 移动窗口的步长
	'group_size': 5,
}

if __name__ == '__main__':
	print(subsampling_config_2_channel)
	from utils.voice_preprocess.mfcc import compute_frame_ms_ratio, get_mfcc
	from utils.voice_preprocess.mfcc_data_loader import _subsampling
	from numpy import shape, mean
	# from matplotlib import pyplot as plt
	import os

	cwd = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects copy'
	os.chdir(cwd)

	# wkdirs = [
	# 	'cjr/trimmed2channel',
	# 	'gfz/trimmed2channel',
	# 	'gyz/trimmed2channel',
	# 	'jwy/trimmed2channel',
	# 	'mq/trimmed2channel',
	# ]
	# ratios = []
	# for wkdir in wkdirs:
	# 	ratios += compute_frame_ms_ratio(wkdir, sr=SAMPLE_RATE_2_CHANNEL)
	# print(mean(ratios))
	# plt.hist(ratios, bins=30, facecolor='blue', edgecolor='black')
	# plt.show()

	path = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/wzq/original/190305 18_47_10.wav'
	mfccs = get_mfcc(path)
	print('mfccs:     ', shape(mfccs))
	del subsampling_config_1_channel['group_size']
	print('subsamples:', shape(_subsampling(mfccs, **subsampling_config_1_channel)))
