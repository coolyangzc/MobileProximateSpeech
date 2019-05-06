import os
import numpy as np
from sklearn import svm
from sklearn import tree
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import AdaBoostClassifier

feature_path = '../Data/multi-class/features (backup, mannual)/'
# motion_feature_path = feature_path + 'motion features (full, 162 dimensions)'
motion_feature_path = '../Data/multi-class/features/motion features (1000ms)'
# motion_feature_path = feature_path + 'motion features (full, e~e+0.5, 324)'
# motion_feature_path = feature_path + 'motion features (s~s+1.0, 162 dimensions)'
# motion_feature_path = feature_path + 'motion features (half, half, 324 dimensions)'
voice_feature_path = feature_path + 'voice features (1.0s)'
capa_feature_path = feature_path + 'capa features (10x18, thre=100, 2s, appear only)'
# capa_feature_path = '../Data/multi-class/features/capa features (1000ms)'
# capa_feature_path = feature_path + 'capa features (x,y of 10x18)'
use_motion, use_capa, use_voice = True, True, True

all_category = []
user_list = []

X, y, task = [], [], []


def set_category(c_type='motion'):
	global all_category
	if c_type == 'test':
		all_category = [['竖屏握持，上端遮嘴'],
						['水平端起，倒话筒'],
						['耳旁打电话'],
						['横屏'],
						['竖直对脸，碰触鼻子'],
						['竖直对脸，不碰鼻子']]
	if c_type == 'motion':
		all_category = [['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子', '竖屏握持，上端遮嘴', '话筒'],
						['水平端起，倒话筒'],
						['耳旁打电话'],
						['横屏']]
	if c_type == 'motion(4 types)':
		all_category = [['竖屏握持，上端遮嘴'],
						['水平端起，倒话筒'],
						['耳旁打电话'],
						['横屏']]
	if c_type == 'motion(proximity)':
		all_category = [['竖直对脸，不碰鼻子', '话筒'],
						['竖直对脸，碰触鼻子', '竖屏握持，上端遮嘴'],
						['水平端起，倒话筒'],
						['耳旁打电话'],
						['横屏']]
	if c_type == 'all':
		all_category = [['竖直对脸，碰触鼻子'],
						['竖直对脸，不碰鼻子'],
						['竖屏握持，上端遮嘴'],
						['话筒'],
						['水平端起，倒话筒'],
						['耳旁打电话'],
						['横屏']]
	if c_type == 'all_compact':
		all_category = [['竖直对脸，碰触鼻子'],
						['竖直对脸，不碰鼻子'],
						['竖屏握持，上端遮嘴', '话筒'],
						['水平端起，倒话筒'],
						['耳旁打电话'],
						['横屏']]
	if c_type == 'all_no_microphone':
		all_category = [['竖直对脸，碰触鼻子'],
						['竖直对脸，不碰鼻子'],
						['竖屏握持，上端遮嘴'],
						['水平端起，倒话筒'],
						['耳旁打电话'],
						['横屏']]
	if c_type == 'motion+voice':
		all_category = [['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子'],
						['竖屏握持，上端遮嘴', '话筒'],
						['水平端起，倒话筒'],
						['耳旁打电话'],
						['横屏']]
	if c_type == 'confused':
		all_category = [['竖直对脸，碰触鼻子'],
						['竖直对脸，不碰鼻子'],
						['竖屏握持，上端遮嘴'],
						['话筒']]
	if c_type == 'voice':
		all_category = [['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子', '横屏'],
						['竖屏握持，上端遮嘴', '话筒'],
						['水平端起，倒话筒', '耳旁打电话']]


def read_file(user, file_name, id):
	if not file_name.endswith('.txt'):
		return
	feature = []

	file = open(os.path.join(motion_feature_path, user, file_name), "r", encoding='utf-8')
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

	if use_motion:
		for i in range(7, 7 + feature_num):
			feature.append(float(lines[i]))

	if use_voice:
		file = open(os.path.join(voice_feature_path, user, file_name), "r", encoding='utf-8')
		lines = file.readlines()
		file.close()
		for i in range(len(lines)):
			feature.append(float(lines[i]))

	if use_capa:
		file = open(os.path.join(capa_feature_path, user, file_name), "r", encoding='utf-8')
		lines = file.readlines()
		file.close()
		for i in range(len(lines)):
			feature.append(float(lines[i]))

	X[id].append(feature)
	y[id].append(y_type)
	task[id].append(task_description)


def read_features():
	global X, y, task, user_list
	id = -1
	for u in os.listdir(motion_feature_path):
		if u.endswith('.txt'):
			continue
		print('Reading', u)
		user_list.append(u)
		p = os.path.join(motion_feature_path, u)
		files = os.listdir(p)
		X.append([])
		y.append([])
		task.append([])
		id += 1
		for f in files:
			read_file(u, f, id)


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
		# clf = svm.SVC(kernel='rbf', gamma=1e-2, class_weight='balanced')
		clf = svm.SVC(kernel='rbf', gamma='auto', class_weight='balanced')
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

	if use_motion:
		print('motion feature:', motion_feature_path)
	if use_capa:
		print('capa feature:', capa_feature_path)
	if use_voice:
		print('voice feature:', voice_feature_path)
	print('Mean')
	print(mean_train_acc / len(X))
	print(mean_test_acc / len(X))
	print('truth | predict')
	for i in range(category_n):
		tot = 0
		for j in range(category_n):
			tot += confusion[i][j]
		acc = confusion[i][i] / tot
		print(confusion[i], round(acc * 100, 2), end='\t')
		print(int(confusion[i][i]), '/', int(tot), all_category[i])


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
	set_category(c_type='test')
	# set_category(c_type='all_compact')
	# set_category(c_type='motion(4 types)')
	# set_category(c_type='motion')
	# set_category(c_type='motion+voice')
	# set_category(c_type='voice')
	read_features()
	data_normalization()
	leave_one_out_validation()
