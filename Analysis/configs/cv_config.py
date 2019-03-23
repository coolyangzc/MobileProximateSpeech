import re

from utils.tools import inverse_dict

label_dict = {  # todo 分类字典, 0 表示舍弃这个特征的所有数据，- 表示负例
	'大千世界': 0,
	'易混淆': -1,
	'耳旁打电话': 0,
	'右耳打电话（不碰）': +7,
	'右耳打电话（碰触）': +8,
	'左耳打电话（不碰）': +9,
	'左耳打电话（碰触）': +10,
	'倒着拿手机': 0,
	'自拍': 0,

	'竖直对脸，碰触鼻子': +1,
	'竖直对脸，不碰鼻子': +2,
	'竖屏握持，上端遮嘴': +3,
	'水平端起，倒话筒': 0,
	'话筒': +5,
	'横屏': +6,
}

description_pattern = re.compile('(.*) Study2', re.U)
doc_dict = inverse_dict(label_dict)  # 每一类对应的描述
try:
	del doc_dict[0]
except:
	pass
# doc_dict = {0: '易混淆', 1: '正例'}

CLASSES = list(set(label_dict.values()))
try:
	CLASSES.remove(0)
except:
	pass
N_CLASS = len(doc_dict)

# todo directories
working_directory = 'E:/ZFS_TEST/Analysis/'
data_directory = 'E:/ZFS_TEST/Analysis/Data/Study2/'  # should include 'train' 'test' 'val' folders
data_source = 'H:/FullData/Study2/'  # should include 'negatives' 'fixed subjects'

data_gen_config = {
	'rotation_range': 40,
	'width_shift_range': 0.2,
	'height_shift_range': 0.2,
	'zoom_range': 0.1,
	'horizontal_flip': True,
	'vertical_flip': True,
}

# todo hyperparameters
batch_size = 10
random_seed = 101
learning_rate = 1e-6
decay = 1e-5
epochs = 5
class_weight = {0: 3, 1: 1}

if __name__ == '__main__':
	print(label_dict)
	print(doc_dict)
	print(CLASSES)
	print(N_CLASS)