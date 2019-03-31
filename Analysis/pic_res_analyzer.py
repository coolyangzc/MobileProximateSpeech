import os
import numpy as np

res_path = '../Data/Study2/sorted pics_192_108/Mouth+Ear vs. Other/results/'

positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
           '竖屏握持，上端遮嘴', # '水平端起，倒话筒',
           '横屏', '话筒',
			'左耳打电话（不碰）', '右耳打电话（不碰）', '左耳打电话（碰触）', '右耳打电话（碰触）']

negative = ['手中', '打字', '拍照', '浏览',
			'自拍', '摇晃（前后）', '摇晃（左右）', '裤兜']

all_type = positive + negative

if __name__ == "__main__":
	acc, cnt = {}, {}
	for t in all_type:
		acc[t], cnt[t] = 0, 0

	for file_name in os.listdir(res_path):
		file = open(os.path.join(res_path, file_name), "r", encoding='utf-8')
		lines = file.readlines()
		for line in lines[1:-1]:
			data = line.strip().split(' ')
			t = data[0]
			predict_acc = float(data[-1])
			acc[t] += predict_acc
			cnt[t] += 1
	all_acc = []
	for t in acc:
		if cnt[t] > 0:
			print(t.ljust(24 - len(t)), cnt[t], acc[t] / cnt[t])
			all_acc.append(acc[t] / cnt[t])
		else:
			print(t.ljust(24 - len(t)), cnt[t])
	all_acc = np.array(all_acc)
	print(np.mean(all_acc))