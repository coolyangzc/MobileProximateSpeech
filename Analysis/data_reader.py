
class FrameList:
    def __init__(self):
        self.type = ""
        self.time_stamp, self.accuracy = [], []
        self.value, self.slope = [], []

    def get_data_way(self):
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

    def get_min_slope(self):
        if len(self.slope) == 0:
            self.get_slope()
        tmp = 1e100
        for slopes in self.slope:
            tmp = min(tmp, min(slopes))
        return tmp

    def get_max_slope(self):
        if len(self.slope) == 0:
            self.get_slope()
        tmp = -1e100
        for slopes in self.slope:
            tmp = max(tmp, max(slopes))
        return tmp

    def get_slope(self, time_window=100):
        self.slope.clear()
        for w in range(len(self.value)):
            self.slope.append([])
            slope = self.slope[-1]
            t, v = self.time_stamp, self.value[w]

            slope.append(0)
            window_sum = v[0]
            window_l = 0
            for i in range(1, len(t)):
                while t[i] - t[window_l] > time_window:
                    window_sum -= v[window_l]
                    window_l += 1
                if i == window_l:
                    slope.append(v[i] - v[i - 1])
                else:
                    slope.append(v[i] - window_sum / (i - window_l))
                window_sum += v[i]

        return self.slope



class Data:

    start_time_millis, start_up_time_millis, start_elapsed_realtime_nanos = 0, 0, 0
    description = ''
    min_time, max_time = 0, 0
    type_to_list = {}

    def __init__(self):
        self.type_to_list = {}

    def read(self, file_path, show_msg=True):
        f = open(file_path, "r", encoding='utf-8')
        lines = f.readlines()
        f.close()
        self.description = lines[0]
        print(lines[0])
        self.start_time_millis = int(lines[1])
        self.start_up_time_millis = int(lines[2])
        self.start_elapsed_realtime_nanos = int(lines[3])
        for line in lines[4:]:
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
