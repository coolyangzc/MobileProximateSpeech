import os
import cv2
import math
import numpy as np
import matplotlib.pyplot as plt

path = '../Data/Study2'
subject_path = '../Data/Study2/fixed subjects'
feature_path = '../Data/pic feature'
feature_num = 8


def GLCM(img, dx, dy):
	p = np.zeros((256, 256))
	count = 0
	for x in range(max(-dx, 0), min(r-dx, r)):
		for y in range(max(-dy, 0), min(c-dy, c)):
			nx, ny = x + dx, y + dy
			p[img[x][y]][img[nx][ny]] += 1
			count += 1
	energy, entropy, contrast, idm = 0, 0, 0, 0

	for i in range(px_min, px_max+1):
		for j in range(px_min, px_max+1):
			if p[i][j] > 0:
				p[i][j] /= count
				energy += p[i][j] ** 2
				entropy -= p[i][j] * math.log2(p[i][j])
				contrast += (i - j) ** 2 * p[i][j]
				idm += p[i][j] / (1 + (i - j) ** 2)
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
		pic_path = os.path.join(resz_path, f[:-4])
		if not os.path.exists(pic_path):
			continue
		out_path = os.path.join(feature_path, u)
		if not os.path.exists(out_path):
			os.makedirs(out_path)
		out_file = os.path.join(out_path, f)
		output = open(out_file, 'w', encoding='utf-8')
		output.truncate()
		output.write(lines[0].split(' ')[0] + '\n')
		output.write(str(feature_num) + '\n')

		for pic in os.listdir(pic_path):
			if not pic.endswith(".jpg"):
				continue
			# print(pic)
			pic_file = os.path.join(pic_path, pic)
			img = cv2.imdecode(np.fromfile(pic_file, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
			# img = cv2.imread(pic_file, cv2.IMREAD_GRAYSCALE)
			img = cv2.resize(img, (64, 64))
			[r, c] = img.shape
			px_min, px_max = np.min(img), np.max(img)
			feature = []
			feature.extend(GLCM(img, 0, -1))
			feature.extend(GLCM(img, -1, 0))
			# feature.extend(GLCM(img, -1, -1))
			# feature.extend(GLCM(img, 1, -1))
			for f in feature:
				output.write(str(f) + '\n')

			'''
			sz = r * c
			p = np.zeros(256)

			H = 0
			for i in range(len(p)):
				if p[i] > 0:
					p[i] /= sz
					H += p[i] * math.log2(p[i])
			output.write(str(H) + '\n')
			'''

