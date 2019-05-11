import os
import math
import numpy as np

data_path = '../Data/Field Study/trimmed/'
phone_path = os.path.join(data_path, 'phone')

have_files = []
orig_trigger, linear_z_pass = [], []
sum_orig, sum_linear = 0, 0


def analyze_user(user):
	global sum_orig, sum_linear, sum_try
	user_path = os.path.join(phone_path, user)
	have_files.append(np.zeros(11))
	orig_trigger.append(np.zeros(11))
	linear_z_pass.append(np.zeros(11))
	file_cnt, task_cnt = 0, 0
	user_id = int(user.split(' ')[0])
	for f in os.listdir(user_path):
		if not f.endswith('.txt'):
			continue
		file_cnt += 1
		file = open(os.path.join(user_path, f), "r", encoding='utf-8')
		lines = file.readlines()
		task_id = int(lines[0].split(' ')[0])
		if have_files[-1][task_id] == 0:
			task_cnt += 1
			have_files[-1][task_id] = 1

		max_linear_z = -100
		for line in lines:
			data = line.split(' ')
			if data[0] == 'TRIGGER':
				orig_trigger[-1][task_id] = 1
			if data[0] == 'LINEAR_ACCELERATION':
				max_linear_z = max(max_linear_z, float(data[5]))

		if max_linear_z <= 3:
			linear_z_pass[-1][task_id] = 1

	if file_cnt != 11 or task_cnt != 11:
		print('Warning: ', user, 'file_cnt =', file_cnt, 'task_cnt =', task_cnt)

	min_happen = -1
	orig, linear = 0, 0
	for t in range(1, 11):
		orig += int(orig_trigger[-1][t])
		if orig_trigger[-1][t] == 1 or (linear_z_pass[-1][t] == 1 and user_id <= 19):
			linear += 1
			if min_happen == -1:
				min_happen = t
		else:
			print('no motion triggered:', user, t)

	sum_orig += orig
	sum_linear += linear
	print(user, orig, linear, min_happen)


if __name__ == "__main__":
	user_list = os.listdir(phone_path)
	user_num = len(user_list)
	for u in user_list:
		analyze_user(u)
	print(user_num)
	print(sum_orig / user_num)
	print(sum_linear / user_num)