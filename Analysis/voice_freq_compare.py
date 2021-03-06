import os
import wave
import struct
import numpy as np
import matplotlib.pyplot as plt


fft_size = 512
sample_rate = 32000

positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子', '竖屏握持，上端遮嘴',
			'水平端起，倒话筒', '话筒', '横屏']
all_pos = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子', '竖屏握持，上端遮嘴',
			'水平端起，倒话筒', '话筒', '横屏',
		   '手上正面', '手上反面', '桌上正面', '桌上反面',
		   '耳旁打电话', '裤兜']


freqs = np.linspace(0, sample_rate / 2, fft_size / 2 + 1)
freq_tot = np.zeros((4, len(freqs)))
count = np.zeros(4)


def calc_wav(file_path, type, output):
	try:
		wavefile = wave.open(file_path, 'r')
	except wave.Error:
		return
	nchannels = wavefile.getnchannels()
	sample_width = wavefile.getsampwidth()
	framerate = wavefile.getframerate()
	numframes = wavefile.getnframes()
	time = numframes / framerate

	print(nchannels, sample_width, framerate, numframes, time)

	y = np.zeros(numframes)
	for i in range(numframes):
		val = wavefile.readframes(1)
		left = val[0:2]
		# right = val[2:4]
		if left != val:
			while True:
				print("Mono")
		v = struct.unpack('h', left)[0]
		y[i] = v
	s = 0
	sum = np.zeros(len(freqs))
	cnt = 0
	while s + fft_size < len(y):
		data = y[s:s + fft_size]
		xf = np.fft.rfft(data) / fft_size
		xfp = 20 * np.log10(np.clip(np.abs(xf), 1e-20, 1e100))
		s += fft_size

		if output != 0:
			cnt += 1
			sum += xfp
			if cnt == 20:
				for f in sum:
					output.write(str(f / cnt) + '\n')
				cnt = 0
				sum = np.zeros(len(freqs))
		else:
			for i in range(len(freqs)):
				freq_tot[type][i] += xfp[i]
			count[type] += 1


def get_xfp(data):
	xf = np.fft.rfft(data) / fft_size
	xfp = 20 * np.log10(np.clip(np.abs(xf), 1e-20, 1e100))
	return xfp


def calc_wav_stereo(file_path, type, output):
	try:
		wavefile = wave.open(file_path, 'r')
	except wave.Error:
		return
	nchannels = wavefile.getnchannels()
	sample_width = wavefile.getsampwidth()
	framerate = wavefile.getframerate()
	numframes = wavefile.getnframes()
	time = numframes / framerate

	print(nchannels, sample_width, framerate, numframes, time)

	y, z = np.zeros(numframes), np.zeros(numframes)

	for i in range(numframes):
		val = wavefile.readframes(1)
		left, right = val[0:2], val[2:4]
		y[i] = struct.unpack('h', left)[0]
		z[i] = struct.unpack('h', right)[0]
	s = 0
	sum_l, sum_r = np.zeros(len(freqs)), np.zeros(len(freqs))
	cnt = 0

	while s + fft_size < len(y):
		xfp_l = get_xfp(y[s:s + fft_size])
		xfp_r = get_xfp(z[s:s + fft_size])
		s += fft_size
		if output != 0:
			cnt += 1
			sum_l += xfp_l
			sum_r += xfp_r
			if cnt == 20:
				for f in sum_l:
					output.write(str(f / cnt) + '\n')
				for f in sum_r:
					output.write(str(f / cnt) + '\n')
				cnt = 0
				sum_l, sum_r = np.zeros(len(freqs)), np.zeros(len(freqs))
		else:
			for i in range(len(freqs)):
				freq_tot[type][i] += xfp_l[i]
				freq_tot[type+1][i] += xfp_r[i]
			count[type] += 1
			count[type+1] += 1


def visualization_stereo(path):
	global freq_tot, count
	for u in user_list:
		user_path = os.path.join(path, u)
		file_list = os.listdir(user_path)
		for f in file_list:
			if f[-4:] != '.txt':
				continue
			file = open(os.path.join(user_path, f), "r", encoding='utf-8')
			lines = file.readlines()
			type = 0
			if lines[1].strip() in positive:
				type = 2
			wav_file = os.path.join(user_path, f[:-4] + '.wav')
			calc_wav_stereo(wav_file, type, 0)
		for t in range(4):
			for i in range(len(freqs)):
				freq_tot[t][i] /= count[t]
		print(freq_tot)
		plt.plot(freqs, freq_tot[0], label='distant left')
		plt.plot(freqs, freq_tot[1], label='distant right')
		plt.plot(freqs, freq_tot[2], label='close left')
		plt.plot(freqs, freq_tot[3], label='close right')
		plt.title(u)
		plt.legend()
		plt.show()
		freq_tot = np.zeros((4, len(freqs)))
		count = np.zeros(4)


