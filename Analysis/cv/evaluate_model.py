import os

import matplotlib.pyplot as plt
import numpy as np
from keras import models, preprocessing
from tqdm import tqdm
from configs import cv_config as config

from cv import funcs
from utils import io
from utils.cv_preprocess.img_loader import ImagePack
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
		it = self.datagen.flow(self.imgset.images, self.imgset.labels, batch_size=config.batch_size, shuffle=False)
		for _ in tqdm(range(n_img // config.batch_size), desc='preparing data', leave=False):
			x, y = next(it)
			X += list(x)
			truths += list(y)
		X = np.array(X)
		return X, truths

	def get_metric(self, n_img: int, metric: callable, **kwargs):
		X, truths = self.make_eval_data(n_img)
		preds = list(self.model.predict_classes(X, batch_size=1, verbose=0).squeeze())
		return metric(truths, preds, **kwargs)

	def get_accuracy(self, n_img: int = None):
		if n_img is None: n_img = len(imgset.images)
		return self.get_metric(n_img, funcs.accuracy_score)

	def get_confusion_matrix(self, n_img: int = None):
		if n_img is None: n_img = len(imgset.images)
		return self.get_metric(n_img, funcs.confusion_matrix, classes=config.CLASSES)

	def demo_clf(self, n_img: int, show=True, save_mistakes_only=False):
		'''
		demonstrate the model's classifying ability by letting it predict n images
		'''
		print('=== demonstrating model\'s classifying ability ===')
		X, truths = self.make_eval_data(n_img)
		print('predicting...')
		preds = list(self.model.predict_classes(X, batch_size=1, verbose=0).squeeze())
		if show:
			print('preds :', preds)
			print('truths:', truths)
		acc = funcs.accuracy_score(truths, preds)
		print('acc = %.1f%%' % (acc * 100))

		folder = 'outputs/%sdemo-clf' % DATETIME
		if not os.path.exists(folder):
			os.mkdir(folder)
		for i in tqdm(range(n_img // config.batch_size), desc='saving images', leave=False):
			if save_mistakes_only:
				if (truths[i] > 0 and preds[i] == 1) or (truths[i] < 0 and preds[i] == 0):
					continue
			plt.figure(i)
			plt.imshow(self.imgset.images[i])
			plt.axis('off')
			plt.title(u'truth: %s,  pred: %s' % (config.doc_dict[truths[i]], preds[i]))
			savename = '%d.png' % i if truths[i] == preds[i] else '%dx.png' % i
			plt.savefig(os.path.join(folder, savename))
			if show: plt.show()
			plt.close()

		return funcs.confusion_matrix(truths, preds, classes=config.CLASSES)


if __name__ == '__main__':

	CWD = config.working_directory

	os.chdir(CWD)
	model = models.load_model('cv/model_state/190322 21_59_58 PN best model.h5', compile=False)
	model.summary()
	# datagen = io.load_from_file('cv/model_state/190316 21_26_45 PN datagen.h5')
	datagen = preprocessing.image.ImageDataGenerator(**config.data_gen_config)

	imgset = ImagePack()
	imgset.from_data_dir(os.path.join(config.data_directory, 'val/'))

	imgset.images = np.array(imgset.images)
	print('shape of imgset:')
	imgset.show_shape()
	print()
	os.chdir(CWD)

	n_img = len(imgset.images)
	evaluator = Evaluator(model, imgset, datagen)
	mat = evaluator.demo_clf(n_img, show=False, save_mistakes_only=True)

	# print('getting confusion matrix')
	# mat = evaluator.get_confusion_matrix(n_img)

	# save to csv
	with open('outputs/%sConfusion Matrix.csv' % DATETIME, 'w') as f:
		f.write('Confusion Matrix Over %d Images (train),' % n_img)
		f.write(' 0, 1\n')
		for c in config.CLASSES:
			f.write('%s, %d, %d\n'% (config.doc_dict[c], mat[c][0], mat[c][1]))
