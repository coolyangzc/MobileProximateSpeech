"""PyAudio example: Record a few seconds of audio and save to a WAVE file."""
import pyaudio
import wave
import threading
import time

# constants
CHUNK = 2048
FORMAT = pyaudio.paInt16
RATE = 16000
RECORD_SECONDS = 3


class _Switch(object):
	def __init__(self, status: bool = False):
		self.status = status

	def is_on(self):
		return self.status

	def is_off(self):
		return not self.status


class _RecorderThread(threading.Thread):
	def __init__(self, pa, frames, sr, n_channel):
		self.pa = pa
		self.frames = frames
		self.sr = sr
		self.n_channel = n_channel
		self.switch = _Switch(False)  # sharing memory
		self.elapse = 0.
		super().__init__()

	def run(self):
		# keep recording, until self.switch is turned off
		self.switch.status = True
		since = time.time()
		stream = self.pa.open(format=FORMAT, channels=self.n_channel,
							  rate=self.sr, input=True, frames_per_buffer=CHUNK)
		print("* thread %s is recording" % self.getName())
		while self.switch.is_on():
			data = stream.read(CHUNK)  # fpb / rate  seconds per buffer
			self.frames.append(data)
		# stopped recording
		self.elapse = time.time() - since
		print("* done recording in %.2f sec" % self.elapse)
		stream.stop_stream()
		stream.close()


class Recorder(object):
	'''
	encapsulated pyaudio recorder + thread support.
	this object should be instantiated in the main thread
	'''

	def __init__(self, sr=16000, n_channel=1):
		self.sr = sr
		self.n_channel = n_channel
		self.pa = pyaudio.PyAudio()
		self.thread = None
		self.frames = []

	def start(self):
		'''
		start recording (thread working), this will clear the frame data the thread has collected

		:return: a thread name
		'''
		self.frames.clear()
		self.thread = _RecorderThread(self.pa, self.frames, self.sr, self.n_channel)
		self.thread.start()
		return self.thread.getName()

	def stop(self):
		'''
		stop recording (by stopping the thread)

		:return: total record time in sec
		'''
		self.thread.switch.status = False
		return self.thread.elapse

	def get_frames(self):
		return self.thread.frames

	def get_thread_name(self):
		return self.thread.getName()

	def save(self, out_path):
		'''
		save frames as wav files
		'''
		wf = wave.open(out_path, 'wb')
		wf.setnchannels(self.n_channel)
		wf.setsampwidth(self.pa.get_sample_size(FORMAT))
		wf.setframerate(self.sr)
		wf.writeframes(b''.join(self.frames))
		wf.close()

	def __del__(self):
		self.pa.terminate()


if __name__ == '__main__':
	recorder = Recorder()
	recorder.start()
	i = 0
	while i < 5:  # record for 5 s
		time.sleep(1.0)
		i += 1
	recorder.stop()

	# print(recorder.start())
	# i = 0
	# while i < 3:  # record for 3 s, will overwrite previous frames
	# 	time.sleep(1.0)
	# 	i += 1
	# print(recorder.stop())

	recorder.save('out.wav')
