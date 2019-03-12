import os
import sklearn as sk
import numpy as np
from sklearn import svm


feature_path = '../Data/feature/'
user_list = os.listdir(feature_path)
for u in user_list:
	#if u != "yzc" and u != "plh":
	if u != "plh":
		continue
	p = os.path.join(feature_path, u)
	out_dir = os.path.join(feature_path, u)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
	files = os.listdir(p)
	X = []
	y = []
	for f in files:
		if f[-4:] == ".txt":
			file = open(os.path.join(p, f), "r", encoding='utf-8')
			lines = file.readlines()
			file.close()
			if int(f.split('_')[0]) < 32:
				feature = []
				for i in range(6, 12):
					feature.append(float(lines[i]))
				X.append(feature)
				y.append(1)
			else:
				for j in range(5):
					feature = []
					for i in range(6, 12):
						feature.append(float(lines[j*8+i]))
					X.append(feature)
					y.append(0)
	X = np.array(X)
	y = np.array(y)
	print(X.shape, y.shape)
	X_train, X_test, y_train, y_test = sk.model_selection.train_test_split(X, y, test_size=0.2)
	print(X_train.shape, y_train.shape)
	print(X_test.shape, y_test.shape)
	clf = sk.svm.SVC(kernel='rbf', gamma='scale')
	clf.fit(X_train, y_train)
	print(clf.score(X_train, y_train))
	print(clf.score(X_test, y_test))
