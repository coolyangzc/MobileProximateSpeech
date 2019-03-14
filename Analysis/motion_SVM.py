import os
import numpy as np
from sklearn import tree
from sklearn import svm
from sklearn.ensemble import AdaBoostClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split


feature_path = '../Data/feature_2s_1s1s/'
# feature_path = '../Data/feature - 副本/'
user_list = os.listdir(feature_path)
X = []
y = []
task = []
id = -1
for u in user_list:
	print(u)
	if u[-4:] == '.txt':
		continue
	if u == 'tqy':
		continue
	p = os.path.join(feature_path, u)
	out_dir = os.path.join(feature_path, u)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
	files = os.listdir(p)
	X.append([])
	y.append([])
	task.append([])
	id += 1
	for f in files:
		if f[-4:] == ".txt":
			file = open(os.path.join(p, f), "r", encoding='utf-8')
			lines = file.readlines()
			file.close()
			#feature_num = 78
			#feature_num = 63
			feature_num = 156
			task_id = int(f.split('_')[0])
			if 19 <= task_id <= 22:
				continue
			if task_id < 32:
				feature = []
				for i in range(6, 6 + feature_num):
					feature.append(float(lines[i]))
				# feature = feature[:42]
				X[id].append(feature)
				y[id].append(1)
				task[id].append(lines[2])
			else:
				if lines[2] == '接听\n':
					continue
				sp = 6
				while sp + feature_num <= len(lines):
					feature = []
					for i in range(feature_num):
						feature.append(float(lines[sp + i]))
					# feature = feature[:42]
					X[id].append(feature)
					# if lines[2] == '接听\n':
					#	y[id].append(2)
					# else:
					y[id].append(0)
					task[id].append(lines[2])
					sp += feature_num + 2

X_all = []
for i in range(len(X)):
	X_all.extend(X[i])
# scaler = RobustScaler()
scaler = StandardScaler()
scaler.fit(X_all)
for i in range(len(X)):
	X[i] = scaler.transform(X[i])

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
	X_test = X[loo]
	y_test = y[loo]
	X_train = np.array(X_train)
	X_test = np.array(X_test)
	y_train = np.array(y_train)
	y_test = np.array(y_test)
	# clf = AdaBoostClassifier()
	clf = svm.SVC(kernel='rbf', gamma=1e-3, class_weight={0:1, 1:1})
	# clf = tree.DecisionTreeClassifier(max_depth=10)
	clf.fit(X_train, y_train)
	print(X_train.shape)
	print(y_train.shape)
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
	print(t, correct[t], '/', total[t], correct[t] / total[t])

'''
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
print(X_train.shape, y_train.shape)
print(X_test.shape, y_test.shape)
clf = svm.SVC(kernel='rbf', gamma='scale')
clf.fit(X_train, y_train)
print(clf.score(X_train, y_train))
print(clf.score(X_test, y_test))
'''