import socket
import math
from collections import deque
from sklearn.externals import joblib
from motion_feature import extract_sensor_feature
from time import ctime

HOST = '192.168.1.57'
PORT = 8888
res, last_time = 0, 0

sensor_list = ['ACCELEROMETER', 'LINEAR_ACCELERATION', 'GRAVITY', 'GYROSCOPE', 'PROXIMITY']


def work_sensor(sensor_name, queue, start_time, end_time):
	arr = [[] for i in range(len(queue[0]) - 1)]
	for frame in queue:
		# print(q, start_time, end_time)
		if frame[0] < start_time:
			continue
		if frame[0] > end_time:
			break
		for i in range(len(frame) - 1):
			arr[i].append(frame[i+1])
	# print('arr: ', arr)
	# print(sensor_name, extract_sensor_feature(arr, sensor_name))
	return extract_sensor_feature(arr, sensor_name)


def work(data):
	# print("trimmed: " + data + '\n')
	if len(data) == 0:
		return
	item = data.split(' ')
	c = -1
	for i in range(len(sensor_list)):
		if (sensor_list[i] == item[0]):
			c = i
			break
	val = []
	try:
		for i in range(len(item) - 1):
			val.append(float(item[i+1]))
	except ValueError:
		return
	q[c].append(val)
	t = val[0]
	s = t - 2000
	while q[c][0][0] < s:
		q[c].popleft()
	global last_time
	if c != 0 or t - 200 < last_time:
		return
	last_time = t
	feature = []
	m = (s + t) / 2
	for i in range(len(sensor_list)):
		feature.extend(work_sensor(sensor_list[i], q[i], s, m))
		feature.extend(work_sensor(sensor_list[i], q[i], m, t))
	for f in feature:
		if math.isnan(f) or math.isinf(f):
			return
	new_res = clf.predict([feature])[0]
	print('feature', feature)
	print(new_res)
	global res
	if new_res != res:
		res = new_res
		print(res)


if __name__ == "__main__":
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
		s.bind((HOST, PORT))
	except socket.error as err:
		print('Bind Failed, Error Code: ' + str(err[0]) + ' ,Message: ' + err[1])
	print('Socket Bind Success!')

	s.listen(5)
	print('Socket is now listening')

	q = []
	for i in range(len(sensor_list)):
		q.append(deque())
		q[i].append([0 for i in range(3+1)])

	clf = joblib.load("motion_model.m")
	buffer = ''
	while True:
		conn, addr = s.accept()
		print('Connect with ' + addr[0] + ':' + str(addr[1]))
		while True:
			data = conn.recv(512).decode()
			if not data:
				break
			# print('data:' + data)
			buffer += data
			while True:
				sp = buffer.find('#')
				if sp == -1:
					break
				work(buffer[:sp])
				buffer = buffer[sp+1:]
			# conn.send(('[%s] %s' % (ctime(), data)).encode())
			# print('[%s] %s' % (ctime(), data))

		conn.close()
		print('client disconnected')
	s.close()