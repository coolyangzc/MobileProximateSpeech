import os
import webrtcvad_utils

check_path = '../Data/multi-class/users/'
empty_file_cnt, strange_file_cnt = 0, 0


def print_in_format(t, description):
	print('-' * 40)
	print(description)
	print(t)
	print()
	for i in range(0, len(t), 2):
		print(t[i], t[i+1])
	print()


def check_vad_chunk(file_name, file_dir):
	vad_file = os.path.join(file_dir, file_name + '_vad.txt')
	f_vad = open(vad_file, "r", encoding='utf-8')
	lines = f_vad.readlines()
	f_vad.close()
	t = []
	global empty_file_cnt, strange_file_cnt
	for line in lines:
		data = line.strip().split(' ')
		t.append(float(data[0]))
		t.append(float(data[1]))
	if len(t) == 0:
		empty_file_cnt += 1
		print(file_dir, file_name)
		t = webrtcvad_utils.calc_vad(2, os.path.join(file_dir, file_name + '.wav'))
		print_in_format(t, 'aggressiveness = 2')
		t = webrtcvad_utils.calc_vad(1, os.path.join(file_dir, file_name + '.wav'))
		print_in_format(t, 'aggressiveness = 1')
	elif t[0] < 0.5 or t[0] > 4.0:
		strange_file_cnt += 1


if __name__ == "__main__":
	for u in os.listdir(check_path):
		p = os.path.join(check_path, u)
		for f in os.listdir(p):
			if f.endswith('.wav'):
				check_vad_chunk(f[:-4], p)
	print(empty_file_cnt, strange_file_cnt)