import keras.backend as K
import tensorflow as tf
import matplotlib.pyplot as plt


def plot_history(history, which, datetime):
	plt.plot(history.history[which], label='train')
	plt.plot(history.history['val_%s' % which], label='val')
	plt.title('Model %s' % which)
	plt.ylabel(('%s' % which).upper())
	plt.xlabel('Epoch')
	plt.legend()
	plt.savefig('outputs/%s%s.png' % (datetime, which))
	plt.show()


def f1(y_true, y_pred):
	'''
	compute f1 score
	'''
	y_pred = K.round(y_pred)
	tp = K.sum(K.cast(y_true * y_pred, 'float'), axis=0)
	# tn = K.sum(K.cast((1-y_true)*(1-y_pred), 'float'), axis=0)
	fp = K.sum(K.cast((1 - y_true) * y_pred, 'float'), axis=0)
	fn = K.sum(K.cast(y_true * (1 - y_pred), 'float'), axis=0)

	p = tp / (tp + fp + K.epsilon())
	r = tp / (tp + fn + K.epsilon())

	f1 = 2 * p * r / (p + r + K.epsilon())
	f1 = tf.where(tf.is_nan(f1), tf.zeros_like(f1), f1)
	return K.mean(f1)


def accuracy_score(truths, preds):
	'''
	:param truths: multiclass label, -1, 1, 2 ...
	:param preds: two class label 0, 1
	:return: acc, float
	'''
	correct = 0
	for truth, pred in zip(truths, preds):
		if (truth > 0 and pred == 1) or (truth < 0 and pred == 0):
			correct += 1

	return correct / len(truths)


def confusion_matrix(truths, preds, classes=None):
	'''
	:param truths: [n_class]
	:param preds: [0 pr 1]
	:return: dict {class_label : [categories]}
	'''
	mat = {}
	if classes:
		for c in classes:
			mat[c] = [0, 0]
	for truth, pred in zip(truths, preds):
		if not mat.get(truth):
			mat[truth] = [0, 0]
		mat[truth][pred] += 1
	return mat


if __name__ == '__main__':
	from configs.cv_config import doc_dict, CLASSES
	t = [-1, -1, 1, 2, 2, 2, 6, 7, 8, 9, 10, 10, 10]
	p = [0,  0,  1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0]
	mat = confusion_matrix(t, p, CLASSES)
	for c in CLASSES:
		print(doc_dict[c], ": ", mat[c][0], mat[c][1])
	print()
