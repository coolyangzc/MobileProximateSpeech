import os
import math
import wave
import struct
import numpy as np
import data_reader
import voice_feature
import motion_feature
import webrtcvad_utils

data_path = '../Data/multi-class/users/'
voice_data_path = '../Data/multi-class/32000 Hz stereo/'
feature_path = '../Data/multi-class/features/'
voice_feature_path = '../Data/multi-class/voice features/'


def find_suitable_end(t, l, r):
	for i in range(0, len(t), 2):
		if l <= t[i] <= r:
			return t[i]
	return l


def extract_feature(start_time, end_time, data, output):
	start_time *= 1000
	end_time *= 1000
	output.write(str(start_time) + "\n")
	output.write(str(end_time) + "\n")
	s, e = start_time, end_time
	m = (s + e) / 2
	feature = []
	sensor_list = ['ACCELEROMETER', 'LINEAR_ACCELERATION', 'GRAVITY', 'GYROSCOPE', 'PROXIMITY']
	for sensor in sensor_list:
		# f = motion_feature.extract_time_feature(data, sensor, s, e)

		# 2s
		# f = motion_feature.extract_time_feature(data, sensor, s, m)
		# f.extend(motion_feature.extract_time_feature(data, sensor, m, e))

		# f = motion_feature.extract_time_feature(data, sensor, s, e)
		# f.extend(motion_feature.extract_time_feature(data, sensor, e, e + 0.5))

		f = motion_feature.extract_time_feature(data, sensor, s, e - 0.1)
		f.extend(motion_feature.extract_time_feature(data, sensor, e - 0.1, e))

		output.write(sensor + ' ' + str(len(f)) + ' ')
		feature.extend(f)
	output.write('\n')
	for f in feature:
		output.write(str(f) + '\n')


def get_vad_chunks(file_dir, file_name):
	vad_file = os.path.join(file_dir, file_name + '_vad.txt')
	if not os.path.exists(vad_file):
		t = webrtcvad_utils.calc_vad(3, os.path.join(file_dir, file_name + '.wav'))
		out_vad = open(vad_file, 'w', encoding='utf-8')
		for i in range(0, len(t), 2):
			out_vad.write(str(t[i]) + ' ' + str(t[i + 1]) + '\n')
		out_vad.close()

	f_vad = open(vad_file, "r", encoding='utf-8')
	lines = f_vad.readlines()
	f_vad.close()
	t = []
	for line in lines:
		data = line.strip().split(' ')
		t.append(float(data[0]))
		t.append(float(data[1]))
	return t


def calc_motion_data(file_name, file_dir, out_dir):
	print(file_name)
	d = data_reader.Data()
	d.read(os.path.join(file_dir, file_name + ".txt"))
	out_file = os.path.join(out_dir, d.task_id + ".txt")
	print(out_file)

	output = open(out_file, 'w', encoding='utf-8')
	output.write(d.user_pos + '\n')
	output.write(d.start_pos + '\n')
	output.write(d.description + '\n')
	output.write(d.hand + '\n')

	t = get_vad_chunks(file_dir, file_name)
	print(t)
	end = find_suitable_end(t, 0.4, 4.0)
	extract_feature(0.05, end, d, output)


def calc_voice_data(file_name, file_dir, user_name, voice_out_dir):
	f = open(os.path.join(file_dir, file_name + ".txt"), "r", encoding='utf-8')
	line = f.readline()
	task_id = line.strip().replace("/", "_").replace(":", "_").replace(" ", "")
	print(user_name, task_id)
	out_file = os.path.join(voice_out_dir, task_id + ".txt")
	output = open(out_file, 'w', encoding='utf-8')

	wav_file = os.path.join(voice_data_path + '/' + user_name, file_name + '.wav')
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

	t = get_vad_chunks(file_dir, file_name)
	print(t)
	end = find_suitable_end(t, 0.4, 4.0)

	interval_size = 3200
	stride = 0.5
	s = int(framerate * end)
	t = int(framerate * (end + 1.0))
	feature = voice_feature.extract_voice_features\
		(y[0][s:t], y[1][s:t])
	for f in feature:
		output.write(str(f) + '\n')

	'''
	while s + interval_size < numframes:
		feature = voice_feature.extract_voice_features\
			(y[0][s:s + interval_size], y[1][s:s + interval_size])
		for f in feature:
			output.write(str(f) + '\n')
		s += int(interval_size * stride)
	'''


if __name__ == "__main__":
	for u in os.listdir(data_path):
		p = os.path.join(data_path, u)
		out_dir = os.path.join(feature_path, u)
		if not os.path.exists(out_dir):
			os.makedirs(out_dir)
		voice_out_dir = os.path.join(voice_feature_path, u)
		if not os.path.exists(voice_out_dir):
			os.makedirs(voice_out_dir)
		for f in os.listdir(p):
			if f.endswith('.txt') and not f.endswith('_vad.txt'):
				calc_motion_data(f[:-4], p, out_dir)
				# calc_voice_data(f[:-4], p, u, voice_out_dir)
