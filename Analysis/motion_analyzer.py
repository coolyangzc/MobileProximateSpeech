import os
import data_reader
import webrtcvad_utils


data_path = '../Data/Study1/'
user_list = os.listdir(data_path)
for u in user_list:

	if u != "yzc" and u != "plh":
		continue
	print(u)
	print(os.path.join(data_path, u))
	p = os.path.join(data_path, u)

	files = os.listdir(p)
	for f in files:
		if f[-4:] == ".txt":
			d = data_reader.Data()
			wav_file = f.replace(".txt", ".wav")
			wav_file = os.path.join(p, wav_file)
			print(wav_file)
			t = webrtcvad_utils.calc_vad(1, wav_file)
			print(t)
			# d.read(os.path.join(p, f))
			# print(d.task_id)

