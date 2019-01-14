import data_reader
import matplotlib.pyplot as plt


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
        if t == 'TOUCH' or t == 'CAPACITY':
            continue
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


def compare_files(file_path_list, show_slope=False):
    data_list = []
    for file_path in file_path_list:
        d = data_reader.Data()
        d.read(file_path)
        data_list.append(d)
    type_list = data_list[0].get_types()
    if 'TOUCH' in type_list:
        type_list.remove('TOUCH')
    if 'CAPACITY' in type_list:
        type_list.remove('CAPACITY')
    type_list.sort()
    max_time = 0
    for d in data_list:
        max_time = max(max_time, d.get_max_time())

    n = len(file_path_list)
    for t in type_list:
        plt.figure(figsize=(10, n*3.5))
        plt.suptitle(t, x=0.02, y=0.998, horizontalalignment='left')

        y_min = 1e100
        y_max = -1e100
        if show_slope:
            for d in data_list:
                d.get_list(t).get_slope(200)
                y_min = min(y_min, d.get_list(t).get_min_slope())
                y_max = max(y_max, d.get_list(t).get_max_slope())
        else:
            for d in data_list:
                y_min = min(y_min, d.get_list(t).get_min_data())
                y_max = max(y_max, d.get_list(t).get_max_data())

        dis = y_max - y_min

        y_min = y_min - dis * 0.05
        y_max = y_max + dis * 0.05
        for file_id in range(n):
            plt.subplot(len(data_list), 1, file_id+1)
            plt.xlim(0, max_time)
            plt.ylim(y_min, y_max)


            frame_list = data_list[file_id].get_list(t)
            if show_slope:
                data = frame_list.slope
                plt.title(file_path_list[file_id] + '(slope)')
            else:
                data = frame_list.value
                plt.title(file_path_list[file_id])
            for i in range(frame_list.get_data_way()):
                if len(data[i]) <= 100:
                    plot_format = 'x:'
                else:
                    plot_format = '-'
                plt.plot(frame_list.time_stamp, data[i], plot_format, label=i)
            plt.legend()
        plt.show()


files = ['../Data/190111 14_40_17.txt', #'../Data/190111 14_40_36.txt',
         '../Data/190111 14_40_47.txt', '../Data/190111 14_40_56.txt',
         '../Data/190114 10_36_37.txt']
#for file in files:
    #visualize_file(file)
compare_files(files, False)
compare_files(files, True)
