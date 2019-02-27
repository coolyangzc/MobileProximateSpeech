# 用SVM对特征进行分类
## 2019年02月27日

import sklearn
import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
import os
import os.path as path
import pickle
from tqdm import tqdm as progress


## 对每个样本抽取时间序列的中间长度为800帧的子序列
def select_mid(sample, length=800):
	'''
	sample - shape like (40, Tx) (Tx ≥ 800)
	length - length of selected sequence

	return - selected 800 time frames in the sample, shape like (40, 800)
	'''
	mid = sample.shape[1] // 2
	semi_len = length // 2
	return sample[:, mid - semi_len: mid + semi_len]


os.chdir('./Data/Sounds/MP3/')
samples = []
labels = []
time_len = 800  # 采样帧个数

## 导入正例
os.chdir('./Positive/')
print('Loading in Positive...')
for filename in progress(os.listdir()):
	if filename.endswith('.ftr'):
		with open(filename, 'rb') as f:
			sample = pickle.load(f)
		sample = select_mid(sample, time_len)
		samples.append(sample)
		labels.append('+')

## 导入负例
os.chdir('../Negative/')
print('Loading in Negative...')
for filename in progress(os.listdir()):
	if filename.endswith('.ftr'):
		with open(filename, 'rb') as f:
			sample = pickle.load(f)
		sample = select_mid(sample, time_len)
		samples.append(sample)
		labels.append('-')

## 扁平化特征分类法
print('\nFlatten Method')
# flatten features
flatten_samlpes = [sample.flatten() for sample in samples]
X_train1, X_test1, Y_train1, Y_test1 = train_test_split(flatten_samlpes, labels, shuffle=True, test_size=0.2)

clf1 = SVC(kernel='rbf', gamma=1e-8)
clf1.fit(X_train1, Y_train1)

print('train set score:', clf1.score(X_train1, Y_train1))
print('test set  score:', clf1.score(X_test1, Y_test1))

## 对每一帧打分，加权投票法
print('\nAverage Method')
# average features
avg_samples = [sample.mean(axis=1) for sample in samples]
X_train2, X_test2, Y_train2, Y_test2 = train_test_split(avg_samples, labels, shuffle=True, test_size=0.2)

clf2 = SVC(kernel='rbf', gamma=1e-3)
clf2.fit(X_train2, Y_train2)

print('train set score:', clf2.score(X_train2, Y_train2))
print('test set  score:', clf2.score(X_test2, Y_test2))

### 保存模型
os.chdir('../../../../voice/')
with open('flatten-svc.obj', 'wb') as f:
	pickle.dump(clf1, f)
with open('average-svc.obj', 'wb') as f:
	pickle.dump(clf2, f)