def visualization_stereo_by_task(path):
	global freq_tot, count
	out_path = '../Data/voice visualization'
	for u in user_list:
		freq_tot = np.zeros((len(all_pos) * 2, len(freqs)))
		count = np.zeros(len(all_pos) * 2)
		user_path = os.path.join(path, u)
		file_list = os.listdir(user_path)
		for f in file_list:
			if f[-4:] != '.txt':
				continue
			file = open(os.path.join(user_path, f), "r", encoding='utf-8')
			lines = file.readlines()
			task_pos = lines[1].strip()
			for i in range(len(all_pos)):
				if (task_pos == all_pos[i]):
					type = i
					break
			type *= 2
			wav_file = os.path.join(user_path, f[:-4] + '.wav')
			calc_wav_stereo(wav_file, type, 0)
		for t in range(len(freq_tot)):
			for i in range(len(freqs)):
				freq_tot[t][i] /= count[t]
		for i in range(len(all_pos)):
			plt.plot(freqs, freq_tot[i*2], label='down')
			plt.plot(freqs, freq_tot[i*2+1], label='up')
			pic_name = u + ' ' + all_pos[i]
			plt.title(pic_name, fontproperties='SimHei')
			plt.legend()
			plt.savefig(os.path.join(out_path, pic_name + '.png'), format='png')
			plt.show()




def visualization():
	global freq_tot, count
	for u in user_list:
		user_path = os.path.join(path, u)
		trimmed_path = os.path.join(user_path, 'trimmed')
		filtered_path = os.path.join(user_path, 'filtered')
		file_list = os.listdir(trimmed_path)

		for f in file_list:
			if f.find('.') != -1:
				continue
			description_file = os.path.join(filtered_path, f + '.txt')
			file = open(description_file, "r", encoding='utf-8')
			lines = file.readlines()
			type = 0
			if lines[1].strip() in positive:
				type = 1
			if lines[2].strip() == '大声':
				type += 2
			task_path = os.path.join(trimmed_path, f)
			wav_list = os.listdir(task_path)
			print(description_file)
			for w in wav_list:
				if w[-4:] != '.wav':
					continue
				calc_wav(os.path.join(task_path, w), type, 0)

		for t in range(4):
			for i in range(len(freqs)):
				freq_tot[t][i] /= count[t]
		print(freq_tot)
		plt.plot(freqs, freq_tot[0], label='distant low')
		plt.plot(freqs, freq_tot[1], label='close low')
		plt.plot(freqs, freq_tot[2], label='distant loud')
		plt.plot(freqs, freq_tot[3], label='close loud')
		plt.title(u)
		plt.legend()
		plt.show()
		freq_tot = np.zeros((4, len(freqs)))
		count = np.zeros(4)


'''
def output_freqs(feature_path):
	for u in user_list:
		# if u != 'yzc':
			# continue
		user_path = os.path.join(path, u)
		trimmed_path = os.path.join(user_path, 'trimmed')
		filtered_path = os.path.join(user_path, 'filtered')
		file_list = os.listdir(trimmed_path)

		out_dir = os.path.join(feature_path, u)
		if not os.path.exists(out_dir):
			os.makedirs(out_dir)
		for f in file_list:
			if f.find('.') != -1:
				continue
			description_file = os.path.join(filtered_path, f + '.txt')
			file = open(description_file, "r", encoding='utf-8')
			lines = file.readlines()
			task_id = lines[0].strip().replace("/", "_").replace(":", "_").replace(" ", "")
			out_file = os.path.join(out_dir, task_id + ".txt")
			output = open(out_file, 'w', encoding='utf-8')
			output.write(lines[1])
			output.write(lines[2])
			output.write(str(len(freqs)) + '\n')
			task_path = os.path.join(trimmed_path, f)
			wav_list = os.listdir(task_path)
			print(description_file)
			for w in wav_list:
				if w[-4:] != '.wav':
					continue
				calc_wav(os.path.join(task_path, w), 0, output)
'''


def output_freqs(feature_path):
	for u in user_list:
		if u in ['wwn', 'wj', 'zfs']:
			continue
		user_path = os.path.join(path, u)
		file_list = os.listdir(user_path)
		out_path = os.path.join(feature_path, u)
		if not os.path.exists(out_path):
			os.makedirs(out_path)
		for f in file_list:
			if f.endswith('.wav'):
				description_file = os.path.join(user_path, f[:-4] + '.txt')
				file = open(description_file, "r", encoding='utf-8')
				lines = file.readlines()
				task_id = lines[0].strip().replace("/", "_").replace(":", "_").replace(" ", "")
				out_file = os.path.join(out_path, task_id + ".txt")
				output = open(out_file, 'w', encoding='utf-8')
				output.write(lines[1])
				output.write(lines[2])
				output.write(str(len(freqs) * 2) + '\n')
				print(u, f)
				calc_wav_stereo(os.path.join(user_path, f), 0, output)


if __name__ == "__main__":
	path = '../Data/Trimmed Stereo 32000Hz/'
	user_list = os.listdir(path)
	visualization_stereo_by_task(path)
	# visualization_stereo(path)
	# output_freqs('../Data/voice feature/')
	# visualization()



