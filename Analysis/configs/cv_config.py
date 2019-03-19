import re

from utils.tools import inverse_dict

label_dict = {  # todo 分类字典, 0 表示舍弃这个特征的所有数据，- 表示负例
	'大千世界': -1,
	'易混淆': -2,
	'耳旁打电话': -3,
	'右耳打电话（不碰）': -4,
	'右耳打电话（碰触）': -5,
	'左耳打电话（不碰）': -6,
	'左耳打电话（碰触）': -7,
	'倒着拿手机': -8,
	'自拍': -9,

	'竖直对脸，碰触鼻子': +1,
	'竖直对脸，不碰鼻子': +2,
	'竖屏握持，上端遮嘴': +3,
	'水平端起，倒话筒': +4,
	'话筒': +5,
	'横屏': +6,
}

doc_dict = inverse_dict(label_dict)  # 每一类对应的描述
try:
	del doc_dict[0]
except:
	pass

CLASSES = label_dict.values()
N_CLASS = len(doc_dict)

description_pattern = re.compile('(.*) Study2', re.U)
