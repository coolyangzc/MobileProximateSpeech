import os
import wave
import struct
import numpy as np
import voice_feature
from sklearn.externals import joblib

voice_path = '../Data/Field Study/trimmed/phone-voice_check'
feature_num = 32

used_feature = [1, # min
				1, # max
				1, # median
				1, # mean
				0, # std
				1, # IQR
				0, # energy
				1] # RMS


def analyze(user_path, file_name):
	vad_file = os.path.join(user_path, file_name + ' vad.txt')
	if not os.path.exists(vad_file):
		return
	file = open(vad_file, "r", encoding='utf-8')
	lines = file.readlines()
	data = lines[0].split(' ')
	start_time, end_time = float(data[0]), float(data[1])
	file.close()
	print(start_time, end_time)
	wav_file = os.path.join(user_path, file_name + '.wav')

	try:
		wavefile = wave.open(wav_file, 'r')
	except wave.Error:
		return
	nchannels = wavefile.getnchannels()
	sample_width = wavefile.getsampwidth()
	framerate = wavefile.getframerate()
	numframes = wavefile.getnframes()
	time = numframes / framerate

	print(nchannels, sample_width, framerate, numframes, time)

	y = np.zeros((2, numframes))
	for i in range(numframes):
		val = wavefile.readframes(1)
		left, right = val[0:2], val[2:4]
		y[0][i] = struct.unpack('h', left)[0]
		y[1][i] = struct.unpack('h', right)[0]

	out_file = os.path.join(user_path, file_name + ' feature.txt')
	output = open(out_file, 'w', encoding='utf-8')
	output.write(str(feature_num) + '\n')

	interval_size = 6400  # 32000 * 0.2s
	stride = 0.5
	s = int(start_time * framerate)
	e = int(end_time * framerate)
	while s + interval_size < e:
		feature = voice_feature.extract_voice_features(y[0][s:s + interval_size], y[1][s:s + interval_size])
		for f in feature:
			output.write(str(f) + '\n')
		s += int(interval_size * stride)


def calc_features():
	for u in os.listdir(voice_path):
		if 'no speak' in u or '.txt' in u:
			continue
		user_path = os.path.join(voice_path, u)
		for f in os.listdir(user_path):
			if f.endswith('.wav'):
				analyze(user_path, f[:-4])


def classification():
	voice_model = joblib.load('voice_model.m')
	for u in os.listdir(voice_path):
		if 'no speak' in u or '.txt' in u:
			continue
		user_path = os.path.join(voice_path, u)
		for f in os.listdir(user_path):
			if f.endswith('feature.txt'):
				feature_file = os.path.join(user_path, f)
				print(feature_file)
				file = open(feature_file, "r", encoding='utf-8')
				lines = file.readlines()
				file.close()
				sp = 1
				sum, cnt = 0, 0
				while sp + feature_num <= len(lines):
					feature = []
					for i in range(feature_num):
						if used_feature[i % len(used_feature)] == 1:
							feature.append(float(lines[sp + i]))
					res = voice_model.predict([feature])
					sum += res[0]
					cnt += 1
					sp += feature_num
				print(sum / cnt)


if __name__ == "__main__":
	# calc_features()
	classification()
