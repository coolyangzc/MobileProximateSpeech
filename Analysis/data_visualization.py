import data_reader
import matplotlib.pyplot as plt


data = data_reader.Data()
data.read("../Data/181228 17_08_01.txt")

acc_list = data.get_list('ACCELEROMETER')
type_list = data.get_types()
type_list.remove('TOUCH')
type_list.remove('CAPACITY')
type_list.sort()

n = 0

print(data.get_max_time())
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
        plt.plot(frame_list.time_stamp, frame_list.value[i], label=i)
    plt.legend()

plt.show()

