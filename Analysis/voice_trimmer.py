import os
from pydub import AudioSegment


start_interval = {  # in millisecond
	'竖直对脸，碰触鼻子': 1100, '竖直对脸，不碰鼻子': 1100,
	'竖屏握持，上端遮嘴': 1100,	 '水平端起，倒话筒': 1100,
	'话筒': 1100, '横屏': 1100,
	'耳旁打电话': 1100, '桌上正面': 1100,
	'手上正面': 1100,

	'桌上反面': 2100, '手上反面': 2100,
	'裤兜': 6000,
}
start_response_time, end_response_time = 300, 300


path = '../Data/Voice Study Stereo 32000Hz'
trimmed_path = '../Data/Trimmed Stereo 32000Hz'
user_list = os.listdir(path)
for u in user_list:
	if u in ['wwn', 'wj', 'zfs']:
		continue
	user_path = os.path.join(path, u)
	file_list = os.listdir(user_path)
	for f in file_list:
		if f.endswith('.wav'):
			description_file = os.path.join(user_path, f[:-4] + '.txt')
			file = open(description_file, "r", encoding='utf-8')
			lines = file.readlines()
			pos = lines[1].strip()
			out_path = os.path.join(trimmed_path, u)
			if not os.path.exists(out_path):
				os.makedirs(out_path)
			out_file = os.path.join(out_path, f[:-4] + ".txt")
			output = open(out_file, 'w', encoding='utf-8')
			for l in lines:
				output.write(l)
			print(os.path.join(user_path, f))
			speech = AudioSegment.from_wav(os.path.join(user_path, f))
			trimmed_speech = speech[start_interval[pos] + start_response_time:-end_response_time]
			trimmed_speech.export(os.path.join(out_path, f), format='wav')
