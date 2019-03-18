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