import os
import math
import numpy as np
import data_reader
import webrtcvad_utils


def sgn(x):
	if x > 0:
		return 1
	elif x < 0:
		return -1
	else:
		return 0


def statical_signal_feature(data):
	# mean, min, max, median, standard deviation, IQR: interquartile range
	# ZCR: Zero-Crossing Rate, energy, skew: skewness, kurt: kurtosis
	# 6 + 4 = 10 features
	n = len(data)
	feature = []
	if n == 0:
		for i in range(9):
			feature.append(0)
		feature.append(3)
		return feature
	EX = np.mean(data)
	if n > 1:
		std = np.std(data, ddof=1)
	else:
		std = 0
	q75, q25 = np.percentile(data, [75, 25])
	IQR = q75 - q25

	feature.append(EX)
	feature.append(np.min(data))
	feature.append(np.max(data))
	feature.append(np.median(data))
	feature.append(std)
	feature.append(IQR)

	EX2, EX3, EX_minus_miu4, ZCR = 0, 0, 0, 0

	for i in range(len(data)):
		EX2 += data[i] ** 2
		EX3 += data[i] ** 3
		EX_minus_miu4 += (data[i] - EX) ** 4
		if i > 0 & sgn(data[i-1]) * sgn(data[i]) == -1:
			ZCR += 1
	EX2 /= n
	EX3 /= n
	EX_minus_miu4 /= n
	if n > 1:
		ZCR /= n - 1
	energy = EX2
	skew, kurt = 0, 3
	if std > 0:
		skew = (EX3 - 3 * EX * std ** 2 - EX ** 3) / std ** 3
		kurt = EX_minus_miu4 / std ** 4

	feature.append(ZCR)
	feature.append(energy)
	feature.append(skew)
	feature.append(kurt)
	return feature


def heuristic_feature(arr):
	n = len(arr[0])
	feature = []
	for i in range(len(arr)):
		for j in range(i+1, len(arr)):
			if n > 1:
				EXY = 0
				for k in range(n):
					EXY += arr[i][k] * arr[j][k]
				EXY /= n
				CovXY = EXY - np.mean(arr[i]) * np.mean(arr[j])
				try:
					CorrXY = CovXY / (np.std(arr[i], ddof=1) * np.std(arr[j], ddof=1))
				except RuntimeWarning:
					CorrXY = 0
				if math.isnan(CorrXY) or math.isinf(CorrXY):
					CorrXY = 0
				feature.append(CorrXY)
			else:
				feature.append(0)
	return feature


def extract_sensor_feature(arr, sensor_name):
	feature = []
	for v in range(len(arr)):
		feature.extend(statical_signal_feature(arr[v]))
	heuristic_sensors = ['ACCELEROMETER', 'LINEAR_ACCELERATION', 'GRAVITY', 'GYROSCOPE']
	if sensor_name not in heuristic_sensors:
		return feature
	feature.extend(heuristic_feature(arr))
	return feature


def extract_time_feature(data, sensor_name, start_time, end_time):
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
	return extract_sensor_feature(arr, sensor_name)


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
		# f = extract_time_feature(data, sensor, s, e)

		# 2s
		f = extract_time_feature(data, sensor, s, m)
		f.extend(extract_time_feature(data, sensor, m, e))

		output.write(sensor + ' ' + str(len(f)) + ' ')
		feature.extend(f)
	output.write('\n')
	for f in feature:
		output.write(str(f) + '\n')


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

	'''
	# 1s
	if task < 32 or d.description == '接听':
		t = webrtcvad_utils.calc_vad(3, os.path.join(file_dir, file_name + ".wav"))
		print(t)
		if d.start_pos == '裤兜':
			end = find_suitable_end(t, 4.0, 10.0)
		else:
			end = find_suitable_end(t, 1.0, 4.0)
		extract_feature(end - 1.0, end, d, output)
	else:
		max_time = d.get_max_time() / 1000
		start = 2.0
		while start + 2.5 < max_time:
			extract_feature(start, start + 1.0, d, output)
			start += 2.0

	'''
	# 2s
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



if __name__ == "__main__":
	data_path = '../Data/Study1/'
	feature_path = '../Data/motion feature/'
	user_list = os.listdir(data_path)
	for u in user_list:
		p = os.path.join(data_path, u)
		out_dir = os.path.join(feature_path, u)
		if not os.path.exists(out_dir):
			os.makedirs(out_dir)
		files = os.listdir(p)
		for f in files:
			if f[-4:] == ".txt":
				calc_data(f[:-4], p, out_dir)
