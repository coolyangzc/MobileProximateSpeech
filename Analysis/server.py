import socket
from time import ctime
HOST = '192.168.1.57'
PORT = 8888

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
	s.bind((HOST, PORT))
except socket.error as err:
	print('Bind Failed, Error Code: ' + str(err[0]) + ' ,Message: ' + err[1])
print('Socket Bind Success!')

s.listen(5)
print('Socket is now listening')

while True:
	conn, addr = s.accept()
	print('Connect with ' + addr[0] + ':' + str(addr[1]))
	while True:
		data = conn.recv(4096).decode()
		if not data:
			break
		print(data)
		if len(data) > 0:
		# conn.send(('[%s] %s' % (ctime(), data)).encode())
		# print('[%s] %s' % (ctime(), data))

	conn.close()
	print('client disconnected')
s.close()