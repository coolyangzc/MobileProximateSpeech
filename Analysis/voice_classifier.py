import os
import numpy as np
from sklearn import tree
from sklearn import svm
from sklearn import neighbors
from sklearn.externals import joblib
from sklearn.ensemble import AdaBoostClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子', '竖屏握持，上端遮嘴',
			'水平端起，倒话筒', '话筒', '横屏', '耳旁打电话']
negative = ['手上正面', '手上反面', '桌上正面', '桌上反面']
			#'裤兜']

all_category = positive + negative

used_feature = [1, # min
				1, # max
				1, # median
				1, # mean
				0, # std
				1, # IQR
				0, # energy
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

	if task_description in positive:
		y_type = 1
	elif task_description in negative:
		y_type = 0
	else:
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
	X_all, y_all = np.array(X_all), np.array(y_all)
	print(X_all.shape, y_all.shape)
	clf = svm.SVC(kernel='rbf', gamma='scale', class_weight={0: 1, 1: 1}, probability=True)
	# clf = tree.DecisionTreeClassifier(max_depth=8)
	clf.fit(X_all, y_all)
	# joblib.dump(clf, "voice_model.m")
	print(clf.score(X_all, y_all))

	cnt = np.zeros((2, 100 + 1))
	proba = clf.predict_proba(X_all)
	for i in range(len(X_all)):
		for res in range(2):
			if proba[i][res] > 0.5:
				if res == y_all[i]:
					correct = 1
				else:
					correct = 0
				p = int(proba[i][res] / 0.01)
				cnt[correct][p] += 1
	x_range = np.linspace(50, 100, 51)
	plt.plot(x_range, cnt[0][50:], label='error')
	plt.plot(x_range, cnt[1][50:], label='correct')
	plt.legend()
	plt.show()


def leave_one_out_validation():
	mean_train_acc, mean_test_acc = 0, 0

	total, correct, total_vote, correct_vote = {}, {}, {}, {}

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
		print(X_train.shape, y_train.shape)
		# clf = AdaBoostClassifier()
		# bigger gamma -> higher fit acc
		# clf = svm.SVC(kernel='rbf', gamma='scale', class_weight={0: 1, 1: 1}, probability=True)
		# clf = neighbors.KNeighborsClassifier()
		clf = tree.DecisionTreeClassifier(max_depth=10, class_weight={0: 1, 1: 1})
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
				total[t], total_vote[t] = 0, 0
				correct[t], correct_vote[t] = 0, 0
			total[t] += 1
			if res[i] == y[loo][i]:
				same.append(1)
				correct[t] += 1
			else:
				same.append(0)
		print(same)
		print(train_acc)
		print(test_acc)

		vote = 0
		task_from[loo].append('#')
		# Simple Vote
		'''
		for i in range(len(res)):
			t = task[loo][i]
			if res[i] == 1:
				vote += 1
			else:
				vote -= 1
			if task_from[loo][i] != task_from[loo][i+1]:
				if vote > 0:
					vote_res = 1
				else:
					vote_res = 0
				total_vote[t] += 1
				if vote_res == y[loo][i]:
					correct_vote[t] += 1
				vote = 0
		'''
		# Proba Vote
		res = clf.predict_proba(X[loo])
		# print(res)
		for i in range(len(res)):
			t = task[loo][i]
			vote -= res[i][0]
			vote += res[i][1]
			if task_from[loo][i] != task_from[loo][i + 1]:
				if vote > 0:
					vote_res = 1
				else:
					vote_res = 0
				total_vote[t] += 1
				if vote_res == y[loo][i]:
					correct_vote[t] += 1
				vote = 0

	print('Mean')
	print(mean_train_acc / len(X))
	print(mean_test_acc / len(X))
	for t in correct:
		print(t.ljust(24 - len(t)), correct[t], '/', total[t], correct[t] / total[t])

	print('Vote')
	mean_vote_acc = 0
	for t in correct_vote:
		print(t.ljust(24 - len(t)), correct_vote[t], '/', total_vote[t], correct_vote[t] / total_vote[t])
		mean_vote_acc += correct_vote[t] / total_vote[t]
	mean_vote_acc /= len(correct_vote)
	print(mean_vote_acc)


def leave_one_out_save(path):
	out_file = os.path.join(path, 'leave_one_out3.csv')
	output = open(out_file, 'w', encoding='utf-8-sig')
	output.write('user')
	for c in all_category:
		output.write(',' + c)
	for c in all_category:
		output.write(',' + c + '(sentence)')
	output.write('\n')
	type = len(all_category)

	for loo in range(len(X)):
		print(loo)
		X_train, y_train = [], []
		total, correct = np.zeros(type), np.zeros(type)
		total_vote, correct_vote = np.zeros(type), np.zeros(type)
		for i in range(len(X)):
			if i != loo:
				X_train.extend(X[i])
				y_train.extend(y[i])
		X_test, y_test = X[loo], y[loo]
		X_train, X_test = np.array(X_train), np.array(X_test)
		y_train, y_test = np.array(y_train), np.array(y_test)
		print(X_train.shape, y_train.shape)
		clf = tree.DecisionTreeClassifier(max_depth=10, class_weight={0: 1, 1: 1})
		clf.fit(X_train, y_train)
		res = clf.predict(X[loo])
		res_proba = clf.predict_proba(X[loo])
		vote = 0
		task_from[loo].append('#')
		for i in range(len(res)):
			t = all_category.index(task[loo][i])
			total[t] += 1
			vote -= res_proba[i][0]
			vote += res_proba[i][1]
			if res[i] == y[loo][i]:
				correct[t] += 1
			if task_from[loo][i] != task_from[loo][i + 1]:
				if vote > 0:
					vote_res = 1
				else:
					vote_res = 0
				total_vote[t] += 1
				if vote_res == y[loo][i]:
					correct_vote[t] += 1
				vote = 0
		output.write(str(loo))
		for i in range(type):
			if total[i] > 0:
				acc = correct[i] / total[i] * 100
			else:
				acc = 100
			output.write(',' + str(acc))
		for i in range(type):
			if total_vote[i] > 0:
				acc_vote = correct_vote[i] / total_vote[i] * 100
			else:
				acc_vote = 100
			output.write(',' + str(acc_vote))
		output.write('\n')


def personalization(path):
	out_file = os.path.join(path, 'personalization.csv')
	output = open(out_file, 'w', encoding='utf-8-sig')
	output.write('user')
	for c in all_category:
		output.write(',' + c)
	for c in all_category:
		output.write(',' + c + '(sentence)')
	output.write('\n')
	type = len(all_category)
	for user in range(len(X)):
		print(user)
		task_from[user].append('#')

		total, correct = np.zeros(type), np.zeros(type)
		total_vote, correct_vote = np.zeros(type), np.zeros(type)
		clf = tree.DecisionTreeClassifier(max_depth=10, class_weight={0: 1, 1: 1})
		clf.fit(X[user], y[user])

		res = clf.predict(X[user])
		res_proba = clf.predict_proba(X[user])
		vote = 0
		for i in range(len(res)):
			t = all_category.index(task[user][i])
			total[t] += 1
			vote -= res_proba[i][0]
			vote += res_proba[i][1]
			if res[i] == y[user][i]:
				correct[t] += 1
			if task_from[user][i] != task_from[user][i + 1]:
				if vote > 0:
					vote_res = 1
				else:
					vote_res = 0
				total_vote[t] += 1
				if vote_res == y[user][i]:
					correct_vote[t] += 1
				vote = 0
		output.write(str(user))
		for i in range(type):
			if total[i] > 0:
				acc = correct[i] / total[i] * 100
			else:
				acc = 100
			output.write(',' + str(acc))
		for i in range(type):
			if total_vote[i] > 0:
				acc_vote = correct_vote[i] / total_vote[i] * 100
			else:
				acc_vote = 100
			output.write(',' + str(acc_vote))
		output.write('\n')


if __name__ == "__main__":
	X, y, task, task_from = [], [], [], []
	# read_features('../Data/voice feature/')
	path = '../Data/voice feature Stereo 32000 Hz 0.2s stride=50%/'
	read_features(path)
	data_normalization()
	# generate_model()
	leave_one_out_validation()
	# leave_one_out_save(path)
	# personalization(path)
