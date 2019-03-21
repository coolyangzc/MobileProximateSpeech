import os
from utils.voice_preprocess.denoise.wavpcm import wav2pcm, pcm2wav

SCRIPT_PATH = '/Users/james/Test/rnnoise-master/examples/rnnoise_demo'


def rnn_denoise(wav_path, out_path=None, n_channel=1, sample_rate=16000):
	'''
	denoise using a trained rnn - see rnnoise

	:param wav_path:
	:param out_path:
	:param n_channel:
	:param sample_rate:
	'''
	name = wav_path.split('.')[0]
	if out_path is None:
		out_path = name + ' - denoised.wav'
	temp_path = name + ' - temp.pcm'
	temp_path_dn = name + ' - temp dn.pcm'
	wav2pcm(wav_path, temp_path)

	command = '%s  \'%s\'  \'%s\'' % (SCRIPT_PATH, temp_path, temp_path_dn)
	print(command)
	os.system(command)

	pcm2wav(temp_path_dn, out_path, n_channel, sample_rate)

	os.remove(temp_path)
	os.remove(temp_path_dn)


if __name__ == '__main__':
	wkdir = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/test/denoise/'
	os.chdir(wkdir)
	# wav_path = '190304 20_27_18.wav'
	# wav_path = '190304 20_27_34.wav'
	wav_path = '01_counting_org.wav'
	rnn_denoise(wav_path, 'out.wav', 1, 22050)
