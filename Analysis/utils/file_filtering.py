# this code deal with the raw data folder.
# Concerning some experiments failed in the very first, and hence re-tests were done,
# this code tries to select the last three successful experiments.

import shutil, os, re
from tqdm import tqdm
from utils import logger, tools

DATE_TIME = tools.date_time()

N_STUDY1 = 134  # 134 tests for study1

progress_re = re.compile('(\d+) / %d' % N_STUDY1, re.U)  # pattern for progress number

class TriList(list):
	# three element list
	def append(self, object: str):
		super().append(object)
		self.sort()
		while len(self) > 3: del self[0]


def filter1(file_dir):
	"""
	filter for study1, copying selected files to `Filtered`

	:param file_dir: raw data directory
	"""
	sub_dir = './Filtered/'
	print('# filtering for study 1 at %s' % file_dir)
	os.chdir(file_dir)
	if os.path.exists(sub_dir):
		raise FileExistsError('the subdirectory already exists.')
	os.mkdir(sub_dir)
	selected_files = {}
	for i in range(1, N_STUDY1 + 1):
		selected_files[i] = TriList()
	file_names = os.listdir('.')

	# select the files
	print('selecting...')
	for file_name in tqdm(file_names):
		if file_name.endswith('.txt'):
			with open(file_name, 'r') as f:
				line1 = f.readline()
			mt = progress_re.search(line1)
			assert mt  # the match must succeed
			selected_files[int(mt.group(1))].append(file_name)

	# copy to subdirectory
	file_count = 0
	print('copying...')
	for i in tqdm(range(1, N_STUDY1 + 1)):
		cur_list = selected_files[i]
		for file_name in cur_list:
			file_count += 1
			# .txt
			new_path = os.path.join(sub_dir, file_name)
			shutil.copyfile(file_name, new_path)
			# .mp4
			file_name = tools.suffix_conv(file_name, '.mp4')
			new_path = os.path.join(sub_dir, file_name)
			shutil.copyfile(file_name, new_path)

	assert file_count == N_STUDY1 * 3
	print('filtered files copied to %s' % os.path.join(file_dir, sub_dir))


if __name__ == '__main__':
	logger.DualLogger('../logs/%sfile filtering.txt' % DATE_TIME)
	filter1('../Data/Study1/Fengshi Zheng (raw)/')
