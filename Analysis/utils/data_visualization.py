import os
import random

from utils import data_reader, logger, tools
from tqdm import tqdm  # progressbar
import matplotlib.pyplot as plt

remove_sensor = ['TOUCH', 'CAPACITY', 'STEP_COUNTER', 'PRESSURE']

RUN_TIME = tools.date_time()  # name of save directory


def visualize_file(file_path, save_dir='../output/%s/' % RUN_TIME, show_msg=False):
	"""
	visualize data from a single .txt file

	:param file_path: given file path
	:param save_dir: saving directory
	:param show_msg: bool, whether to print message
	"""
	if show_msg: print('visualizing %s...  ' % file_path, end='')
	data = data_reader.Data()
	data.read(file_path)
	if show_msg: print(data.description)

	type_list = data.get_types()
	type_list.remove('TOUCH')
	type_list.remove('CAPACITY')
	type_list.sort()

	n = 0

	plt.figure(figsize=(10, 40))
	for t in type_list:
		n += 1
		plt.subplot(len(type_list), 1, n)
		plt.xlim(0, data.get_max_time())
		frame_list = data.get_list(t)

		plt.title(t)
		for i in range(frame_list.get_data_way()):
			if len(frame_list.value[i]) <= 100:
				plot_format = 'x:'
			else:
				plot_format = '-'
			plt.plot(frame_list.time_stamp, frame_list.value[i], plot_format, label=i)

		plt.legend()
	plt.suptitle(file_path, x=0.02, y=0.998, horizontalalignment='left')
	if not os.path.exists(save_dir): os.mkdir(save_dir)
	plt.savefig(os.path.join(save_dir, 'file_' + tools.suffix_conv(file_path, '.png')))
	plt.show()


def compare_files(data_list, show_slope=False):
	print('comparing files...')
	type_list = data_list[0].get_types()
	for r in remove_sensor:
		if r in type_list:
			type_list.remove(r)
	type_list.sort()
	print('type_list: ', type_list)
	for sensor_name in type_list:
		visualize_sensor(data_list, sensor_name, 'value')


def visualize_sensor(data_list, sensor_name, kind='value', save_dir='../output/%s/' % RUN_TIME, title=None):
	"""
	visualize data collected by a sensor

	:param data_list: list of Data()
	:param sensor_name: name string of sensor, e.g. 'ACCELEROMETER'
	:param kind: 'value', 'slope' or 'sum'
	:param save_dir: directory to save the figure, default: './output/SAVE_PREFIX/'
	:param title: extra assigned title of figure
	"""
	if title is None: title = sensor_name
	print('visualizing %s data...' % sensor_name)
	choice_list = []
	max_time = 0
	for d in data_list:
		choice_list.append(d.get_list(sensor_name))
		max_time = max(max_time, d.get_max_time())

	y_min = 1e100
	y_max = -1e100

	for d in choice_list:
		y_min = min(y_min, d.get_min_data(kind))
		y_max = max(y_max, d.get_max_data(kind))

	dis = y_max - y_min

	y_min = y_min - dis * 0.04
	y_max = y_max + dis * 0.04

	n = len(data_list)
	plt.figure(figsize=(9, n * 3))
	plt.suptitle(title, x=0.02, y=0.998, horizontalalignment='left')

	for file_id in range(n):
		plt.subplot(len(data_list), 1, file_id + 1)
		plt.xlim(0, max_time)
		plt.ylim(y_min, y_max)

		data = choice_list[file_id].get_data(kind)
		plt.title(data_list[file_id].file_path + ' ' +
				  data_list[file_id].description + ' ' + kind,
				  fontproperties='SimHei')
		for i in range(len(data)):
			if len(data[i]) <= 100:
				plot_format = 'x:'
			else:
				plot_format = '-'
			plt.plot(choice_list[file_id].time_stamp, data[i], plot_format, label=i)
		plt.legend()

	save_name = title + '.png'
	if not os.path.exists(save_dir): os.mkdir(save_dir)
	plt.savefig(os.path.join(save_dir, save_name))
	plt.show()


def search_files(file_dir: str):
	""" collect all .txt files in the given file directory

	:param file_dir: file directory
	:return: list of .txt files
	"""
	print('searching files %s ...' % file_dir)
	file_list = os.listdir(file_dir)
	files = []
	for file_name in file_list:
		if file_name[-4:] == ".txt":
			files.append(file_dir + file_name)
	print('files searched.')
	return files


def get_data_list(file_path_list: list):
	""" get Data list from file path list

	:param file_path_list: list of file path
	:return: list of Data()
	"""
	print('reading data...')
	data_list = []
	for file_path in tqdm(file_path_list):  # show progress bar
		d = data_reader.Data()
		d.read(file_path)
		data_list.append(d)
	print('data read.')
	return data_list


if __name__ == '__main__':
	logger.DualLogger('../logs/' + RUN_TIME + 'data visualization.txt') # setup logger
	file_dir1 = '../Data/Study1/Fengshi Zheng/'  # data of Fengshi Zheng
	file_dir1_P = '../Data/Study1/Fengshi Zheng/Positive/'  # Positive data of Fengshi Zheng
	file_dir1_N = '../Data/Study1/Fengshi Zheng/Negative/'  # Negative data of Fengshi Zheng
	file_dir2 = '../Data/Study1/123/'  # just for debugging
	file_dir2_P = '../Data/Study1/123/Positive/'
	file_dir2_N = '../Data/Study1/123/Negative/'

	# watched_sensors = ['ROTATION_VECTOR', 'ACCELEROMETER', 'LINEAR_ACCELEROMETER', 'GYROSCOPE', 'PROXIMITY']
	watched_sensors = ['ROTATION_VECTOR', 'ACCELEROMETER', 'GYROSCOPE', 'PROXIMITY']
	# watched_sensors = ['PROXIMITY']
	print('# Make Comparisons Between P/N Data')

	# 以下为一个随机取样的实验，从正例和反例中各随机选取 n_sample 次实验的数据，然后对比它们在四个传感器数据上的差异
	n_sample = 8

	print('\n## Visualizing Positive Data')
	file_paths = random.choices(search_files(file_dir1_P), k=n_sample)
	data_list = get_data_list(file_paths)
	for sensor in watched_sensors:
		visualize_sensor(data_list, sensor, title='+ %s' % sensor)

	print('\n## Visualizing Negative Data')
	file_paths = random.choices(search_files(file_dir1_N), k=n_sample)
	data_list = get_data_list(file_paths)
	for sensor in watched_sensors:
		visualize_sensor(data_list, sensor, title='- %s' % sensor)

	# visualize_file(file_paths[-1], show_msg=True)
	# visualize_sensor(data_list, 'LINEAR_ACCELERATION')
	# visualize_sensor(data_list, 'LINEAR_ACCELERATION', 'sum')
	# visualize_sensor(data_list, 'LINEAR_ACCELERATION', 'slope 1000')
	# compare_files(data_list, False)
	# compare_files(files, True)

	pass
