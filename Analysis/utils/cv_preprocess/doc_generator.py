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


def generate_doc_for_mp4(wkdir: str, description: str):
	'''
	generate doc .txt file in directory for .mp4 files
	necessary only when .txt files are missing

	:param wkdir: directory to deal with
	:param description: description text
	'''
	old_path = os.getcwd()
	os.chdir(wkdir)
	video_names = suffix_filter(os.listdir('.'), '.mp4')
	for video_name in video_names:
		txt_name = suffix_conv(video_name, '.txt')
		with open(txt_name, 'w', encoding='utf-8') as f:
			f.write(description + ' Study2\n')
	os.chdir(old_path)


if __name__ == '__main__':
	CWD = 'E:\ZFS_TEST\Analysis\Data\Study2\\negatives'
	os.chdir(CWD)
	generate_doc_for_subfolders('world/original', '大千世界')
	pass
