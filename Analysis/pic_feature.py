import os
import cv2
import math
import numpy as np
import random
import matplotlib.pyplot as plt

'''
positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
            '竖屏握持，上端遮嘴',  '水平端起，倒话筒',
            '话筒', '横屏',
			'左耳打电话（不碰）', '右耳打电话（不碰）',
			'左耳打电话（碰触）', '右耳打电话（碰触）',
			'接听']
negative = ['大千世界', '自拍']
neg_study1 = ['打字', '浏览', '拍照', '裤兜', '手中']
'''
positive = []
negative = []
neg_study1 = ['摇晃（前后）', '摇晃（左右）']


path = '../Data/Study2'
subject_path = '../Data/Study2/fixed subjects'
feature_path = '../Data/pic feature'
feature_num = 16


def GLCM(img, dx, dy):
	p = np.zeros((256, 256))
	hav_val = []
	count = 0
	for x in range(max(-dx, 0), min(r-dx, r)):
		for y in range(max(-dy, 0), min(c-dy, c)):
			nx, ny = x + dx, y + dy
			if p[img[x][y]][img[nx][ny]] == 0:
				hav_val.append([int(img[x][y]), int(img[nx][ny])])
			p[img[x][y]][img[nx][ny]] += 1
			count += 1
	energy, entropy, contrast, idm = 0.0, 0.0, 0.0, 0.0
	'''
	for i in range(px_min, px_max+1):
		for j in range(px_min, px_max+1):
			if p[i][j] > 0:
				p[i][j] /= count
				energy += p[i][j] ** 2
				entropy -= p[i][j] * math.log2(p[i][j])
				contrast += (i - j) ** 2 * p[i][j]
				idm += p[i][j] / (1 + (i - j) ** 2)
	'''
	for [i, j] in hav_val:
		prob = float(p[i][j]) / count
		# i, j = float(i), float(j)
		energy += prob ** 2
		entropy -= prob * math.log2(prob)
		contrast += (i - j) ** 2 * prob
		idm += prob / (1 + (i - j) ** 2)

	return [energy, entropy, contrast, idm]


for u in os.listdir(subject_path):
	user_path = os.path.join(subject_path, u)
	orig_path = os.path.join(user_path, 'original')
	resz_path = os.path.join(user_path, 'resized')
	for f in os.listdir(orig_path):
		if not f.endswith('.txt'):
			continue
		print(u, f)
		description_file = os.path.join(orig_path, f)
		file = open(description_file, "r", encoding='utf-8')
		lines = file.readlines()
		if len(lines) < 1:
			continue
		type = lines[0].strip().split(' ')[0]
		if type not in positive and type not in negative and type not in neg_study1:
			continue
		pic_path = os.path.join(resz_path, f[:-4])
		if not os.path.exists(pic_path):
			continue
		out_path = os.path.join(feature_path, u)
		if not os.path.exists(out_path):
			os.makedirs(out_path)
		out_file = os.path.join(out_path, f)
		output = open(out_file, 'w', encoding='utf-8')
		output.truncate()
		output.write(type + '\n')
		output.write(str(feature_num) + '\n')

		pic_list = list(filter(lambda x: x.endswith('.jpg'), os.listdir(pic_path)))
		if type in neg_study1 and len(pic_list) > 10:
			random.shuffle(pic_list)
			pic_list = pic_list[:10]
		for pic in pic_list:
			print(pic)
			pic_file = os.path.join(pic_path, pic)
			img = cv2.imdecode(np.fromfile(pic_file, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
			# img = cv2.imread(pic_file, cv2.IMREAD_GRAYSCALE)
			# img = cv2.resize(img, (64, 64))
			[r, c] = img.shape
			px_min, px_max = np.min(img), np.max(img)
			feature = []
			# Modify feature_num
			feature.extend(GLCM(img, 0, -1))
			feature.extend(GLCM(img, -1, 0))
			feature.extend(GLCM(img, -1, -1))
			feature.extend(GLCM(img, 1, -1))
			for f in feature:
				output.write(str(f) + '\n')

