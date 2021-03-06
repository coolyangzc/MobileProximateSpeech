
class FrameList:
	def __init__(self):
		self.type = ""
		self.time_stamp, self.accuracy = [], []
		self.value, self.slope, self.sum, self.sqrt = [], [], [], []

	def get_data_way(self):
		return len(self.value)

	def get_data(self, kind='value'):
		if kind[:5] == 'slope':
			k = kind.split()
			if len(k) > 1:
				self.get_slope(int(k[1]))
			else:
				self.get_slope()
			return self.slope
		elif kind == 'sum':
			return self.sum
		elif kind == 'sqrt':
			return self.sqrt
		else:
			return self.value

	def get_min_data(self, kind='value'):
		choice = self.get_data(kind)
		tmp = 1e100
		for data in choice:
			tmp = min(tmp, min(data))
		return tmp

	def get_max_data(self, kind='value'):
		choice = self.get_data(kind)
		tmp = -1e100
		for data in choice:
			tmp = max(tmp, max(data))
		return tmp

	def get_sum(self):
		self.sum.clear()
		for w in range(len(self.value)):
			self.sum.append([])
			s = self.sum[-1]
			v = self.value[w]
			s.append(v[0])
			for i in range(1, len(v)):
				s.append(v[i] + s[i-1])
		return self.sum

	def get_sqrt(self):
		self.sqrt.clear()
		if self.type == 'TOUCH':
			return
		self.sqrt.append([])
		s = self.sqrt[-1]
		for i in range(0, len(self.time_stamp)):
			s.append(0)
			for w in range(len(self.value)):
				s[-1] += self.value[w][i] ** 2
			s[-1] = s[-1] ** 0.5

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
	task_id, user_pos, start_pos, description, hand, phrase = '', '', '', '', '', ''
	file_path = ''
	min_time, max_time = 0, 0
	type_to_list = {}

	def __init__(self):
		self.type_to_list = {}

	def read(self, file_path, show_msg=True):
		f = open(file_path, "r", encoding='utf-8')
		lines = f.readlines()
		f.close()
		self.file_path = file_path
		self.task_id = lines[0].strip().replace("/", "_").replace(":", "_").replace(" ", "")
		self.user_pos = lines[1].split()[1]
		self.start_pos = lines[2].split()[1]
		self.description = lines[3].split()[1]
		self.hand = lines[4].strip()
		self.phrase = lines[5].strip()
		self.start_time_millis = int(lines[6])
		self.start_up_time_millis = int(lines[7])
		self.start_elapsed_realtime_nanos = int(lines[8])

		for line in lines[9:]:
			self.__add_frame(line)
		#for (t, l) in self.type_to_list.items():
			#l.get_sum()
			#l.get_sqrt()

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
