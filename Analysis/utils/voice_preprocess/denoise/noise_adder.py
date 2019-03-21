import os

import librosa
import numpy as np


def white_noise(audio_path, out_path, ratio=0.1, sr=16000):
	y, sr = librosa.load(audio_path, sr=sr)
	y = y + ratio * np.random.rand(len(y))
	librosa.output.write_wav(out_path, y, sr, norm=True)


def superpose(audio_path1, audio_path2, out_path, ratio=1.0, sr=16000):
	# assume audio2 is environ which is a lot longer than audio1
	y1, sr = librosa.load(audio_path1, sr=sr)
	y2, sr = librosa.load(audio_path2, sr=sr)
	l1, l2 = len(y1), len(y2)
	pos = np.random.randint(0, l2 - l1)
	y2 = y2[pos: pos + l1]
	y1 += ratio * y2
	librosa.output.write_wav(out_path, y1, sr, norm=True)


if __name__ == '__main__':
	wkdir = '/Users/james/MobileProximateSpeech/Analysis/Data/Study3/test/denoise/'
	os.chdir(wkdir)
	audio_path = '190304 20_27_18.wav'
	out_path = 'white 190304 20_27_18.wav'
	white_noise(audio_path, out_path, ratio=0.01, sr=16000)
