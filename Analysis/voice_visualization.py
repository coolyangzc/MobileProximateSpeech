import wave
import numpy as np
import matplotlib.pyplot as plt
import struct
from scipy import zeros

import pylab

path = '../Data/voice/'
wavefile = wave.open(path + '/yzc/filtered/190305 10_26_49.wav', 'r')

'''
from scipy import signal
from scipy.io import wavfile

sample_rate, samples = wavfile.read(path + '/yzc/filtered/190305 10_26_49.wav')
frequencies, times, spectrogram = signal.spectrogram(samples, sample_rate)
print(frequencies.shape, times.shape, spectrogram.shape)

while True:
	continue
'''

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
'''
# -*- coding: utf-8 -*-
import numpy as np
import pylab as pl

sampling_rate = 8000
fft_size = 512
t = np.arange(0, 1.0, 1.0/sampling_rate)
print(t.shape)
x = np.sin(2*np.pi*156.25*t) + 2*np.sin(2*np.pi*234.375*t)
xs = x[:fft_size]
xf = np.fft.rfft(xs)/fft_size
freqs = np.linspace(0, sampling_rate/2, fft_size/2+1)
print(freqs)
xfp = 20*np.log10(np.clip(np.abs(xf), 1e-20, 1e100))
print(xf.shape, freqs.shape)
print(xfp.shape)
pl.figure(figsize=(8,4))
pl.subplot(211)
pl.plot(t[:fft_size], xs)
pl.xlabel(u"时间(秒)")
pl.title(u"156.25Hz和234.375Hz的波形和频谱")
pl.subplot(212)
pl.plot(freqs, xfp)
pl.xlabel(u"频率(Hz)")
pl.subplots_adjust(hspace=0.4)
pl.show()
'''