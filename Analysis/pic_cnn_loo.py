import os
import numpy as np
from PIL import Image
from keras import Model
from keras.applications import ResNet50
from keras.models import Sequential
from keras.optimizers import SGD
from keras.layers import Dense, GlobalAveragePooling2D
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array
from keras.utils.np_utils import to_categorical
from keras.applications.densenet import DenseNet201, preprocess_input

positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
           '竖屏握持，上端遮嘴', # '水平端起，倒话筒',
           '话筒', '横屏',
			'左耳打电话（不碰）', '右耳打电话（不碰）', '左耳打电话（碰触）', '右耳打电话（碰触）']

negative = ['手中', '打字', '拍照', '浏览',
			'自拍', '摇晃（前后）', '摇晃（左右）', '裤兜']

all = positive + negative
pic_path = '../Data/Study2/sorted pics_192_108'

X, y, task = {}, {}, {}


def read_pics():
	global X, y, task
	type_list = os.listdir(pic_path)
	for type in type_list:
		type_path = os.path.join(pic_path, type)
		if type in positive:
			t = 1
		elif type in negative:
			t = 0
		else:
			continue
		for pic in os.listdir(type_path):
			pic_file = os.path.join(type_path, pic)
			img = Image.open(pic_file)
			arr = img_to_array(img)
			user = pic.split('_')[0]
			if user not in X:
				X[user], y[user], task[user] = [], [], []
			X[user].append(arr)
			y[user].append(t)
			task[user].append(type)

	for user in X:
		X[user], y[user] = np.array(X[user]), np.array(y[user])
		X[user] /= 255
		X[user] = X[user].astype(np.float32)
		y[user] = to_categorical(y[user])


def add_new_last_layer(base_model, nb_classes):
	x = base_model.output
	x = GlobalAveragePooling2D()(x)
	predictions = Dense(nb_classes, activation='softmax')(x)
	model = Model(inputs=base_model.input, outputs=predictions)
	return model


def leave_one_out_validation():
	for loo in X:
		print(loo)
		X_train, y_train = [], []
		for user in X:
			if user != loo:
				X_train.extend(X[user])
				y_train.extend(y[user])
		X_train, y_train = np.array(X_train), np.array(y_train)
		X_test, y_test = X[loo], y[loo]
		model = DenseNet201(include_top=False)
		model = add_new_last_layer(model, 2)

		model.compile(optimizer=SGD(lr=0.001, momentum=0.9, decay=0.0001, nesterov=True),
					  loss='categorical_crossentropy', metrics=['accuracy'])

		batch_size = 32
		epochs = 5

		history = model.fit(X_train, y_train,
							batch_size=batch_size, epochs=epochs,
							validation_data=(X_test, y_test), shuffle=True,
							verbose=1)


if __name__ == "__main__":
	read_pics()
	leave_one_out_validation()