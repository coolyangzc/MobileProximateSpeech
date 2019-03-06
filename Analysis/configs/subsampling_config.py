# FRAME_MS_RATIO = 5.692187578342543  # 帧 / 毫秒  这是当前 wav 格式对应的数据
FRAME_MS_RATIO = 0.09380235476687636  # 帧 / 毫秒  这是当前 mp3 格式对应的数据
# 和采样相关的参数
subsampling_config = {
	'offset': int(0 * FRAME_MS_RATIO),  # offset of subsampling, in frames (2s in this eg.) 偏移量
	'duration': int(10000 * FRAME_MS_RATIO),  # maximun length of subsampling range, in frames 持续时间
	'window': int(100 * FRAME_MS_RATIO),  # length of a single unit, in frames 单元窗口长度
	'stride': int(50 * FRAME_MS_RATIO)  # step in frames 移动窗口的步长
}

if __name__ == '__main__':
	from utils.voice_preprocess.mfcc import compute_frame_ms_ratio

	wkdirs = [
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/wty/trimmed',
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/gfz/trimmed',
		'/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/xy/trimmed'
	]
	ratio = 0.0
	for wkdir in wkdirs:
		ratio += compute_frame_ms_ratio('/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/wty/trimmed')
	ratio /= len(wkdirs)
	print(ratio)
