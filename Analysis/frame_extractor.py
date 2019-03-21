import os
import cv2
import shutil
import threading


class ExtractThread(threading.Thread):

	def __init__(self, extract_list, task_list, user_path, out_path):
		self.extract_list = extract_list
		self.task_list = task_list
		self.user_path = user_path
		self.out_path = out_path
		super().__init__()

	def run(self):
		for i in range(len(self.extract_list)):
			f = self.extract_list[i]
			print(user, f)
			mov_file = os.path.join(self.user_path, f[:-4] + '.mp4')
			dst_path = os.path.join(self.out_path, f[:-4] + ' fromStudy1')
			if os.path.exists(dst_path):
				shutil.rmtree(dst_path)
			if not os.path.exists(dst_path):
				os.makedirs(dst_path)
			s, t = 0, 0
			if self.task_list[i] == '接听':
				s, t = 0.5, 1.2
			elif self.task_list[i] == '裤兜':
				s, t = 1.0, 2.0
			else:
				s, t = 1.1, 1.2
			extract_frames(mov_file, dst_path, start_time=s, minus_time=t)


def extract_frames(mov_file, dst_path, start_time=0., minus_time=0.):

	mov_name = os.path.basename(mov_file)
	# assert video_name == video_path

	# get the video handle
	cam = cv2.VideoCapture(mov_file)
	fps = cam.get(cv2.CAP_PROP_FPS)
	tot_frame = cam.get(cv2.CAP_PROP_FRAME_COUNT)

	cur_frame = 0
	start_frame = int(start_time * fps)
	end_frame = int(tot_frame - minus_time * fps)
	step = 0  # count valid frame
	stride = 10
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

			# todo if brightness < threshold: continue...

			step += 1
			if step == stride:  # output a frame per `stride` valid framed
				step = 0  # zero the step counter

				dst_file = os.path.join(dst_path, 'frame%d.jpg' % cur_frame)
				# print('Creating...' + dst_path)

				cv2.imwrite(dst_file, frame)
		else:
			# no frame to extract
			break

	# Release all space and windows once done
	cam.release()
	cv2.destroyAllWindows()


if __name__ == '__main__':
	mov_path = '../Data/Study1/'
	pic_path = '../Data/Study2/subjects/'
	# subjects = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	# subjects = ['yzc']
	subjects = os.listdir(mov_path)
	for user in subjects:
		user_path = os.path.join(mov_path, user)
		out_path = os.path.join(pic_path, user, 'original')
		if not os.path.exists(out_path):
			os.makedirs(out_path)
		file_list = list(filter(lambda x: x.endswith('.txt'), os.listdir(user_path)))
		extract_list, task_list = [], []
		for f in file_list:
			file = open(os.path.join(user_path, f), "r", encoding='utf-8')
			lines = []
			for i in range(5):
				lines.append(file.readline())
			task_id = int(lines[0].split(' ')[0])
			task_description = lines[3].strip().split(' ')[-1]
			if task_id < 32 or task_id > 37:
				continue
			extract_list.append(f)
			task_list.append(task_description)
			out_txt = os.path.join(out_path, f[:-4] + ' fromStudy1.txt')
			output = open(out_txt, 'w', encoding='utf-8')
			output.truncate()
			output.write(task_description + ' Study1\n')
			output.write(lines[0])
			output.close()

		thread_num = 5
		mov_num = len(extract_list)
		threads = []
		for i in range(thread_num):
			l, r = i * mov_num // thread_num, (i + 1) * mov_num // thread_num
			threads.append(ExtractThread(extract_list[l: r], task_list[l: r], user_path, out_path))
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()
		'''
		for f in extract_list:
			print(f)
			mov_file = os.path.join(user_path, f[:-4] + '.mp4')
			dst_path = os.path.join(out_path, f[:-4] + ' fromStudy1')
			if os.path.exists(dst_path):
				shutil.rmtree(dst_path)
			os.makedirs(dst_path)
			extract_frames(mov_file, dst_path, start_time=1.1, minus_time=1.2)
		'''