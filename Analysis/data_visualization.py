import data_reader
from data_reader import FrameList
import matplotlib.pyplot as plt


data = data_reader.Data()
data.read("../Data/181228 17_08_01.txt")

acc_list = data.get_list('ACCELEROMETER')

plt.figure(1)
for i in range(acc_list.get_data_len()):
    plt.plot(acc_list.time_stamp, acc_list.value[i])
plt.show()
