import os
import numpy as np
import wave
from contextlib import closing


def wav2pcm(wav_path, out_path):
	'''
	convert wav to pcm

	:param wav_path:
	:param out_path:
	:return:
	'''
	with closing(open(wav_path, 'rb')) as f:
		f.seek(0)
		f.read(44)
		data = np.fromfile(f, dtype=np.int16)
	data.tofile(out_path)


def pcm2wav(pcm_path, out_path, n_channel, sample_rate):
	'''
	convert wav to pcm

	:param pcm_path:
	:param out_path:
	:param n_channel:
	:param sample_rate:
	'''
	with closing(open(pcm_path, 'rb')) as f:
		pcm_data = f.read()
	with closing(wave.open(out_path, 'wb')) as w:
		w.setnchannels(n_channel)
		w.setsampwidth(2)
		w.setframerate(sample_rate)
		w.writeframes(pcm_data)


if __name__ == '__main__':
	wkdir = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/test/denoise/'
	os.chdir(wkdir)
	pcm_path = 'denoised.pcm'
	wav_path = '190304 20_27_18.wav'
	pcm2wav(pcm_path, 'denoised ' + wav_path, 1, 16000)
