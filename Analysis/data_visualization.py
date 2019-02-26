import os

import data_reader
import matplotlib.pyplot as plt

remove_sensor = ['TOUCH', 'CAPACITY', 'STEP_COUNTER', 'PRESSURE']


def visualize_file(file_path):
	data = data_reader.Data()
	data.read(file_path)

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
	plt.show()


def compare_files(data_list, show_slope=False):
	type_list = data_list[0].get_types()
	for r in remove_sensor:
		if r in type_list:
			type_list.remove(r)
	type_list.sort()

	for sensor_name in type_list:
		visualize_sensor(data_list, sensor_name, 'value')


def visualize_sensor(data_list, sensor_name, kind='value'):

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
	plt.suptitle(sensor_name, x=0.02, y=0.998, horizontalalignment='left')

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

	plt.show()


def search_files(file_dir):
	# files = ['../Data/190111 14_40_17.txt', #'../Data/190111 14_40_36.txt',
	#         '../Data/190111 14_40_47.txt', '../Data/190111 14_40_56.txt',
	#         '../Data/190114 10_36_37.txt']
	# for file in files:
	# visualize_file(file)
	file_list = os.listdir(file_dir)
	files = []
	for file_name in file_list:
		if file_name[-4:] == ".txt":
			files.append(file_dir + file_name)
	return files


def read_data(file_path_list):
	data_list = []
	for file_path in file_path_list:
		d = data_reader.Data()
		d.read(file_path)
		data_list.append(d)
	return data_list


file_paths = search_files('../Data/190226/')
data_list = read_data(file_paths)
# visualize_file(file_paths[0])

# visualize_sensor(data_list, 'ROTATION_VECTOR')
# visualize_sensor(data_list, 'LINEAR_ACCELERATION')
# visualize_sensor(data_list, 'LINEAR_ACCELERATION', 'sqrt')
# visualize_sensor(data_list, 'LINEAR_ACCELERATION', 'sum')
# visualize_sensor(data_list, 'LINEAR_ACCELERATION', 'slope 1000')
visualize_sensor(data_list, 'ROTATION_VECTOR')
visualize_sensor(data_list, 'LINEAR_ACCELERATION', 'sqrt')
visualize_sensor(data_list, 'LINEAR_ACCELERATION')
visualize_sensor(data_list, 'LINEAR_ACCELERATION', 'sum')



# compare_files(data_list, False)
# compare_files(files, True)
