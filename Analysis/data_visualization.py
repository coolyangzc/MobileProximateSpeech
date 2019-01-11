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
        for i in range(frame_list.get_data_len()):
            if len(frame_list.value[i]) <= 100:
                plot_format = 'x:'
            else:
                plot_format = '-'
            plt.plot(frame_list.time_stamp, frame_list.value[i], plot_format, label=i)

        plt.legend()
    plt.suptitle(file_path, x=0.02, y=0.998, horizontalalignment='left')
    plt.show()


visualize_file('../Data/190111 14_40_17.txt')
visualize_file('../Data/190111 14_40_36.txt')
visualize_file('../Data/190111 14_40_47.txt')
visualize_file('../Data/190111 14_40_56.txt')