
class FrameList:
    def __init__(self):
        self.type = ""
        self.time_stamp, self.accuracy = [], []
        self.value = []

    def get_data_len(self):
        return len(self.value)

    def get_min_data(self):
        tmp = 1e100
        for values in self.value:
            tmp = min(tmp, min(values))
        return tmp

    def get_max_data(self):
        tmp = -1e100
        for values in self.value:
            tmp = max(tmp, max(values))
        return tmp


class Data:

    start_time_millis, start_up_time_millis, start_elapsed_realtime_nanos = 0, 0, 0
    min_time, max_time = 0, 0
    type_to_list = {}

    def __init__(self):
        self.type_to_list = {}

    def read(self, file_path, show_msg=True):
        f = open(file_path, "r")
        lines = f.readlines()
        f.close()

        self.start_time_millis = int(lines[0])
        self.start_up_time_millis = int(lines[1])
        self.start_elapsed_realtime_nanos = int(lines[2])
        for line in lines[3:]:
            self.__add_frame(line)

    def clear(self):
        self.min_time = self.max_time = 0
        self.start_time_millis = 0
        self.start_up_time_millis = 0
        self.start_elapsed_realtime_nanos = 0
        self.type_to_list.clear()

    def __add_frame(self, line):
        data = line.split()
        type_name = data[0]
        if type_name not in self.type_to_list:
            self.type_to_list.setdefault(type_name, FrameList())
            frame_list = self.type_to_list[type_name]
            frame_list.type = type_name

        frame_list = self.type_to_list[type_name]
        frame_list.time_stamp.append(int(data[1]))
        self.max_time = max(int(data[1]), self.max_time)
        frame_list.accuracy.append(int(data[2]))

        for i in range(len(data) - 3):
            if i >= len(frame_list.value):
                frame_list.value.append([])
            frame_list.value[i].append(float(data[i+3]))

    def get_types(self):
        type_list = []
        for t in self.type_to_list:
            type_list.append(t)
        return type_list

    def get_list(self, type_name) -> 'FrameList':
        if type_name in self.type_to_list:
            return self.type_to_list[type_name]

    def get_max_time(self):
        return self.max_time
