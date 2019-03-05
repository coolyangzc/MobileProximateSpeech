# this code deal with the raw data folder.
# Concerning some experiments failed in the very first, and hence re-tests were done,
# this code tries to select the last three successful experiments.

import shutil, os, re
from tqdm import tqdm
from utils import logger, tools

DATE_TIME = tools.date_time()

N_STUDY1 = 134  # 134 tests for study1

N_STUDY3 = 24  # 24 tests for voice study


class TriList(list):
	# three element list
	def append(self, object: str):
		super().append(object)
		self.sort()
		while len(self) > 3: del self[0]


def filter_(file_dir, n_test, deal_individual=False, audio_format='mp4'):
	'''
	general raw file filter

	:param file_dir: raw data directory
	:param n_test: test count
	:param deal_individual: whether to view three repeated experiments as individual experiments
	:param audio_format: format of audio files
	'''
	if deal_individual:
		progress_re = re.compile('(\d+) / %d: ([123])' % n_test, re.U)
	else:
		progress_re = re.compile('(\d+) / %d' % n_test, re.U)  # pattern for progress number

	print('filtering in %s' % file_dir)
	old_dir = os.getcwd()
	os.chdir(file_dir)
	dst_dir = '../filtered/'
	if os.path.exists(dst_dir):
		raise FileExistsError('the subdirectory already exists.')
	os.mkdir(dst_dir)
	selected_files = {}
	if not deal_individual:
		for i in range(1, n_test + 1):
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
			if deal_individual:
				dice = (int(mt.group(1)), int(mt.group(2)))
				if selected_files.get(dice) == None or selected_files[dice] < file_name:  # create or overwrite
					selected_files[dice] = file_name
			else:  # TriList()
				selected_files[int(mt.group(1))].append(file_name)

	# copy to subdirectory
	file_count = 0
	print('copying...')
	if deal_individual:
		for i in tqdm(range(1, n_test + 1)):
			for j in [1, 2, 3]:
				file_count += 1
				file_name = selected_files[(i, j)]
				# .txt
				dst_path = os.path.join(dst_dir, file_name)
				shutil.copyfile(file_name, dst_path)
				# audio
				file_name = tools.suffix_conv(file_name, audio_format)
				dst_path = os.path.join(dst_dir, file_name)
				shutil.copyfile(file_name, dst_path)
	else:
		for i in tqdm(range(1, n_test + 1)):
			cur_list = selected_files[i]
			for file_name in cur_list:
				file_count += 1
				# .txt
				dst_path = os.path.join(dst_dir, file_name)
				shutil.copyfile(file_name, dst_path)
				# audio
				file_name = tools.suffix_conv(file_name, audio_format)
				dst_path = os.path.join(dst_dir, file_name)
				shutil.copyfile(file_name, dst_path)

	assert file_count == n_test * 3
	print('filtered files copied to %s' % os.path.join(file_dir, dst_dir))
	os.chdir(old_dir)


def filter1(file_dir, audio_format='mp4'):
	"""
	filter for study1, copying selected files to `filtered`

	:param file_dir: raw data directory
	"""
	print('Study 1')
	filter_(file_dir, N_STUDY1, audio_format=audio_format)


def filter3(file_dir, deal_individual=False, audio_format='mp4'):
	"""
	filter for study3, copying selected files to `filtered`

	:param file_dir: raw data directory
	:param deal_individual: whether to view three repeated experiments as individual experiments
	:param audio_format: format of audio files
	"""
	print('Study 3')
	filter_(file_dir, N_STUDY3, deal_individual=deal_individual, audio_format=audio_format)


if __name__ == '__main__':
	logger.DualLogger('../logs/%svoice file filtering.txt' % DATE_TIME)
	filter3('../Data/Study3/subjects/xy/original', deal_individual=True, audio_format='wav')
