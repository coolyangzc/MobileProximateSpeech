import os
import data_reader
import motion_feature
import webrtcvad_utils

data_path = '../Data/multi-class/users/'
feature_path = '../Data/multi-class/features/'


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

		f = motion_feature.extract_time_feature(data, sensor, s, e)
		f.extend(motion_feature.extract_time_feature(data, sensor, e, e + 0.5))

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


if __name__ == "__main__":
	for u in os.listdir(data_path):
		p = os.path.join(data_path, u)
		out_dir = os.path.join(feature_path, u)
		if not os.path.exists(out_dir):
			os.makedirs(out_dir)
		for f in os.listdir(p):
			if f.endswith('.txt') and not f.endswith('_vad.txt'):
				calc_motion_data(f[:-4], p, out_dir)
