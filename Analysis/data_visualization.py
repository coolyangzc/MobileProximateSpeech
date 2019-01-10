import data_reader


data = data_reader.Data()
data.read("../Data/181228 17_08_01.txt")

for d in data.frame_list['ACCELEROMETER']:
    print(d.time_stamp)




