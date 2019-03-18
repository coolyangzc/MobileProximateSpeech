import os
import numpy as np
from sklearn import tree
from sklearn import svm
from sklearn.externals import joblib
from sklearn.ensemble import AdaBoostClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split


def read_file(path, file_name, id):
	if file_name[-4:] != ".txt":
		return
	file = open(os.path.join(path, file_name), "r", encoding='utf-8')
	lines = file.readlines()
	file.close()
	if len(lines) <= 7:
		return
	task_id = int(file_name.strip().split('_')[0])
	if 19 <= task_id <= 22:
		return
	global X, y, task
	f_dim = lines[6].split(' ')
	feature_num = 0
	for i in range(1, len(f_dim), 2):
		feature_num += int(f_dim[i])
	task_description = lines[2].strip()
	if task_id < 32:
		feature = []
		for i in range(7, 7 + feature_num):
			feature.append(float(lines[i]))
		X[id].append(feature)
		y[id].append(1)
		task[id].append(task_description)
	else:
		if task_description == '接听':
			return
		sp = 7
		while sp + feature_num <= len(lines):
			feature = []
			for i in range(feature_num):
				feature.append(float(lines[sp + i]))
			X[id].append(feature)
			# if lines[2] == '接听\n':
			#	y[id].append(2)
			# else:
			y[id].append(0)
			task[id].append(task_description)
			sp += feature_num + 3


def read_features(feature_path):
	user_list = os.listdir(feature_path)
	global X, y, task
	id = -1
	for u in user_list:
		if u[-4:] == '.txt':
			continue
		print('Reading', u)
		if u == 'tqy':
			continue
		p = os.path.join(feature_path, u)
		files = os.listdir(p)
		X.append([])
		y.append([])
		task.append([])
		id += 1
		for f in files:
			read_file(p, f, id)


def data_normalization():
	global X
	X_all = []
	for i in range(len(X)):
		X_all.extend(X[i])
	# scaler = RobustScaler()
	scaler = StandardScaler()
	scaler.fit(X_all)
	for i in range(len(X)):
		X[i] = scaler.transform(X[i])


def generate_model():
	X_all, y_all = [], []
	for i in range(len(X)):
		X_all.extend(X[i])
		y_all.extend(y[i])
	clf = svm.SVC(kernel='rbf', gamma=1e-4, class_weight={0: 1, 1: 1})
	clf.fit(X_all, y_all)
	joblib.dump(clf, "my_model.m")
	print(clf.score(X_all, y_all))


def leave_one_out_validation():
	mean_train_acc, mean_test_acc = 0, 0

	total, correct = {}, {}

	for loo in range(len(X)):
		print(loo)
		X_train = []
		y_train = []
		for i in range(len(X)):
			if i != loo:
				X_train.extend(X[i])
				y_train.extend(y[i])
		X_test, y_test = X[loo], y[loo]
		X_train, X_test = np.array(X_train), np.array(X_test)
		y_train, y_test = np.array(y_train), np.array(y_test)
		print(X_train.shape, y_train.shape)
		# clf = AdaBoostClassifier()
		clf = svm.SVC(kernel='rbf', gamma=1e-3, class_weight={0: 1, 1: 1})
		# clf = tree.DecisionTreeClassifier(max_depth=5)
		clf.fit(X_train, y_train)

		train_acc = clf.score(X_train, y_train)
		test_acc = clf.score(X_test, y_test)
		mean_train_acc += train_acc
		mean_test_acc += test_acc
		res = clf.predict(X[loo])
		print(res)
		same = []
		for i in range(len(res)):
			t = task[loo][i]
			if t not in total:
				total[t] = 0
			total[t] += 1
			if res[i] == y[loo][i]:
				if t not in correct:
					correct[t] = 0
				same.append(1)
				correct[t] += 1
			else:
				same.append(0)
		print(same)
		print(train_acc)
		print(test_acc)

	print('Mean')
	print(mean_train_acc / len(X))
	print(mean_test_acc / len(X))

	for t in correct:
		print(t.ljust(24 - len(t)), correct[t], '/', total[t], correct[t] / total[t])


if __name__ == "__main__":
	X, y, task = [], [], []
	read_features('../Data/feature/')
	data_normalization()
	# generate_model()
	leave_one_out_validation()

