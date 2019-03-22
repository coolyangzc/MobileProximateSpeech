import os
import numpy as np
from PIL import Image
from keras.models import Sequential
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array
from keras.utils.np_utils import to_categorical
from sklearn.model_selection import train_test_split
from keras.layers import Dense, Dropout, Flatten, BatchNormalization
from keras.layers import Conv2D, MaxPooling2D
from keras.layers.normalization import BatchNormalization

positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
            '竖屏握持，上端遮嘴', # '水平端起，倒话筒',
            '话筒', '横屏']
negative = ['左耳打电话（不碰）', '右耳打电话（不碰）', '左耳打电话（碰触）', '右耳打电话（碰触）']

subject_path = '../Data/Study2/fixed subjects'


def read_pics():
	X, y = [], []
	for u in os.listdir(subject_path):
		user_path = os.path.join(subject_path, u)
		orig_path = os.path.join(user_path, 'original')
		resz_path = os.path.join(user_path, 'resized')
		txt_list = list(filter(lambda x: x.endswith('.txt'), os.listdir(orig_path)))
		for f in txt_list:
			description_file = os.path.join(orig_path, f)
			file = open(description_file, "r", encoding='utf-8')
			line = file.readline()
			type = line.strip().split(' ')[0]
			if type in positive:
				type = 1
			elif type in negative:
				type = 0
			else:
				continue
			pic_path = os.path.join(resz_path, f[:-4])
			if not os.path.exists(pic_path):
				continue
			pic_list = list(filter(lambda x: x.endswith('.jpg'), os.listdir(pic_path)))
			for pic in pic_list:
				pic_file = os.path.join(pic_path, pic)
				img = Image.open(pic_file)
				arr = img_to_array(img)
				# arr = np.asarray(img, dtype=np.float32)
				# print(pic, img.size, arr.shape)
				X.append(arr)
				y.append(type)
	X = np.array(X)
	y = np.array(y)
	X = X.astype('float32')
	y = to_categorical(y)
	print(X.shape, y.shape)

	# X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.10, shuffle=True)
	'''
	index = np.arange(len(X))
	np.random.shuffle(index)
	X = X[index,:,:,:]
	y = y[index]

	'''
	validation_split = 0.2
	sp = int((1 - validation_split) * len(X))
	X_train, X_val = X[:sp], X[sp:]
	y_train, y_val = y[:sp], y[sp:]

	return (X_train, y_train), (X_val, y_val)


if __name__ == "__main__":
	(X_train, y_train), (X_val, y_val) = read_pics()
	print(X_train.shape, y_train.shape, X_val.shape, y_val.shape)

	model = Sequential([
		Conv2D(32, (5, 5), padding='Same', activation='relu', input_shape=(108, 192, 3)),
		Conv2D(32, (5, 5), padding='Same', activation='relu'),
		MaxPooling2D((2, 2)),
		Dropout(0.25),
		Flatten(),
		Dense(128, activation='relu'),
		Dropout(0.5),
		Dense(2, activation="softmax")
	])
	model.compile(optimizer='RMSprop', loss="categorical_crossentropy", metrics=['accuracy'])

	batch_size = 128
	epochs = 10

	history = model.fit(X_train, y_train,
						batch_size=batch_size, epochs=epochs,
						validation_data=(X_val, y_val), shuffle=True,
						verbose=1)
	'''
	history_dict = history.history
	acc_values = history_dict['acc']
	print(acc_values)
	val_acc_values = history_dict['val_acc']
	print(val_acc_values)
	'''
	# print(model.)

	print(model.evaluate(X_val, y_val))
	#print('Test loss:', loss)
	#print('Test accuracy:', accuracy)
