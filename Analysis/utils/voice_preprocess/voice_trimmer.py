# trim .mp3/.wav files according to our rules

from pydub import AudioSegment
import os
import wave
import contextlib
from tqdm import tqdm

from utils.tools import suffix_conv, date_time
from utils.logger import DualLogger
from utils.voice_preprocess.VAD import get_voice_chunks

start_sec_dict = {  # in second
	'竖直对脸，碰触鼻子': 1.1,
	'竖直对脸，不碰鼻子': 1.1,
	'竖屏握持，上端遮嘴': 1.1,
	'水平端起，倒话筒': 1.1,
	'话筒': 1.1,
	'横屏': 1.1,
	'耳旁打电话': 1.1,
	'桌上正面': 1.1,
	'手上正面': 1.1,

	'桌上反面': 2.1,
	'手上反面': 2.1,

	'裤兜': 6.0,
}
response_sec = 0.3  # human response time


def trim_head(file_path, dst_dir, in_format='wav', out_format='wav'):
	'''
	trim head of audio file_path and output to dst_dir

	:param file_path: audio file to trim
	:param dst_dir: output directory
	:param in_format: input format
	:param out_format: output format
	:return dst_path
	'''
	assert os.path.exists(file_path)
	txt_path = suffix_conv(file_path, '.txt')
	assert os.path.exists(txt_path)
	dst_path = os.path.join(dst_dir, os.path.basename(file_path))
	dst_path = suffix_conv(dst_path, out_format)

	audio = AudioSegment.from_file(file_path, in_format)
	with open(txt_path, 'r') as f:
		f.readline()
		description = f.readline().strip()

	audio[(start_sec_dict[description] + response_sec) * 1000:].export(dst_path, out_format)
	print('trimmed %s \n and saved to %s' % (file_path, dst_path))
	return dst_path


def trim_in_dir(wk_dir, dst_dir, in_format='wav', out_format='wav'):
	'''
	trim head of audios in wk_dir and output to dst_dir

	:param wk_dir: audio file directory
	:param dst_dir: output directory
	:param in_format: input format
	:param out_format: output format
	'''
	old_path = os.getcwd()
	if not os.path.exists(dst_dir):
		os.mkdir(dst_dir)
	assert os.path.exists(wk_dir)
	os.chdir(wk_dir)
	print('trimming in %s ...' % wk_dir)
	files = filter(lambda x: x.endswith('.%s' % in_format), os.listdir('.'))
	for file_path in tqdm(files):
		trim_head(file_path, dst_dir, in_format, out_format)
	print('done.')
	os.chdir(old_path)

if __name__ == '__main__':
	DualLogger('../logs/%svoice_trimmer.txt' % date_time())
	# wk_dir = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/Raw Data/xy/Filtered'
	# dst_dir = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/Raw Data/xy/trimmed'
	# trim_in_dir(wk_dir, dst_dir)
