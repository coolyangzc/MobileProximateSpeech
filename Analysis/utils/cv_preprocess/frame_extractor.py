# Importing all necessary libraries
import os

import cv2
from tqdm import tqdm

from utils.tools import suffix_filter


def extract_frames(video_path, start_time=0., minus_time=0., stride_time=1., threshold=None, progress_bar=False):
	'''
	从视频中提取帧，输出到子目录
	extract picture frames from mp4 video, starting from `start_time`, ending at `time duration of the video - end_time`
	this function will output all the picture frames to a sub folder which shares the same name as the basename of `video_path`

	:param video_path: str, mp4 video path
	:param start_time: float, start time in seconds
	:param minus_time: float, length minus time in seconds
	:param stride_time: float, how long to skip after one output frame (in seconds)
	:param threshold: float, how bright a frame should at least be to be regarded as valid
	:param progress_bar: whether to display a progress bar
	'''
	old_path = os.getcwd()
	try:
		os.chdir(os.path.dirname(video_path))
	except FileNotFoundError:
		pass
	video_name = os.path.basename(video_path)

	# get the video handle
	cam = cv2.VideoCapture(video_name)
	fps = cam.get(cv2.CAP_PROP_FPS)
	tot_frame = cam.get(cv2.CAP_PROP_FRAME_COUNT)

	# creating a sub folder
	dst_dir = video_name.split('.')[0]
	assert not os.path.exists(dst_dir)
	os.makedirs(dst_dir)

	cur_frame = 0
	start_frame = int(start_time * fps)
	end_frame = int(tot_frame - minus_time * fps)
	step = 0  # count valid frame
	stride = int(stride_time * fps)
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


def extract_frames_in_dir(wkdir, start_time=0., minus_time=0., stride_time=1., threshold=None):
	'''
	从视频目录中批量提取帧，输出到许多子目录
	extract picture frames from mp4 video directory

	:param wkdir: str, directory of mp4 videos
	:param start_time: float, start time in seconds
	:param minus_time: float, length minus time in seconds
	:param stride_time: float, how long to skip after one output frame (in seconds)
	:param threshold: float, how bright a frame should at least be to be regarded as valid
	'''
	old_path = os.getcwd()
	os.chdir(wkdir)
	print('Extracting frames in directory %s...' % wkdir)
	video_paths = suffix_filter(os.listdir('.'), suffix='.mp4')
	for video_path in tqdm(video_paths):
		extract_frames(video_path, start_time=start_time, minus_time=minus_time, stride_time=stride_time,
					   threshold=threshold)
	os.chdir(old_path)


if __name__ == '__main__':
	wkdir = '/Users/james/MobileProximateSpeech/Analysis/Data/Study2/test'
	extract_frames_in_dir(wkdir)
