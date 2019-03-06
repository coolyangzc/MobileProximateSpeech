# 将mp3音频转换成MFCC向量
## （频率x时间）

import librosa
# import librosa.display
# import matplotlib.pyplot as plt
import os


## 定义返回并可视化MFCC的函数

def get_mfcc(filename, sr=None):
	y, sr = librosa.load(filename, sr=sr)
	return librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)


# def visualize_mfcc(filename, sr=None):
# 	mfccs = get_mfcc(filename, sr)
# 	plt.figure(figsize=(10, 4))
# 	librosa.display.specshow(mfccs, x_axis='time')
# 	plt.colorbar()
# 	plt.title('MFCC')
# 	plt.tight_layout()
# 	plt.show()
# 	return mfccs


def compute_frame_ms_ratio(wkdir):
	old_path = os.getcwd()
	os.chdir(wkdir)
	res = 0.0
	files = list(filter(lambda x: x.endswith('.wav'), os.listdir('.')))
	for file in files:
		y, sr = librosa.load(file)
		duration = len(y) / sr
		mfcc = librosa.feature.mfcc(y, sr, n_mfcc=40)
		res += len(mfcc) / duration
	res /= len(files)
	os.chdir(old_path)
	return res


if __name__ == '__main__':
	from tqdm import tqdm as progress
	import pickle

	# 以下是正负例分类程序
	os.chdir('../Data/Sounds/MP3/Positive/')
	file_list = os.listdir()

	## 预览第一个音频
	filename = file_list[0]
	visualize_mfcc(filename)

	## 开始处理音频
	print('Positive...')
	for filename in progress(file_list):
		mfccs = get_mfcc(filename)
		portions = filename.split('.')
		assert portions[-1] == 'mp3'
		portions[-1] = 'ftr'  # stands for feature
		newname = '.'.join(portions)
		with open(newname, 'wb') as f:
			pickle.dump(mfccs, f)
	print('Done.')

	os.chdir('../Negative/')
	file_list = os.listdir()
	print('Negative...')
	for filename in progress(file_list):
		mfccs = get_mfcc(filename)
		portions = filename.split('.')
		assert portions[-1] == 'mp3'
		portions[-1] = 'ftr'  # stands for feature
		newname = '.'.join(portions)
		with open(newname, 'wb') as f:
			pickle.dump(mfccs, f)
	print('Done.')
