import os
import Levenshtein


def digit_to_character(s):
	digit_list = ['22', '33', '28', '1', '2', '3', '4', '5', '6', '7', '8', '9']
	ch_list = ['二十二', '三十三', '二十八', '一', '二', '三', '四', '五', '六',
				'七', '八', '九']
	for i in range(len(digit_list)):
		s = s.replace(digit_list[i], ch_list[i])
	return s


if __name__ == "__main__":

	pos_list = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子', '竖屏握持，上端遮嘴',
				'水平端起，倒话筒', '话筒', '横屏',
				'耳旁打电话',
				'手上正面', '手上反面',
				'桌上正面', '桌上反面',
				'裤兜']
	dis, tot, percent, cnt = {}, {}, {}, {}
	for pos in pos_list:
		dis[pos] = [0, 0, 0, 0, 0, 0]
		tot[pos] = [0, 0, 0, 0, 0, 0]
		percent[pos] = [0, 0, 0, 0, 0, 0]
		cnt[pos] = [0, 0, 0, 0, 0, 0]

	recog_path = '../Data/Voice Study Mono 16000Hz/recognition'
	user_list = os.listdir(recog_path)
	for u in user_list:
		if u in ['wj', 'zfs', 'wwn']:
			continue
		user_path = os.path.join(recog_path, u)
		file_list = os.listdir(user_path)
		for f in file_list:
			print(u, f)
			file = open(os.path.join(user_path, f), "r", encoding='utf-8')
			lines = file.readlines()
			file.close()
			phrase = lines[3].strip()
			phrase = phrase[phrase.find('.') + 1:]
			re_list = [' ', '。', '，', '、', '？', '\t']
			for re in re_list:
				phrase = phrase.replace(re, '')
			phrase = digit_to_character(phrase)
			print(phrase)

			recog_res = ''
			if len(lines) >= 5:
				recog_res = lines[4].strip()
			print(recog_res)
			recog_res = digit_to_character(recog_res)
			print(recog_res)
			d = Levenshtein.distance(phrase, recog_res)
			print('dis', d)

			pos = lines[1].strip()
			volume = lines[2].strip()
			order = int(lines[0].strip().split(' ')[-1])

			kind = 0
			if volume == '大声':
				kind = 3
			kind += order - 1
			print('kind', kind)
			dis[pos][kind] += d
			tot[pos][kind] += len(phrase)
			percent[pos][kind] += d / len(phrase)
			cnt[pos][kind] += 1

	for pos in dis:
		if pos == '耳旁打电话':
			print('-' * 140)
		print(pos)
		sumd, sumt= 0, 0
		for i in range(len(dis[pos])):
			d, t = dis[pos][i], tot[pos][i]
			sumd += d
			sumt += t
			print("%3d/%3d: %5.2f%%" % (d, t, d/t * 100), end='    ')
		print("%3d/%3d: %5.2f%%" % (sumd, sumt, sumd/sumt * 100))
	print('-' * 140)
	print('Average Percent:')
	for pos in dis:
		if pos == '耳旁打电话':
			print('-' * 140)
		print(pos)
		sump, sumc = 0, 0
		for i in range(len(dis[pos])):
			p, c = percent[pos][i], cnt[pos][i]
			sump += p
			sumc += c
			print("%3d: %5.2f%%" % (c, p/c * 100), end='    ')
		print("%3d: %5.2f%%" % (sumc, sump/sumc * 100))


