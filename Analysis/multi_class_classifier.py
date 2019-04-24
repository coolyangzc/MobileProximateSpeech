import os
import numpy as np
from sklearn import svm
from sklearn import tree
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import AdaBoostClassifier

feature_path = '../Data/multi-class/features'
# feature_path = '../Data/multi-class/features (motion, 162 dimensions)'

all_category = []
user_list = []

X, y, task = [], [], []


def set_category():
	global all_category

	# motion
	all_category = [['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子', '竖屏握持，上端遮嘴', '话筒'],
					['水平端起，倒话筒'],
					['耳旁打电话'],
					['横屏']]
	'''
	# voice
	all_category = [['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子'],
					['竖屏握持，上端遮嘴', '话筒'],
					['水平端起，倒话筒', '耳旁打电话'],
					['横屏']]
	'''


def read_file(path, file_name, id):
	if not file_name.endswith('.txt'):
		return
	file = open(os.path.join(path, file_name), "r", encoding='utf-8')
	lines = file.readlines()
	file.close()
	if len(lines) <= 7:
		return

	global X, y, task
	f_dim = lines[6].split(' ')
	feature_num = 0
	for i in range(1, len(f_dim), 2):
		feature_num += int(f_dim[i])
	task_description = lines[2].strip()

	y_type = -1
	for i in range(len(all_category)):
		if task_description in all_category[i]:
			y_type = i
			break
	if y_type == -1:
		print('Warning: unknown task:' + task_description, file_name)
		return
	feature = []
	for i in range(7, 7 + feature_num):
		feature.append(float(lines[i]))
	# feature = feature[198:264]
	X[id].append(feature)
	y[id].append(y_type)
	task[id].append(task_description)


def read_features():
	global X, y, task, user_list
	id = -1
	for u in os.listdir(feature_path):
		if u.endswith('.txt'):
			continue
		print('Reading', u)
		user_list.append(u)
		p = os.path.join(feature_path, u)
		files = os.listdir(p)
		X.append([])
		y.append([])
		task.append([])
		id += 1
		for f in files:
			read_file(p, f, id)


def leave_one_out_validation():
	total, correct = {}, {}
	mean_train_acc, mean_test_acc = 0, 0
	category_n = len(all_category)
	confusion = np.zeros((category_n, category_n))

	for loo in range(len(X)):
		print(loo, user_list[loo])
		for c in all_category:
			for t in c:
				total[t], correct[t] = 0, 0
		X_train, y_train = [], []
		for i in range(len(X)):
			if i != loo:
				X_train.extend(X[i])
				y_train.extend(y[i])
		X_test, y_test = X[loo], y[loo]
		X_train, X_test = np.array(X_train), np.array(X_test)
		y_train, y_test = np.array(y_train), np.array(y_test)
		print(X_train.shape, y_train.shape)

		# clf = tree.DecisionTreeClassifier(max_depth=10)
		clf = svm.SVC(kernel='rbf', gamma=1e-3)
		# clf = AdaBoostClassifier(n_estimators=100)

		clf.fit(X_train, y_train)
		res = clf.predict(X[loo])
		train_acc = clf.score(X_train, y_train)
		test_acc = clf.score(X_test, y_test)
		print(train_acc)
		print(test_acc)
		mean_train_acc += train_acc
		mean_test_acc += test_acc

		for i in range(len(res)):
			t = task[loo][i]
			total[t] += 1
			if res[i] == y[loo][i]:
				correct[t] += 1
			confusion[y[loo][i]][res[i]] += 1
		print('-' * 20)

	print(feature_path)
	print('Mean')
	print(mean_train_acc / len(X))
	print(mean_test_acc / len(X))
	print('truth | predict')
	for i in range(category_n):
		tot = 0
		for j in range(category_n):
			tot += confusion[i][j]
		acc = confusion[i][i] / tot
		print(confusion[i], acc * 100)


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


if __name__ == "__main__":
	set_category()
	read_features()
	data_normalization()
	leave_one_out_validation()