import os
from tqdm import tqdm
from utils.tools import suffix_filter, dir_filter


def _remove_redundant(subject_dir, which='trimmed'):
	'''
	apply filter to original/ or trimmed/, only keep jpgs exsiting in resized/
	be careful to call this function!!

	:param subject_dir:
	:param which: 'original' or 'trimmed', depending on where the frame folders are stored
	:return del_cnt: how many deleted
	'''
	owd = os.getcwd()
	os.chdir(subject_dir)
	assert os.path.exists(which) and os.path.exists('resized')
	os.chdir('resized')
	frame_folders = dir_filter(os.listdir('.'))
	del_cnt = 0
	for folder in tqdm(frame_folders):
		img_names = set(suffix_filter(os.listdir(folder), '.jpg'))
		src_folder = os.path.join('..', which, folder)
		# delete files in src_folder that are not in img_names in 'resized/'
		for file_name in os.listdir(src_folder):
			if file_name not in img_names:
				file_path = os.path.join(src_folder, file_name)
				os.remove(file_path)
				del_cnt += 1
	os.chdir(owd)
	return del_cnt


if __name__ == '__main__':
	cwd = '/Users/james/MobileProximateSpeech/Analysis/Data/Study2/subjects-2/'
	os.chdir(cwd)
	subjects = ['hsd', 'cjr']
	for subject in subjects:
		print('deleted cnt:',  _remove_redundant(subject, which='trimmed'))
