import numpy as np


def extract_time_feature(data, start_time, end_time):
	frame_list = data.get_list('CAPACITY')
	values = frame_list.get_data()
	arr = [[] for i in range(len(values))]
	t = frame_list.time_stamp

	sum_capa = np.zeros((32, 18))
	cnt = 0
	for i in range(len(t)):
		if t[i] < start_time:
			continue
		if t[i] > end_time:
			break
		capa = np.zeros(32 * 18)
		for v in range(len(values)):
			arr[v].append(values[v][i])
			capa[v] = values[v][i]
		capa = capa.reshape((32, 18))
		for i in range(10):
			for j in range(18):
				if capa[i][j] >= 100:
					sum_capa[i][j] += capa[i][j]
		cnt += 1

	feature = []
	'''
	x_sum, y_sum, all_sum = 0, 0, 0
	for i in range(10):
		for j in range(18):
			x_sum += i * sum_capa[i][j]
			y_sum += j * sum_capa[i][j]
			all_sum += sum_capa[i][j]
	if all_sum == 0:
		feature = [0, 0, 0]
	else:
		x = x_sum / all_sum
		y = y_sum / all_sum
		feature = [1, x, y]
	'''
	for i in range(10):
		for j in range(18):
			if cnt > 0:
				feature.append(sum_capa[i][j] / cnt)
			else:
				feature.append(0)

	return feature
