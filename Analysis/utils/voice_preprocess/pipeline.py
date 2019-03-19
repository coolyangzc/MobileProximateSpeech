# 懒人一键包

import os
from utils.tools import date_time
from utils.logger import DualLogger
from utils import raw_data_filter
from utils.voice_preprocess import re_encoder, voice_trimmer, VAD

if __name__ == '__main__':
	DualLogger('../../logs/%svoice file filtering.txt' % date_time())

	os.chdir('/Users/james/MobileProximateSpeech/Analysis/Data/Study3/test/')
	for subject_name in ['downsampling']:  # todo
		if os.path.isdir(subject_name):
			print('\nSubject %s: \n' % subject_name)
			os.chdir(subject_name)

			print('\nraw data filtering...')
			raw_data_filter.filter3('original', deal_individual=True, audio_format='mp4')

			print('\nre-encoding...')
			# generate 1 channel 16000Hz audio
			os.mkdir('wav1channel')
			re_encoder.re_encode_in_dir('filtered', out_dir='wav1channel',
										audio_format='mp4', sample_rate=16000, mono=True, suffix=False)
			# generate 2 channel 32000Hz audio
			os.mkdir('wav2channel')
			re_encoder.re_encode_in_dir('filtered', out_dir='wav2channel',
										audio_format='mp4', sample_rate=32000, mono=False, suffix=False)

			print('\ntrimming...')
			voice_trimmer.trim_in_dir('wav1channel', dst_dir='trimmed1channel', in_format='wav', out_format='wav')
			voice_trimmer.trim_in_dir('wav2channel', dst_dir='trimmed2channel', in_format='wav', out_format='wav')

			print('\nvad...')
			VAD.get_voice_chunks_in_dir('wav1channel', aggressiveness=3)

			os.chdir('..')
