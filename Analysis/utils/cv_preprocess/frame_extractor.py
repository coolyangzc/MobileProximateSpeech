# Importing all necessary libraries
import os
import shutil
import threading

import cv2
from tqdm import tqdm

from utils.tools import suffix_filter


def extract_frames(video_path, start_time=0., minus_time=0., stride_time=None, stride_frame=10,
				   threshold=None, overwrite=False, progress_bar=False):
	'''
	从单个视频中提取帧，输出到子目录
	extract picture frames from mp4 video, starting from `start_time`, ending at `time duration of the video - end_time`
	this function will output all the picture frames to a sub folder which shares the same name as the basename of `video_path`

	:param video_path: str, mp4 video path
	:param start_time: float, start time in seconds
	:param minus_time: float, length minus time in seconds
	:param stride_time: float, how long to skip after one output frame (in seconds)
	:param stride_frame: int, how many frames to skip after one output frame
	:param threshold: float, how bright a frame should at least be to be regarded as valid
	:param overwrite: bool, whether to overwrite when destined path already exists
	:param progress_bar: whether to display a progress bar
	'''
	old_path = os.getcwd()
	try:
		os.chdir(os.path.dirname(video_path))
	except OSError:
		pass
	video_name = os.path.basename(video_path)
	# assert video_name == video_path

	# creating a sub folder
	dst_dir = video_name.split('.')[0]
	if os.path.exists(dst_dir):
		if overwrite==True:
			shutil.rmtree(dst_dir)
		else:
			os.chdir(old_path)
			raise FileExistsError
	os.makedirs(dst_dir)

	# get the video handle
	cam = cv2.VideoCapture(video_name)
	fps = cam.get(cv2.CAP_PROP_FPS)
	tot_frame = cam.get(cv2.CAP_PROP_FRAME_COUNT)

	cur_frame = 0
	start_frame = int(start_time * fps)
	end_frame = int(tot_frame - minus_time * fps)
	step = 0  # count valid frame
	stride = int(stride_time * fps) if stride_time is not None else stride_frame
	progress = tqdm(total=(end_frame - start_frame)) if progress_bar else None
	while True:
		# reading from frame
		ret, frame = cam.read()

		if ret:
			# move current position forward
			cur_frame += 1

			# outside the range, skip
			if cur_frame <= start_frame:
				continue
			elif cur_frame > end_frame:
				break
			if progress_bar: progress.update()

			# todo if brightness < threshold: continue...

			step += 1
			if step == stride:  # output a frame per `stride` valid framed
				step = 0  # zero the step counter

				dst_path = os.path.join(dst_dir, 'frame%d.jpg' % cur_frame)
				# print('Creating...' + dst_path)

				# writing the extracted images
				cv2.imwrite(dst_path, frame)
		else:
			# no frame to extract
			break

	# Release all space and windows once done
	cam.release()
	cv2.destroyAllWindows()

	os.chdir(old_path)


def extract_frames_in_dir(wkdir, start_time=0., minus_time=0., stride_time=None, stride_frame=10, threshold=None,
						  overwrite=False, n_jobs=2):
	'''
	从视频目录中批量提取帧，输出到许多子目录
	extract picture frames from mp4 video directory

	:param wkdir: str, directory of mp4 videos
	:param start_time: float, start time in seconds
	:param minus_time: float, length minus time in seconds
	:param stride_time: float, how long to skip after one output frame (in seconds)
	:param stride_frame: int, how many frames to skip after one output frame
	:param threshold: float, how bright a frame should at least be to be regarded as valid
	:param overwrite: bool, whether to overwrite when destined path already exists
	:param n_jobs: int, how many threads to start
	'''
	old_path = os.getcwd()
	os.chdir(wkdir)
	print('Extracting frames in directory %s...' % wkdir)
	video_paths = suffix_filter(os.listdir('.'), suffix='.mp4')

	n_video = len(video_paths)
	progress = tqdm(total=n_video)
	threads = [
		MyThread(video_paths[i * n_video // n_jobs: (i + 1) * n_video // n_jobs],
				 start_time, minus_time, stride_time, stride_frame, threshold, overwrite, progress)
		for i in range(n_jobs)
	]
	for thread in threads: thread.start()
	for thread in threads: thread.join()

	os.chdir(old_path)


class MyThread(threading.Thread):
	def __init__(self, video_paths, start_time, minus_time, stride_time, stride_frame, threshold, overwrite, progress):
		self.video_paths = video_paths
		self.start_time = start_time
		self.minus_time = minus_time
		self.stride_time = stride_time
		self.stride_frame = stride_frame
		self.threshold = threshold
		self.overwrite = overwrite
		self.progress = progress
		super().__init__()

	def run(self):
		for video_path in self.video_paths:
			try:
				extract_frames(video_path,
							   start_time=self.start_time, minus_time=self.minus_time, stride_time=self.stride_time,
							   stride_frame=self.stride_frame, threshold=self.threshold, overwrite=self.overwrite)
			except FileExistsError:
				pass
			self.progress.update()


if __name__ == '__main__':
	CWD = '/Volumes/TOSHIBA EXT/Analysis/Data/Study2/subjects'
	os.chdir(CWD)
	# subjects = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	subjects = ['jcq']
	print(subjects)

	for wkdir in subjects:
		wkdir = os.path.join(wkdir, 'original')
		extract_frames_in_dir(wkdir, stride_frame=10, start_time=1.1, minus_time=1.2, overwrite=False, n_jobs=3)
