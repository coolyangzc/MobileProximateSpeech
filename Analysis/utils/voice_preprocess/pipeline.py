# 懒人一键包，需先用Audition做wav格式转换，最后调用本程序

import os
from utils.tools import date_time
from utils.logger import DualLogger
from utils import raw_data_filter
from utils.voice_preprocess import voice_trimmer, VAD

if __name__ == '__main__':
	DualLogger('../../logs/%svoice file filtering.txt' % date_time())

	subject_name = 'xxx' # todo 受试者名字，唯一需要填写的参数

	print('\nraw data filtering...')
	raw_data_filter.filter3('../../Data/Study3/subjects/%s/original' % subject_name, deal_individual=True, audio_format='wav')

	print('\ntrimming...')
	voice_trimmer.trim_in_dir('../../Data/Study3/subjects/%s/filtered' % subject_name, in_format='wav', out_format='wav')

	print('\nvad...')
	VAD.get_voice_chunks_in_dir('../../Data/Study3/subjects/%s/trimmed' % subject_name, aggressiveness=3)
