import os
import math
import wave
import struct
import numpy as np

sample_rate = 32000
interval_size = 6400
stride = 0.5
feature_num = 32


def extract_voice_features(left, right):
	data = [[] for i in range(4)]
	n = len(left)
	data[0], data[1] = abs(left), abs(right)
	a, b = 1, 1
	for i in range(n):
		data[2].append(data[0][i] - data[1][i])
		if data[0][i] > 0:
			a = data[0][i]
		if data[1][i] > 0:
			b = data[1][i]
		data[3].append(a / b)

	feature = []
	for i in range(4):
		feature.append(np.min(data[i]))
		feature.append(np.max(data[i]))
		feature.append(np.median(data[i]))
		feature.append(np.mean(data[i]))
		feature.append(np.std(data[i], ddof=1))
		q75, q25 = np.percentile(data[i], [75, 25])
		IQR = q75 - q25
		feature.append(IQR)
		feature.append(np.mean(np.array(data[i]) ** 2))
		feature.append(math.sqrt(np.mean(np.array(data[i]) ** 2)))
	return feature


def calc_features(wav_file):
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

	s = 0
	while s + interval_size < numframes:
		feature = extract_voice_features(y[0][s:s + interval_size], y[1][s:s + interval_size])
		for f in feature:
			output.write(str(f) + '\n')
		s += int(interval_size * stride)


if __name__ == "__main__":
	path = '../Data/Trimmed Stereo 32000Hz/'
	feature_path = '../Data/voice feature/'
	for u in os.listdir(path):
		user_path = os.path.join(path, u)
		out_path = os.path.join(feature_path, u)
		if not os.path.exists(out_path):
			os.makedirs(out_path)
		for f in os.listdir(user_path):
			if f.find('.') == -1:
				print(u, f)
				chunk_path = os.path.join(user_path, f)
				description_file = os.path.join(user_path, f + '.txt')
				file = open(description_file, "r", encoding='utf-8')
				lines = file.readlines()
				task_id = lines[0].strip().replace("/", "_").replace(":", "_").replace(" ", "")
				out_file = os.path.join(out_path, task_id + ".txt")
				output = open(out_file, 'w', encoding='utf-8')
				output.truncate()
				output.write(lines[1])
				output.write(lines[2])
				output.write(str(feature_num) + '\n')
				for wav in os.listdir(chunk_path):
					calc_features(os.path.join(chunk_path, wav))
