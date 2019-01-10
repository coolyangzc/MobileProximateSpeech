import re


class Frame:
    def __init__(self):
        self.type = ""
        self.time_stamp, self.accuracy = 0, 0
        self.value = []


class Data:

    start_time_millis, start_up_time_millis, start_elapsed_realtime_nanos = 0, 0, 0
    frame_list = {}

    def read(self, file_path, show_msg = True):
        f = open(file_path, "r")
        lines = f.readlines()
        f.close()

        self.start_time_millis = int(lines[0])
        self.start_up_time_millis = int(lines[1])
        self.start_elapsed_realtime_nanos = int(lines[2])
        for line in lines[3:]:
            f = line_to_frame(line)
            if f.type not in self.frame_list:
                self.frame_list.setdefault(f.type, [])
            self.frame_list[f.type].append(f)


def line_to_frame(line):
    f = Frame()
    data = line.split()
    f.type = data[0]
    f.time_stamp = int(data[1])
    f.accuracy = int(data[2])
    for v in data[3:]:
        f.value.append(float(v))
    return f
