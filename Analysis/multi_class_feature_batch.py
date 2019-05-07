import os
import wave
import struct
import numpy as np
import data_reader
import capa_feature
import voice_feature
import motion_feature
import webrtcvad_utils
from multi_class_feature import get_vad_chunks

data_path = '../Data/multi-class/users/'
voice_data_path = '../Data/multi-class/32000 Hz stereo/'

feature_path = '../Data/multi-class/features/'
calc_motion, calc_capa, calc_voice = True, True, True

# ms
#time_point = [-1000, -900, -800, -700, -600, -500, -400, -300, -200, -100, 0,
#			  100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
# time_point = [1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]
time_point = [2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000]


def find_suitable_end(t, l, r):
	for i in range(0, len(t), 2):
		if l <= t[i] <= r:
			return t[i], t[i+1]
	return l, r


def extract_motion_feature(start_time, end_time, voice_end, data, time_delta):
	start_time *= 1000
	end_time *= 1000
	voice_end *= 1000
	s, e = start_time, end_time + time_delta
	if e > voice_end:
		e = voice_end
	dir_name = 'motion features (' + str(time_delta) + 'ms)'
	motion_out_path = os.path.join(feature_path, dir_name, u)
	if not os.path.exists(motion_out_path):
		os.makedirs(motion_out_path)
	out_file = os.path.join(motion_out_path, data.task_id + '.txt')
	output = open(out_file, 'w', encoding='utf-8')
	output.write(data.user_pos + '\n')
	output.write(data.start_pos + '\n')
	output.write(data.description + '\n')
	output.write(data.hand + '\n')
	output.write(str(start_time) + ' ' + str(s) + "\n")
	output.write(str(end_time) + ' ' + str(e) + "\n")
	if e - s <= 100:
		output.write('Discarded due to short time interval (<= 100ms)')
		return
	feature = []
	sensor_list = ['ACCELEROMETER', 'LINEAR_ACCELERATION', 'GRAVITY', 'GYROSCOPE', 'PROXIMITY']
	for sensor in sensor_list:
		f = motion_feature.extract_time_feature(data, sensor, s, e)
		# f.extend(motion_feature.extract_time_feature(data, sensor, e, e + 0.5 * 1000))
		output.write(sensor + ' ' + str(len(f)) + ' ')
		feature.extend(f)
	output.write('\n')
	for f in feature:
		output.write(str(f) + '\n')
	output.close()


def extract_capa_feature(start_time, end_time, voice_end, data, time_delta):
	start_time *= 1000
	end_time *= 1000
	voice_end *= 1000
	s, e = start_time, end_time + time_delta
	if e > voice_end:
		e = voice_end
	dir_name = 'capa features (' + str(time_delta) + 'ms)'
	capa_out_path = os.path.join(feature_path, dir_name, u)
	if not os.path.exists(capa_out_path):
		os.makedirs(capa_out_path)
	out_file = os.path.join(capa_out_path, data.task_id + '.txt')
	output = open(out_file, 'w', encoding='utf-8')

	if e - s <= 100:
		output.write('Discarded due to short time interval (<= 100ms)')
		return

	feature = capa_feature.extract_time_feature_count_appearance_only(data, s, e)
	for f in feature:
		output.write(str(f) + '\n')
	output.close()


def calc_motion_capa_data(file_name, file_dir):
	d = data_reader.Data()
	d.read(os.path.join(file_dir, file_name + '.txt'))
	print(u, d.task_id)

	t = get_vad_chunks(file_dir, file_name)
	end, voice_end = find_suitable_end(t, 0.4, 4.0)

	if calc_motion:
		for t in time_point:
			extract_motion_feature(0.05, end, voice_end, d, t)

	if calc_capa:
		for t in time_point:
			extract_capa_feature(0.05, end, voice_end, d, t)


def calc_voice_data(file_name, file_dir):
	f = open(os.path.join(file_dir, file_name + ".txt"), "r", encoding='utf-8')
	line = f.readline()
	task_id = line.strip().replace("/", "_").replace(":", "_").replace(" ", "")

	wav_file = os.path.join(voice_data_path + '/' + u, file_name + '.wav')
	try:
		wavefile = wave.open(wav_file, 'r')
	except wave.Error:
		return
	numframes, framerate = wavefile.getnframes(), wavefile.getframerate()

	y = np.zeros((2, numframes))

	for i in range(numframes):
		val = wavefile.readframes(1)
		left, right = val[0:2], val[2:4]
		y[0][i] = struct.unpack('h', left)[0]
		y[1][i] = struct.unpack('h', right)[0]

	t = get_vad_chunks(file_dir, file_name)
	end, voice_end = find_suitable_end(t, 0.4, 4.0)

	for time_delta in time_point:
		if time_delta > 0:
			s = int(framerate * end)
			if end + time_delta / 1000 > voice_end:
				t = int(framerate * voice_end)
			else:
				t = int(framerate * (end + time_delta / 1000))
			feature = voice_feature.extract_voice_features(y[0][s:t], y[1][s:t])
			dir_name = 'voice features (' + str(time_delta) + 'ms)'
			voice_out_path = os.path.join(feature_path, dir_name, u)
			if not os.path.exists(voice_out_path):
				os.makedirs(voice_out_path)
			out_file = os.path.join(voice_out_path, task_id + '.txt')
			output = open(out_file, 'w', encoding='utf-8')
			for f in feature:
				output.write(str(f) + '\n')


if __name__ == "__main__":
	for u in os.listdir(data_path):
		p = os.path.join(data_path, u)
		for f in os.listdir(p):
			if f.endswith('.txt') and not f.endswith('_vad.txt'):
				if calc_motion or calc_capa:
					calc_motion_capa_data(f[:-4], p)
				if calc_voice:
					calc_voice_data(f[:-4], p)
