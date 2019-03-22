import os
from PIL import Image

positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
            '竖屏握持，上端遮嘴', # '水平端起，倒话筒',
            '话筒', '横屏']
negative = ['左耳打电话（不碰）', '右耳打电话（不碰）', '左耳打电话（碰触）', '右耳打电话（碰触）']

subject_path = '../Data/Study2/fixed subjects'
sort_path = '../Data/Study2/sorted pics'

for u in os.listdir(subject_path):
	user_path = os.path.join(subject_path, u)
	orig_path = os.path.join(user_path, 'original')
	resz_path = os.path.join(user_path, 'resized')
	txt_list = list(filter(lambda x: x.endswith('.txt'), os.listdir(orig_path)))
	for f in txt_list:
		print(u, f)
		description_file = os.path.join(orig_path, f)
		file = open(description_file, "r", encoding='utf-8')
		line = file.readline()
		type = line.strip().split(' ')[0]
		if type not in positive and type not in negative:
			continue
		out_path = os.path.join(sort_path, type)
		if not os.path.exists(out_path):
			os.makedirs(out_path)
		pic_path = os.path.join(resz_path, f[:-4])
		if not os.path.exists(pic_path):
			continue
		pic_list = list(filter(lambda x: x.endswith('.jpg'), os.listdir(pic_path)))
		for pic in pic_list:
			pic_file = os.path.join(pic_path, pic)
			img = Image.open(pic_file)
			out_file = os.path.join(out_path, u+'_'+f[:-4]+'_'+pic)
			img.save(out_file)

