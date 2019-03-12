import os
import numpy as np
import data_reader
import webrtcvad_utils


def extract_feature(start_time, end_time, data, output):
	start_time *= 1000
	end_time *= 1000
	output.write(str(start_time) + "\n")
	output.write(str(end_time) + "\n")

	frame_list = data.get_list("LINEAR_ACCELERATION")

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
	for v in range(len(values)):
		output.write(str(np.mean(arr[v])) + '\n')
	for v in range(len(values)):
		output.write(str(np.std(arr[v])) + '\n')


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
	if task < 32:
		t = webrtcvad_utils.calc_vad(3, os.path.join(file_dir, file_name + ".wav"))
		print(t)
		if len(t) == 0 or t[0] < 0.30:
			if len(t) > 2:
				extract_feature(0, t[2], d, output)
			else:
				extract_feature(0, 0.8, d, output)
		else:
			extract_feature(0, t[0], d, output)
	else:
		max_time = d.get_max_time()
		sp = max_time / 5 / 1000
		for i in range(5):
			extract_feature(i * sp, (i + 1) * sp, d, output)


data_path = '../Data/Study1/'
feature_path = '../Data/feature/'
user_list = os.listdir(data_path)
for u in user_list:
	#if u != "yzc" and u != "plh":
	if u != "plh":
		continue
	p = os.path.join(data_path, u)
	out_dir = os.path.join(feature_path, u)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
	files = os.listdir(p)
	for f in files:
		if f[-4:] == ".txt":
			calc_data(f[:-4], p, out_dir)
