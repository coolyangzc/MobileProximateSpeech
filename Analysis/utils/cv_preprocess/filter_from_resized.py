import os
from utils.tools import suffix_filter, dir_filter


def _remove_redundant(subject_dir, target='trimmed', ref='resized'):
	'''
	apply filter to original/ or trimmed/, only keep jpgs exsiting in resized/
	be careful to call this function!!

	:param subject_dir:
	:param target: 'original' or 'trimmed', depending on where the frame folders are stored
	:return del_cnt: how many deleted
	'''
	owd = os.getcwd()
	os.chdir(subject_dir)
	assert os.path.exists(target) and os.path.exists(ref)
	os.chdir(ref)
	frame_folders = dir_filter(os.listdir('.'))
	del_cnt = 0
	for folder in frame_folders:
		img_names = set(suffix_filter(os.listdir(folder), '.jpg'))
		trg_dir = os.path.join('..', target, folder)
		# delete files in src_folder that are not in img_names in 'resized/'
		for file_name in os.listdir(trg_dir):
			if file_name not in img_names:
				file_path = os.path.join(trg_dir, file_name)
				os.remove(file_path)
				del_cnt += 1
	os.chdir(owd)
	return del_cnt


if __name__ == '__main__':
	cwd = '/Volumes/TOSHIBA EXT/study2 subjects'
	os.chdir(cwd)
	subjects = dir_filter(os.listdir('.'))
	# print(subjects)
	for subject in subjects:
		print(subject, end='\t\t')
		print('deleted cnt:', _remove_redundant(subject, target='original', ref='resized'))
