import os

from utils.tools import suffix_conv, suffix_filter


def generate_doc_for_subfolders(wkdir: str, description: str):
	'''
	generate doc .txt file in directory for subfolders
	necessary only when .txt files are missing

	:param wkdir: directory to deal with
	:param description: description text
	'''
	old_path = os.getcwd()
	os.chdir(wkdir)
	folders = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	for folder in folders:
		txt_name = folder + '.txt'
		with open(txt_name, 'w', encoding='utf-8') as f:
			f.write(description + ' Study2\n')
	os.chdir(old_path)


def generate_doc_for_videos(wkdir: str, description: str, format='mp4'):
	'''
	generate doc .txt file in directory for video files
	necessary only when .txt files are missing

	:param wkdir: directory to deal with
	:param description: description text
	:param format: video file format
	'''
	old_path = os.getcwd()
	os.chdir(wkdir)
	video_names = suffix_filter(os.listdir('.'), format)
	for video_name in video_names:
		txt_name = suffix_conv(video_name, '.txt')
		with open(txt_name, 'w', encoding='utf-8') as f:
			f.write(description + ' Study2\n')
	os.chdir(old_path)


if __name__ == '__main__':
	from configs.cv_config import data_source
	os.chdir(data_source)
	os.chdir('negatives/zfs_confusing_iphone/original')
	generate_doc_for_videos('./', '易混淆', format='MOV')
	pass
