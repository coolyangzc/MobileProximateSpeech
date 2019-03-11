# print log to both console and external file
import sys


class DualLogger:
	def __init__(self, filename='log.txt'):
		self.console = sys.stdout
		sys.stdout = self
		self.file = open(filename, 'w')

	def close(self):
		sys.stdout = self.console
		self.file.close()

	def __del__(self):
		self.file.close()

	def write(self, message):
		self.console.write(message)
		self.file.write(message)

	def flush(self):
		pass
