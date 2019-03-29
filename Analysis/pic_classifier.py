import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn import tree
from sklearn import svm
from sklearn import neighbors
from sklearn.externals import joblib
from sklearn.ensemble import AdaBoostClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split

positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
            '竖屏握持，上端遮嘴',  # '水平端起，倒话筒',
            #'话筒', '横屏',
			'左耳打电话（不碰）', '右耳打电话（不碰）',
			'左耳打电话（碰触）', '右耳打电话（碰触）']
# negative = ['大千世界', '自拍', '拍照', '手中', '打字', '浏览']
negative = ['自拍', '拍照', '手中', '打字', '浏览']


'''
positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
            '竖屏握持，上端遮嘴',  # '水平端起，倒话筒',
            '话筒']
negative = ['左耳打电话（不碰）', '右耳打电话（不碰）',
			'左耳打电话（碰触）', '右耳打电话（碰触）']
'''


def read_file(path, file_name, id):
	if file_name[-4:] != '.txt':
		return
	file = open(os.path.join(path, file_name), 'r', encoding='utf-8')
	lines = file.readlines()
	file.close()
	if len(lines) <= 2:
		return
	global X, y, task
	feature_num = int(lines[1])
	task_description = lines[0].strip()
	if task_description in positive:
		y_type = 1
	elif task_description in negative:
		y_type = 0
	else:
		return
	sp = 2
	while sp + feature_num <= len(lines):
		feature = []
		for i in range(feature_num):
			feature.append(float(lines[sp + i]))
		X[id].append(feature)
		y[id].append(y_type)
		task[id].append(task_description)
		sp += feature_num


def read_features(feature_path):
	user_list = os.listdir(feature_path)
	global X, y, task
	id = -1
	for u in user_list:
		if u[-4:] == '.txt':
			continue
		id += 1
		print('Reading', id, u)
		p = os.path.join(feature_path, u)
		files = os.listdir(p)
		X.append([])
		y.append([])
		task.append([])
		for f in files:
			read_file(p, f, id)
		if len(X[id]) == 0 or len(X[id]) <= 100: #or 0 not in y[id] or 1 not in y[id]:
			X.pop(), y.pop(), task.pop()
			id -= 1


def fit_model():
	X_all, y_all, t_all = [], [], []
	for i in range(len(X)):
		X_all.extend(X[i])
		y_all.extend(y[i])
		t_all.extend(task[i])
	X_all, y_all = np.array(X_all), np.array(y_all)
	print(X_all.shape, y_all.shape)
	clf = svm.SVC(kernel='rbf', gamma='scale', class_weight={0: 1, 1: 1}, probability=True)
	# clf = tree.DecisionTreeClassifier(max_depth=10, class_weight={0: 1, 1: 1})
	clf.fit(X_all, y_all)
	print(clf.score(X_all, y_all))

	X_train, X_test, y_train, y_test = train_test_split(X_all, y_all, test_size=0.2)
	clf.fit(X_train, y_train)
	print(clf.score(X_train, y_train))
	print(clf.score(X_test, y_test))

	total, correct = {}, {}
	for t in positive + negative:
		total[t] = 0
		correct[t] = 0
	res = clf.predict(X_all)
	for i in range(len(X_all)):
		t = t_all[i]
		total[t] += 1
		if res[i] == y_all[i]:
			correct[t] += 1
	for t in correct:
		print(t.ljust(24 - len(t)), correct[t], '/', total[t], correct[t] / total[t])

	cnt = np.zeros((2, 100 + 1))
	proba = clf.predict_proba(X_all)
	for i in range(len(X_all)):
		for res in range(2):
			if proba[i][res] > 0.5:
				if res == y_all[i]:
					same = 1
				else:
					same = 0
				p = int(proba[i][res] / 0.01)
				cnt[same][p] += 1
	x_range = np.linspace(50, 100, 51)
	plt.plot(x_range, cnt[0][50:], label='error')
	plt.plot(x_range, cnt[1][50:], label='correct')
	plt.legend()
	plt.show()


def leave_one_out_validation():

	correct, total = {}, {}
	for t in positive + negative:
		total[t], correct[t] = 0, 0
	mean_train_acc, mean_test_acc = 0, 0
	for loo in range(len(X)):
		print(loo)
		X_train, y_train = [], []
		for i in range(len(X)):
			if i != loo:
				X_train.extend(X[i])
				y_train.extend(y[i])
		X_test, y_test = X[loo], y[loo]
		X_train, X_test = np.array(X_train), np.array(X_test)
		y_train, y_test = np.array(y_train), np.array(y_test)
		print(X_train.shape, y_train.shape, X_test.shape, y_test.shape)
		# clf = svm.SVC(kernel='rbf', gamma=1e-3, class_weight={0: 1, 1: 1})
		clf = tree.DecisionTreeClassifier(max_depth=8, class_weight={0: 1, 1: 1})
		clf.fit(X_train, y_train)

		train_acc = clf.score(X_train, y_train)
		test_acc = clf.score(X_test, y_test)
		mean_train_acc += train_acc
		mean_test_acc += test_acc
		print(train_acc, test_acc)

		res = clf.predict(X_test)
		for i in range(len(res)):
			t = task[loo][i]
			total[t] += 1
			if res[i] == y[loo][i]:
				correct[t] += 1

	print('Mean')
	print(mean_train_acc / len(X))
	print(mean_test_acc / len(X))

	for t in correct:
		print(t.ljust(24 - len(t)), correct[t], '/', total[t], correct[t] / total[t])


if __name__ == '__main__':
	X, y, task = [], [], []
	read_features('../Data/pic feature/')
	fit_model()
	# leave_one_out_validation()
