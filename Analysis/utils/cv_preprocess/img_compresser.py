import os
import shutil
import threading

# import PIL
from PIL import Image
# from matplotlib import pyplot as plt
from tqdm import tqdm


# def compare_gray_hist():
# 	CWD = 'E:\ZFS_TEST\Analysis\Data\Study2\subjects\cjr\\trimmed'
# 	os.chdir(CWD)
#
# 	p = []
# 	n = []
#
# 	os.chdir('190130 12_38_23')
# 	for file in tqdm(list(filter(lambda x: x.endswith('.jpg'), os.listdir('.')))[:3]):
# 		img = Image.open(file)
# 		img = img.convert('L')
# 		p += img.histogram()
# 	os.chdir('..')
#
# 	os.chdir('190130 12_41_54')
# 	for file in tqdm(list(filter(lambda x: x.endswith('.jpg'), os.listdir('.')))[:3]):
# 		img = Image.open(file)
# 		img = img.convert('L')
# 		n += img.histogram()
# 	os.chdir('..')
#
# 	plt.hist(p, bins=30, facecolor='red', edgecolor='black', label='close', alpha=0.5)
# 	plt.hist(n, bins=30, facecolor='blue', edgecolor='black', label='distant', alpha=0.5)
# 	plt.legend()
# 	plt.show()

class MyThread(threading.Thread):
	def __init__(self, files, subject_dir, dst_size, dst_folder, progress):
		self.files = files
		self.subject_dir = subject_dir
		self.dst_size = dst_size
		self.dst_folder = dst_folder
		self.progress = progress
		super().__init__()

	def run(self):
		for file in self.files:
			try:
				img = Image.open(file)
			except:
				print('cannot open', self.subject_dir, file)
				continue
			img = auto_crop(img, self.dst_size[1] / self.dst_size[0])
			img = img.resize(self.dst_size)  # resize image
			img.save(os.path.join(self.dst_folder, file))
			self.progress.update()


def auto_crop(img: Image, height_to_width: float) -> Image:
	'''
	crop the img according to height to width ratio maximunly from the image center
	'''
	width, height = img.size[0], img.size[1]
	height_ = int(width * height_to_width)
	if height_ > height:
		return img.crop((
			int((width - height / height_to_width) / 2), 0,
			int((width + height / height_to_width) / 2), height
		))
	else:
		return img.crop((
			0, int((height - height_) / 2),
			width, int((height + height_) / 2)
		))


def batch_resize(subject_dir, dst_size=(227, 227), src_folder='trimmed', overwrite=False):
	'''
	resize all frame images in subject_dir, output to /resized
	:param subject_dir: the subject's directory
	:param dst_size: destined image size (width, height)
	:param src_folder: subdirectory to get images
	:param overwrite: whether to cover the existing 'resized' folder
	:return dst_dir
	'''
	print('\nWorking in %s...' % subject_dir)
	old_path = os.getcwd()
	dst_dir = os.path.join(old_path, subject_dir, 'resized')
	if os.path.exists(dst_dir):
		if overwrite == True:
			shutil.rmtree(dst_dir)
		else:
			raise FileExistsError('the directory %s already exists.' % dst_dir)
	os.mkdir(dst_dir)

	os.chdir(os.path.join(subject_dir, src_folder))
	folders = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	for folder in folders:
		print('subfolder %s' % folder)
		dst_folder = os.path.join(dst_dir, folder)
		os.mkdir(dst_folder)
		os.chdir(folder)
		files = list(filter(lambda x: x.endswith('.jpg'), os.listdir('.')))

		# start threads
		n = len(files)
		progress = tqdm(total=n)
		if n < 10:
			print('1 thread working...')
			thread1 = MyThread(files, subject_dir, dst_size, dst_folder, progress)
			thread1.start()
			thread1.join()
		elif n < 20:
			print('2 threads working...')
			thread1 = MyThread(files[: n // 2], subject_dir, dst_size, dst_folder, progress)
			thread2 = MyThread(files[n // 2:], subject_dir, dst_size, dst_folder, progress)
			thread1.start()
			thread2.start()
			thread1.join()
			thread2.join()
		else:
			print('6 threads working...')
			threads = [
				MyThread(files[i * n // 6: (i + 1) * n // 6], subject_dir, dst_size, dst_folder, progress)
				for i in range(6)
			]
			for thread in threads: thread.start()
			for thread in threads: thread.join()
		# joined several threads
		os.chdir('..')

	os.chdir(old_path)
	return os.path.abspath(dst_dir)


if __name__ == '__main__':
	# CWD = '/Volumes/TOSHIBA EXT/Analysis/Data/Study2/subjects'
	CWD = '/Users/james/MobileProximateSpeech/Analysis/Data/Study2/subjects'
	os.chdir(CWD)
	# subjects = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	subjects = ['hsd']
	for subject in subjects:
		batch_resize(subject, src_folder='trimmed', overwrite=False)
