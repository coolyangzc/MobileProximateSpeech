# 懒人一键包，需先用Audition做wav格式转换，最后调用本程序

import os
from utils.tools import date_time
from utils.logger import DualLogger
from utils import raw_data_filter
from utils.voice_preprocess import voice_trimmer, VAD

if __name__ == '__main__':
	DualLogger('../../logs/%svoice file filtering.txt' % date_time())

	os.chdir('/Users/james/MobileProximateSpeech/Analysis/Data/Study3/subjects/')
	for subject_name in ['wzq']: # todo
		if os.path.isdir(subject_name):

			print('\nraw data filtering...')
			raw_data_filter.filter3('%s/original' % subject_name, deal_individual=True, audio_format='wav')

			print('\ntrimming...')
			voice_trimmer.trim_in_dir('%s/filtered' % subject_name, in_format='wav', out_format='wav')

			print('\nvad...')
			VAD.get_voice_chunks_in_dir('%s/trimmed' % subject_name, aggressiveness=3)
