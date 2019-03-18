import os

import matplotlib.pyplot as plt
import numpy as np
from keras import models, preprocessing
from sklearn import metrics
from tqdm import tqdm

from cv.CNN_classifier import SEED
from utils import io
from utils.cv_preprocess.img_loader import ImagePack, doc_dict, N_CLASS
from utils.tools import date_time

plt.rcParams['font.sans-serif'] = ['SimHei']
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # todo whether to use cpu

DATETIME = date_time()


class Evaluator(object):
	def __init__(self, model: models.Sequential, imgset: ImagePack, datagen: preprocessing.image.ImageDataGenerator):
		self.model = model
		self.imgset = imgset
		self.datagen = datagen

	def make_eval_data(self, n_img: int):
		'''
		make evaluation data with datagen
		:return:
		'''
		X, truths = [], []
		it = self.datagen.flow(self.imgset.images, self.imgset.labels, batch_size=1, shuffle=False)
		for _ in tqdm(range(n_img)):
			x, y = next(it)
			X.append(x[0])
			truths.append(y[0])
		X = np.array(X)
		return X, truths

	def get_metric(self, n_img: int, metric: callable, **kwargs):
		X, truths = self.make_eval_data(n_img)
		preds = list(self.model.predict_classes(X, batch_size=1, verbose=0))
		return metric(truths, preds, **kwargs)

	def get_accuracy(self, n_img: int = None):
		if n_img is None: n_img = len(imgset.images)
		return self.get_metric(n_img, metrics.accuracy_score)

	def get_confusion_matrix(self, n_img: int = None):
		if n_img is None: n_img = len(imgset.images)
		return self.get_metric(n_img, metrics.confusion_matrix, labels=range(N_CLASS))

	def demo_clf(self, n_img: int, show=True, save_mistakes_only=False):
		'''
		demonstrate the model's classifying ability by letting it predict n images
		'''
		print('=== demonstrating model\'s classifying ability ===')
		X, truths = self.make_eval_data(n_img)
		preds = list(self.model.predict_classes(X, batch_size=1, verbose=0))
		if show:
			print('preds :', preds)
			print('truths:', truths)
		acc = metrics.accuracy_score(truths, preds)
		print('acc = %.1f%%' % (acc * 100))

		folder = 'outputs/%sdemo-clf' % DATETIME
		if not os.path.exists(folder):
			os.mkdir(folder)
		for i in range(n_img):
			if save_mistakes_only and truths[i] == preds[i]: continue
			plt.figure(i)
			plt.imshow(self.imgset.images[i])
			plt.axis('off')
			plt.title(u'truth: %s,  pred: %s' % (doc_dict[truths[i]], doc_dict[preds[i]]))
			savename = '%d.png' % i if truths[i] == preds[i] else '%dx.png' % i
			plt.savefig(os.path.join(folder, savename))
			if show: plt.show()
			plt.close()


if __name__ == '__main__':
	CWD = 'E:\ZFS_TEST\Analysis'
	os.chdir(CWD)
	model = models.load_model('cv/model_state/190316 22_44_10 PN final.h5')
	# model.summary()
	datagen = io.load_from_file('cv/model_state/190316 21_26_45 PN datagen.h5')

	imgset = ImagePack()
	imgset.from_data_dir('Data/Study2/test')
	# # positives
	# os.chdir('Data/Study2/subjects')
	# subject_dirs = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	# print('loading from positives:', subject_dirs)
	# imgset.from_subject(subject_dirs, shuffle=False)
	# # negatives
	# os.chdir('../negatives')
	# negative_dirs = list(filter(lambda x: os.path.isdir(x), os.listdir('.')))
	# print('loading from negatives:', negative_dirs)
	# imgset.from_subject(negative_dirs, random_seed=SEED)
	# os.chdir(CWD)

	imgset.images = np.array(imgset.images)
	print('shape of imgset:')
	imgset.show_shape()
	print()
	os.chdir(CWD)

	n_img = len(imgset.images)
	evaluator = Evaluator(model, imgset, datagen)
	evaluator.demo_clf(n_img, show=False, save_mistakes_only=True)

	print('confusion matrix:')
	mat = evaluator.get_confusion_matrix(n_img)

	# save to csv
	with open('outputs/%sConfusion Matrix.csv' % DATETIME, 'w') as f:
		f.write('Confusion Matrix Over %d Images,' % n_img)
		f.write(','.join(doc_dict) + '\n')
		for i, row in enumerate(mat):
			f.write(doc_dict[i] + ',')
			f.write(','.join(map(str, row)) + '\n')
