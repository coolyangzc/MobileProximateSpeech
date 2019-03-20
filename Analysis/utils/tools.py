import time
import os


def date_time() -> str:
	'''
	generate uniform format date and time string
	promissory save file prefix format in our project

	:return: date_time string
	'''
	return time.strftime('%y%m%d %H_%M_%S ')


def suffix_conv(file_name: str, suffix):
	"""
	convert the suffix of file name to the designated one

	:param file_name: target file name
	:param suffix: designated suffix
	:return: converted file name
	"""
	if not suffix.startswith('.'):
		suffix = '.' + suffix
	segments = file_name.split('.')
	if len(segments) <= 1:
		raise ValueError('file_name `%s` got no suffix' % file_name)
	return '.'.join(segments[:-1]) + suffix


def suffix_filter(files, suffix):
	'''
	return list of files with given suffix
	'''
	return list(filter(lambda x: x.endswith(suffix), files))


def dir_filter(files):
	return list(filter(lambda x: os.path.isdir(x), files))


def inverse_dict(d: dict) -> dict:
	return dict(zip(d.values(), d.keys()))


if __name__ == '__main__':
	a = {'a': -1, 'b': 0, 'c': 2, 'd': 0}
	b = inverse_dict(a)
	del b[0]
	print(b, '\n', len(b))
