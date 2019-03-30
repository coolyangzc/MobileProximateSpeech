import os
import shutil
import threading
from PIL import Image


class MyThread(threading.Thread):
	def __init__(self, files, folder_path, dst_size, dst_folder):
		self.files = files
		self.folder_path = folder_path
		self.dst_size = dst_size
		self.dst_folder = dst_folder
		super().__init__()

	def run(self):
		for file in self.files:
			try:
				img = Image.open(os.path.join(self.folder_path, file))
			except:
				print('cannot open', self.folder_path, file)
				continue
			img = auto_crop(img, self.dst_size[1] / self.dst_size[0])
			img = img.resize(self.dst_size, Image.LANCZOS)  # resize image
			img.save(os.path.join(self.dst_folder, file))


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


def batch_resize(subject, dst_size=(227, 227), src_folder='trimmed', overwrite=False):
	dst_dir = os.path.join(path, subject, 'resized')
	if os.path.exists(dst_dir):
		if overwrite:
			shutil.rmtree(dst_dir)
	if not os.path.exists(dst_dir):
		os.makedirs(dst_dir)
	user_path = os.path.join(path, subject, src_folder)
	folders = list(filter(lambda x: os.path.isdir(os.path.join(user_path, x)), os.listdir(user_path)))
	print(folders)
	for folder in folders:
		print(subject, folder)
		dst_folder = os.path.join(dst_dir, folder)
		os.makedirs(dst_folder)
		folder_path = os.path.join(user_path, folder)
		files = list(filter(lambda x: x.endswith('.jpg'), os.listdir(folder_path)))
		n = len(files)
		threads = [
			MyThread(files[i * n // 6: (i + 1) * n // 6], folder_path, dst_size, dst_folder)
			for i in range(6)
		]
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()


if __name__ == '__main__':
	path = '../Data/Study2/fixed subjects'
	subjects = os.listdir(path)
	#subjects = ['yzc']
	for subject in subjects:
		batch_resize(subject, dst_size=(192, 108), src_folder='original', overwrite=True)