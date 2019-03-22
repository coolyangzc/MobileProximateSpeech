import os
import wave
import numpy as np
import struct
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
from scipy import zeros

import pylab

all_pos = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子', '竖屏握持，上端遮嘴',
			'水平端起，倒话筒', '话筒', '横屏',
		   '手上正面', '手上反面', '桌上正面', '桌上反面',
		   '耳旁打电话', '裤兜']


'''
sample_rate, samples = wavfile.read(path + '/yzc/filtered/190305 10_26_49.wav')
frequencies, times, spectrogram = signal.spectrogram(samples, sample_rate)
print(frequencies.shape, times.shape, spectrogram.shape)
'''


def draw_spectrogram():
	path = '../Data/voice/'
	wavefile = wave.open(path + '/yzc/filtered/190305 10_26_49.wav', 'r')
	nchannels = wavefile.getnchannels()
	sample_width = wavefile.getsampwidth()
	framerate = wavefile.getframerate()
	numframes = wavefile.getnframes()
	time = numframes / framerate

	print("channel", nchannels)
	print("sample_width", sample_width)
	print("framerate", framerate)
	print("numframes", numframes)
	print("time", time)

	y = zeros(numframes)

	# for循环，readframe(1)每次读一个frame，取其前两位，是左声道的信息。右声道就是后两位啦。
	# unpack是struct里的一个函数，用法详见http://docs.python.org/library/struct.html。简单说来就是把＃packed的string转换成原来的数据，无论是什么样的数据都返回一个tuple。这里返回的是长度为一的一个
	# tuple，所以我们取它的第零位。
	for i in range(numframes):
		val = wavefile.readframes(1)
		left = val[0:2]
		right = val[2:4]
		if left != val:
			print("Mono")
		v = struct.unpack('h', left)[0]
		y[i] = v
	print(y.shape)

	s = 0
	fft_size = 1024
	freqs = np.linspace(0, framerate / 2, fft_size / 2 + 1)
	spectrogram = [[] for i in range(len(freqs))]
	count = 0
	while s + fft_size < len(y):
		data = y[s:s+fft_size]
		xf = np.fft.rfft(data) / fft_size
		xfp = 20 * np.log10(np.clip(np.abs(xf), 1e-20, 1e100))
		for i in range(len(freqs)):
			spectrogram[i].append(xfp[i])
		s += fft_size
		count += 1
	times = np.linspace(0, time, count)
	spectrogram = np.array(spectrogram)
	print(times.shape, freqs.shape, spectrogram.shape)
	plt.pcolormesh(times, freqs, spectrogram)
	# plt.imshow(spectrogram)
	plt.ylabel('Frequency [Hz]')
	plt.xlabel('Time [sec]')
	plt.show()
	Fs = framerate
	pylab.specgram(y, NFFT=1024, Fs=Fs, noverlap=900)
	pylab.show()


sample_rate = 32000
fft_size = 512
freqs = np.linspace(0, sample_rate / 2, fft_size / 2 + 1)


def get_xfp(data):
	xf = np.fft.rfft(data) / fft_size
	xfp = 20 * np.log10(np.clip(np.abs(xf), 1e-20, 1e100))
	return xfp


def draw_time_series(wav_file, pic_name):
	wavefile = wave.open(wav_file, 'r')
	nchannels = wavefile.getnchannels()
	sample_width = wavefile.getsampwidth()
	framerate = wavefile.getframerate()
	numframes = wavefile.getnframes()
	time = numframes / framerate

	print("channel", nchannels)
	print("sample_width", sample_width)
	print("framerate", framerate)
	print("numframes", numframes)
	print("time", time)

	y, z = zeros(numframes), zeros(numframes)
	for i in range(numframes):
		val = wavefile.readframes(1)
		left, right = val[0:2], val[2:4]
		y[i] = struct.unpack('h', left)[0]
		z[i] = struct.unpack('h', right)[0]

	times = []
	for i in range(numframes):
		times.append(i / framerate)
	plt.xlabel('Time [s]')
	plt.plot(times, y, label='down')
	plt.plot(times, z, label='up')
	plt.legend()
	if pic_name != '':
		plt.savefig(pic_name + '_down_up.png', format='png')
		plt.close()
	else:
		plt.show()

	plt.xlabel('Times [s]')
	plt.plot(times, z, label='up')
	plt.plot(times, y, label='down')
	plt.legend()
	if pic_name != '':
		plt.savefig(pic_name + '_up_down.png', format='png')
		plt.close()
		return
	else:
		plt.show()


	s, count = 0, 0
	freq_tot = np.zeros((2, len(freqs)))
	while s + fft_size < len(y):
		xfp_l = get_xfp(y[s:s + fft_size])
		xfp_r = get_xfp(z[s:s + fft_size])
		s += fft_size
		for i in range(len(freqs)):
			freq_tot[0][i] += xfp_l[i]
			freq_tot[1][i] += xfp_r[i]
		count += 1
	for i in range(len(freqs)):
		freq_tot[0][i] /= count
		freq_tot[1][i] /= count

	plt.xlabel('Frequency [Hz]')
	plt.plot(freqs, freq_tot[0], label='down')
	plt.plot(freqs, freq_tot[1], label='up')
	plt.legend()
	plt.show()


# draw_time_series('../Data/Trimmed Stereo 32000Hz/gyz/190305 11_22_12.wav')
# draw_time_series('../Data/Trimmed Stereo 32000Hz/cjr/190305 18_47_10.wav')

path = '../Data/Trimmed Stereo 32000Hz/'
pic_path = '../Data/voice visualization'
for pos in all_pos:
	pos_path = os.path.join(pic_path, pos)
	if not os.path.exists(pos_path):
		os.makedirs(pos_path)

for u in os.listdir(path):
	user_path = os.path.join(path, u)
	for f in os.listdir(user_path):
		if f.endswith('.wav'):
			wav_file = os.path.join(user_path, f)
			description_file = os.path.join(user_path, f[:-4] + '.txt')
			file = open(description_file, "r", encoding='utf-8')
			lines = file.readlines()
			pos = lines[1].strip()
			out_path = os.path.join(pic_path, pos)
			pic_name = u + ' ' + lines[2].strip() + lines[0].strip()[-1]
			save_pic = os.path.join(out_path, pic_name)
			print(wav_file, save_pic)
			draw_time_series(wav_file, save_pic)

