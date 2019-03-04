"""
将数据进行若干分类
- 按正、负例归类

编写日期：2019年01月27日
"""

import os, shutil, re
from utils import logger, tools
from tqdm import tqdm	# progressbar

PREFIX = tools.date_time()

NEG_DESCRIPTIONS = re.compile(' (打字|浏览|拍照|裤兜（坐）|裤兜（走）|握持（走）|桌上|接听|负例) ', re.U)  # 负例

logger.DualLogger('../logs/%sdata_sorting.txt' % PREFIX)


def sort_positive_negative(file_dir):
	"""
	sort .txt and .mp4 files in terms of positivity (trigger or normal use)
	the function will make two subdirectories in file_dir named `Positive` and `Negative`
	make sure the `Positive` and `Negative` don't exist

	:param file_dir: working directory
	"""
	print('sortting positive/negative...')
	os.chdir(file_dir)
	if os.path.exists('./Positive/') or os.path.exists('./Negative'):
		raise FileExistsError('the subdirectories already exist.')
	os.mkdir('./Positive/')
	os.mkdir('./Negative/')
	file_names = os.listdir('.')
	file_count = 0
	for file_name in tqdm(file_names):
		if file_name.endswith('.txt'):
			file_count += 2
			with open(file_name, 'r') as f:
				line = f.readline()
			# copy files to target subdirectories
			match = NEG_DESCRIPTIONS.search(line)
			sub_dir = './Positive/' if match is None else './Negative'
			shutil.copyfile(file_name, os.path.join(sub_dir, file_name)) # copy .txt
			file_name = tools.suffix_conv(file_name, '.mp4') # copy .mp4
			shutil.copyfile(file_name, os.path.join(sub_dir, file_name))
	print('sorted.')
	assert len(os.listdir('./Positive')) + len(os.listdir('./Negative')) == file_count


if __name__ == '__main__':
	dir1 = '../Data/Study1/Fengshi Zheng'
	sort_positive_negative(dir1)
