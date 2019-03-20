import os
from pydub import AudioSegment
from webrtcvad_utils import calc_vad

path = '../Data/Trimmed Stereo 32000Hz'

for u in os.listdir(path):
	print(u)
	user_path = os.path.join(path, u)
	for f in os.listdir(user_path):
		if f.endswith('.wav'):
			print(f)
			speech = AudioSegment.from_wav(os.path.join(user_path, f))
			speech_mono = speech.set_channels(1)
			speech_mono.export('temp.wav', format='wav')
			split_times = calc_vad(3, 'temp.wav')

			out_path = os.path.join(user_path, f[:-4])
			if not os.path.exists(out_path):
				os.makedirs(out_path)
			chunk = 0
			for i in range(0, len(split_times), 2):
				s = split_times[i] * 1000
				t = split_times[i+1] * 1000
				speech[s:t].export(os.path.join(out_path, 'chunk' + str(chunk) + '.wav'), format='wav')
				chunk += 1

