import os
import math
import numpy as np
import data_reader
import webrtcvad_utils


def skewness_kurtosis_energy(data):
	n = len(data)
	if n <= 1:
		return [0, 3, 0]
	EX, EX2, EX3 = 0, 0, 0
	for a in data:
		EX += a
		EX2 += a*a
		EX3 += a**3
	EX /= n
	EX2 /= n
	EX3 /= n
	energy = EX2
	miu = EX
	sigma = math.sqrt(EX2 - EX * EX)
	if sigma == 0:
		return [0, 3, energy]
	skew = (EX3 - 3*miu*sigma**2 - miu**3) / sigma**3
	EX_minus_miu4 = 0
	for a in data:
		EX_minus_miu4 += (a - miu) ** 4
	EX_minus_miu4 /= n
	kurt = EX_minus_miu4 / sigma ** 4
	return [skew, kurt, energy]


def output_sensor_feature(data, output, sensor_name, start_time, end_time):
	frame_list = data.get_list(sensor_name)
	values = frame_list.get_data()
	arr = [[] for i in range(len(values))]
	t = frame_list.time_stamp
	for i in range(len(t)):
		if t[i] < start_time:
			continue
		if t[i] > end_time:
			break
		for v in range(len(values)):
			arr[v].append(values[v][i])
	n = len(arr[0])
	if n > 0:
		for v in range(len(values)):
			output.write(str(np.mean(arr[v])) + '\n')
			output.write(str(np.std(arr[v], ddof=0)) + '\n')
			output.write(str(np.max(arr[v])) + '\n')
			output.write(str(np.min(arr[v])) + '\n')
			output.write(str(np.median(arr[v])) + '\n')
			[skew, kurt, energy] = skewness_kurtosis_energy(arr[v])
			output.write(str(energy) + '\n')
			output.write(str(skew) + '\n')
			output.write(str(kurt) + '\n')
	else:
		for v in range(len(values)):
			for i in range(7):
				output.write('0\n')
			output.write('3\n')

	if sensor_name == 'PROXIMITY':
		return
	if n > 0:
		for i in range(len(values)):
			for j in range(i+1, len(values)):
				EXY = 0
				for k in range(n):
					EXY += arr[i][k] * arr[j][k]
				EXY /= n
				CovXY = EXY - np.mean(arr[i]) * np.mean(arr[j])
				CorrXY = CovXY / (np.std(arr[i], ddof=1) * np.std(arr[j], ddof=1))
				output.write(str(CorrXY) + '\n')
	else:
		for i in range(len(values)):
			for j in range(len(values)):
				output.write('0\n')


def extract_feature(start_time, end_time, data, output):
	start_time *= 1000
	end_time *= 1000
	output.write(str(start_time) + "\n")
	output.write(str(end_time) + "\n")
	s, e = start_time, end_time
	m = (s + e) / 2
	output_sensor_feature(data, output, "LINEAR_ACCELERATION", s, m)
	output_sensor_feature(data, output, "LINEAR_ACCELERATION", m, e)
	output_sensor_feature(data, output, "GYROSCOPE", s, m)
	output_sensor_feature(data, output, "GYROSCOPE", m, e)
	output_sensor_feature(data, output, "PROXIMITY", s, m)
	output_sensor_feature(data, output, "PROXIMITY", m, e)
	'''
	output_sensor_feature(data, output, "LINEAR_ACCELERATION", start_time, end_time)
	output_sensor_feature(data, output, "GYROSCOPE", start_time, end_time)
	output_sensor_feature(data, output, "PROXIMITY", start_time, end_time)
	'''


def find_suitable_end(t, l, r):
	for i in range(0, len(t), 2):
		if l <= t[i] <= r:
			return t[i]
	return l


def calc_data(file_name, file_dir, out_dir):
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

	task = int(d.task_id.split("_")[0])
	if task < 32 or d.description == '接听':
		t = webrtcvad_utils.calc_vad(3, os.path.join(file_dir, file_name + ".wav"))
		print(t)
		if d.start_pos == '裤兜':
			end = find_suitable_end(t, 5.0, 10.0)
		else:
			end = find_suitable_end(t, 2.0, 4.0)
		extract_feature(end - 2.0, end, d, output)

	else:
		max_time = d.get_max_time() / 1000
		start = 1.0
		while start + 2.5 < max_time:
			extract_feature(start, start + 2.0, d, output)
			start += 2.0
	'''
	if task < 32:
		t = webrtcvad_utils.calc_vad(3, os.path.join(file_dir, file_name + ".wav"))
		print(t)
		if len(t) == 0 or t[0] < 0.40:
			if len(t) > 2 and t[2] > 0.40:
				extract_feature(0, t[2], d, output)
			else:
				extract_feature(0, 0.8, d, output)
		else:
			extract_feature(0, t[0], d, output)
	else:
		max_time = d.get_max_time()

		sp = (max_time / 1000 - 1) / 5
		for i in range(5):
			extract_feature(i * sp + 0.5, (i + 1) * sp + 0.5, d, output)
	'''


data_path = '../Data/Study1/'
feature_path = '../Data/feature/'
user_list = os.listdir(data_path)
for u in user_list:
	# if u != "plh":
		# continue
	p = os.path.join(data_path, u)
	out_dir = os.path.join(feature_path, u)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
	files = os.listdir(p)
	for f in files:
		if f[-4:] == ".txt":
			calc_data(f[:-4], p, out_dir)