import os
import numpy as np
from sklearn import svm
from sklearn import tree
from sklearn.preprocessing import StandardScaler

feature_path = '../Data/multi-class/features/'
category = ['竖屏握持，上端遮嘴', '水平端起，倒话筒', '耳旁打电话', '横屏',
			'竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子', '话筒']

# ms
minimum_available_data_time = 200
time_point = [-1000, -900, -800, -700, -600, -500, -400, -300, -200, -100, 0,
			  100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

X, y, task = [], [], []
res = np.zeros((len(category) + 1, len(time_point)))
use_motion, use_capa, use_voice = True, True, True


def read_files(file_name, id, motion_path, capa_path, voice_path):
	if not file_name.endswith('.txt'):
		return
	file = open(os.path.join(motion_path, file_name), "r", encoding='utf-8')
	lines = file.readlines()
	file.close()
	s, t = float(lines[4].split(' ')[1]), float(lines[5].split(' ')[1])
	if len(lines) <= 8 or t - s <= minimum_available_data_time:
		return

	feature = []
	global X, y, task
	f_dim = lines[6].split(' ')
	feature_num = 0
	for i in range(1, len(f_dim), 2):
		feature_num += int(f_dim[i])
	task_description = lines[2].strip()

	y_type = -1
	for i in range(len(category)):
		if task_description == category[i]:
			y_type = i
			break
	if y_type == -1:
		print('Warning: unknown task:' + task_description, file_name)
		return

	if use_motion:
		for i in range(7, 7 + feature_num):
			feature.append(float(lines[i]))

	if use_voice and time_delta > 0:
		file = open(os.path.join(voice_path, file_name), "r", encoding='utf-8')
		lines = file.readlines()
		file.close()
		for i in range(len(lines)):
			feature.append(float(lines[i]))

	if use_capa:
		file = open(os.path.join(capa_path, file_name), "r", encoding='utf-8')
		lines = file.readlines()
		file.close()
		for i in range(len(lines)):
			feature.append(float(lines[i]))

	X[id].append(feature)
	y[id].append(y_type)
	task[id].append(task_description)


def read_features():
	global X, y, task
	id = -1
	appendix = '(' + str(time_delta) + 'ms)'
	user_path = os.path.join(feature_path, 'motion features ' + appendix)

	for u in os.listdir(user_path):
		if u.endswith('.txt'):
			continue
		print('Reading', u)
		p = os.path.join(user_path, u)
		files = os.listdir(p)
		X.append([])
		y.append([])
		task.append([])
		id += 1
		motion_path = os.path.join(feature_path, 'motion features ' + appendix, u)
		capa_path = os.path.join(feature_path, 'capa features ' + appendix, u)
		voice_path = os.path.join(feature_path, 'voice features ' + appendix, u)
		for f in files:
			read_files(f, id, motion_path, capa_path, voice_path)


def leave_one_out_validation(classes):
	print(str(time_delta) + 'ms,', classes, 'classes:')

	mean_train_acc, mean_test_acc = 0, 0
	for loo in range(len(X)):
		print(loo, end=' ', flush=True)
		X_train, X_test, y_train, y_test = [], [], [], []
		for i in range(len(X)):
			for j in range(len(X[i])):
				if y[i][j] < classes:
					if i != loo:
						X_train.append(X[i][j])
						y_train.append(y[i][j])
					else:
						X_test.append(X[i][j])
						y_test.append(y[i][j])
		X_train, X_test = np.array(X_train), np.array(X_test)
		y_train, y_test = np.array(y_train), np.array(y_test)
		# print(X_train.shape, y_train.shape)

		clf = svm.SVC(kernel='rbf', gamma='auto', class_weight='balanced')

		clf.fit(X_train, y_train)
		train_acc = clf.score(X_train, y_train)
		test_acc = clf.score(X_test, y_test)
		# print(train_acc)
		# print(test_acc)
		mean_train_acc += train_acc
		mean_test_acc += test_acc
	print('')
	print(mean_train_acc / len(X))
	print(mean_test_acc / len(X))
	print('')
	res[classes][t] = mean_test_acc / len(X)


def data_normalization():
	global X
	X_all = []
	for i in range(len(X)):
		X_all.extend(X[i])
	scaler = StandardScaler()
	scaler.fit(X_all)
	for i in range(len(X)):
		X[i] = scaler.transform(X[i])


def clear():
	global X, y, task
	X, y, task = [], [], []


def save_results():
	out_file = feature_path + 'classes_results.csv'
	output = open(out_file, 'w', encoding='utf-8-sig')
	output.write('class_num')
	for t in time_point:
		output.write(',' + str(t))
	output.write('\n')
	for classes in range(2, len(category) + 1):
		output.write(str(classes))
		for i in range(len(time_point)):
			output.write(',' + str(res[classes][i]))
		output.write('\n')
	output.close()


if __name__ == "__main__":
	print(len(category))
	for t in range(len(time_point)):
		time_delta = time_point[t]
		print('Calc', time_delta, 'ms')
		read_features()
		data_normalization()
		for classes in range(2, len(category) + 1):
			leave_one_out_validation(classes)
		clear()
	save_results()
