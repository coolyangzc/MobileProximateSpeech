import os
from aip import AipSpeech


def get_file_content(file_path):
	with open(file_path, 'rb') as fp:
		return fp.read()


def setup_client():
	global client
	APP_ID = '15779386'
	API_KEY = 'RA4tK9zkDxPxbhTg7CtZbBPw'
	SECRET_KEY = 'LNVQ2rNgoXhYHRzVwNvZzOh5ZXpcSom6'
	client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)


def recognition_files(data_path):
	user_list = os.listdir(data_path)
	user_list.remove('recognition')
	recog_path = os.path.join(data_path, 'recognition')
	for u in user_list:
		user_path = os.path.join(data_path, u)
		out_path = os.path.join(recog_path, u)
		if not os.path.exists(out_path):
			os.makedirs(out_path)
		file_list = os.listdir(user_path)
		for f in file_list:
			if f.endswith('.wav'):
				wav_file = os.path.join(user_path, f)
				description_file = os.path.join(user_path, f[:-4] + '.txt')
				file = open(description_file, "r", encoding='utf-8')
				lines = file.readlines()
				task_id = lines[0].strip().replace("/", "_").replace(":", "_").replace(" ", "")
				out_file = os.path.join(out_path, task_id + ".txt")
				output = open(out_file, 'w', encoding='utf-8')
				for l in lines:
					output.write(l)
				if not lines[-1].endswith('\n'):
					output.write('\n')
				res = client.asr(get_file_content(wav_file), 'wav', 16000, {
					'dev_pid': 1536,
				})
				try:
					print(u, res['result'])
					for recog in res['result']:
						output.write(recog + '\n')
				except KeyError:
					print(u, f)


if __name__ == "__main__":
	setup_client()
	recognition_files('../Data/Voice Study Mono 16000Hz/')

