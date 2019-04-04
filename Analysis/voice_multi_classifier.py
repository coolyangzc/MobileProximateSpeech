import os
import numpy as np
from sklearn import tree

path = '../Data/voice feature Stereo 32000 Hz 0.2s stride=50%/'

'''
all_category = [# ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子'],
				['竖屏握持，上端遮嘴', '话筒'],
				['水平端起，倒话筒'],
				['横屏'],
				['耳旁打电话']]
'''

all_category = [#['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子'],
				['竖直对脸，不碰鼻子'],
				['竖屏握持，上端遮嘴', '话筒'],
				['水平端起，倒话筒', '耳旁打电话']]
				# ['横屏']]

used_feature = [1, # min
				1, # max
				1, # median
				1, # mean
				1, # std
				1, # IQR
				1, # energy
				1] # RMS


def read_file(path, file_name, id):
	if file_name[-4:] != ".txt":
		return
	file = open(os.path.join(path, file_name), "r", encoding='utf-8')
	lines = file.readlines()
	file.close()
	if len(lines) <= 3:
		return
	task_id = int(file_name.strip().split('_')[0])
	global X, y, task, task_from
	feature_num = int(lines[2])
	task_description = lines[0].strip()
	volume = lines[1].strip()

	y_type = -1
	for i in range(len(all_category)):
		if task_description in all_category[i]:
			y_type = i
			break
	if y_type == -1:
		return
	if volume not in ['大声', '小声']:
		return
	sp = 3
	while sp + feature_num <= len(lines):
		feature = []
		for i in range(feature_num):
			if used_feature[i % len(used_feature)] == 1:
				feature.append(float(lines[sp + i]))
		X[id].append(feature)
		y[id].append(y_type)
		task[id].append(task_description)
		task_from[id].append(file_name)
		sp += feature_num


def read_features(feature_path):
	user_list = os.listdir(feature_path)
	global X, y, task, task_from
	id = -1
	for u in user_list:
		if not os.path.isdir(os.path.join(feature_path, u)):
			continue
		print('Reading', u)
		p = os.path.join(feature_path, u)
		files = os.listdir(p)
		X.append([])
		y.append([])
		task.append([])
		task_from.append([])
		id += 1
		for f in files:
			read_file(p, f, id)


def leave_one_out_validation():
	total, correct, total_vote, correct_vote = {}, {}, {}, {}
	mean_train_acc, mean_test_acc = 0, 0
	category_n = len(all_category)
	confusion, confusion_vote = np.zeros((category_n, category_n)), np.zeros((category_n, category_n))
	for loo in range(len(X)):
		print(loo)
		for c in all_category:
			for t in c:
				total[t], correct[t], total_vote[t], correct_vote[t] = 0, 0, 0, 0
		X_train, y_train = [], []
		for i in range(len(X)):
			if i != loo:
				X_train.extend(X[i])
				y_train.extend(y[i])
		X_test, y_test = X[loo], y[loo]
		X_train, X_test = np.array(X_train), np.array(X_test)
		y_train, y_test = np.array(y_train), np.array(y_test)
		print(X_train.shape, y_train.shape)
		clf = tree.DecisionTreeClassifier(max_depth=10)
		clf.fit(X_train, y_train)
		res = clf.predict(X[loo])
		res_proba = clf.predict_proba(X[loo])
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

		vote = np.zeros(category_n)
		task_from[loo].append('#')
		res = clf.predict_proba(X[loo])
		print(res)

		for i in range(len(res)):
			t = task[loo][i]
			for j in range(category_n):
				vote[j] += res[i][j]
			if task_from[loo][i] != task_from[loo][i + 1]:
				vote_res = np.argmax(vote)
				total_vote[t] += 1
				if vote_res == y[loo][i]:
					correct_vote[t] += 1
				confusion_vote[y[loo][i]][vote_res] += 1
				vote = np.zeros(category_n)


	print('Mean')
	print(mean_train_acc / len(X))
	print(mean_test_acc / len(X))
	print('truth | predict')
	for line in confusion:
		print(line)
	print('Vote')
	print('truth | predict')
	for line in confusion_vote:
		print(line)


if __name__ == "__main__":
	X, y, task, task_from = [], [], [], []
	read_features(path)
	leave_one_out_validation()
