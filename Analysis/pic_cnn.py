import os
import random
import numpy as np
from PIL import Image
from keras import Model
from keras.models import load_model
from keras.applications import ResNet50
from keras.models import Sequential
from keras.optimizers import SGD
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array
from keras.utils.np_utils import to_categorical
from keras.applications.densenet import DenseNet201, preprocess_input
from sklearn.model_selection import train_test_split
from keras.layers import Dense, Dropout, Flatten, BatchNormalization, GlobalAveragePooling2D
from keras.layers import Conv2D, MaxPool2D
from keras.layers.normalization import BatchNormalization

'''
positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
           '竖屏握持，上端遮嘴', # '水平端起，倒话筒',
           '话筒', '横屏']
negative = ['左耳打电话（不碰）', '右耳打电话（不碰）', '左耳打电话（碰触）', '右耳打电话（碰触）']
'''


positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
           '竖屏握持，上端遮嘴', # '水平端起，倒话筒',
           '横屏', '话筒',
			'左耳打电话（不碰）', '右耳打电话（不碰）', '左耳打电话（碰触）', '右耳打电话（碰触）']

negative = ['手中', '打字', '拍照', '浏览',
			'自拍', '摇晃（前后）', '摇晃（左右）', '裤兜']


all = positive + negative

# subject_path = '../Data/Study2/fixed subjects'
# pic_path = '../Data/Study2/sorted pics'
pic_path = '../Data/Study2/sorted pics_192_108'


def read_pics(simplification=-1):
	X, y, task = [], [], []
	type_list = os.listdir(pic_path)
	for type in type_list:
		type_path = os.path.join(pic_path, type)
		if type in positive:
			label = 1
		elif type in negative:
			label = 0
		else:
			continue
		pic_list = os.listdir(type_path)
		if len(pic_list) > simplification:
			random.shuffle(pic_list)
			pic_list = pic_list[:simplification]
		for pic in pic_list:
			pic_file = os.path.join(type_path, pic)
			img = Image.open(pic_file)
			arr = img_to_array(img)
			X.append(arr)
			y.append(label)
			task.append(type)
	X = np.array(X)
	y = np.array(y)
	# mean_px = X.mean().astype(np.float32)
	# std_px = X.std().astype(np.float32)
	# X = (X - mean_px) / std_px
	X /= 255
	X = X.astype(np.float32)
	y = to_categorical(y)
	print(X.shape, y.shape)
	return X, y, task


def add_new_last_layer(base_model, nb_classes):
	x = base_model.output
	x = GlobalAveragePooling2D()(x)
	predictions = Dense(nb_classes, activation='softmax')(x)
	model = Model(inputs=base_model.input, outputs=predictions)
	return model


def fit_model(use_data_generator=False):
	global X, y
	X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.10, shuffle=True)
	print(X_train.shape, y_train.shape, X_val.shape, y_val.shape)
	del X, y

	model = DenseNet201(include_top=False)
	model = add_new_last_layer(model, 2)

	model.compile(optimizer=SGD(lr=0.001, momentum=0.9, decay=0.0001, nesterov=True),
				  loss='categorical_crossentropy', metrics=['accuracy'])
	batch_size = 32
	epochs = 20

	if use_data_generator:
		datagen = ImageDataGenerator(
			# preprocessing_function=preprocess_input,
			featurewise_center=False,  # set input mean to 0 over the dataset
			samplewise_center=False,  # set each sample mean to 0
			featurewise_std_normalization=False,  # divide inputs by std of the dataset
			samplewise_std_normalization=False,  # divide each input by its std
			zca_whitening=False,  # apply ZCA whitening
			rotation_range=30,  # randomly rotate images in the range (degrees, 0 to 180)
			shear_range=0.2,
			zoom_range=0.2,  # Randomly zoom image
			width_shift_range=0.2,  # randomly shift images horizontally (fraction of total width)
			height_shift_range=0.2,  # randomly shift images vertically (fraction of total height)
			horizontal_flip=True,
			vertical_flip=False)
		datagen.fit(X_train)
		history = model.fit_generator(datagen.flow(X_train, y_train, batch_size=batch_size),
									  epochs=epochs, steps_per_epoch=len(X_train) // batch_size,
									  validation_data=datagen.flow(X_val, y_val, batch_size=batch_size),
									  validation_steps=len(X_val) // batch_size,
									  verbose=1)
	else:
		history = model.fit(X_train, y_train,
							batch_size=batch_size, epochs=epochs,
							validation_data=(X_val, y_val), shuffle=True,
							verbose=1)
	print(model.evaluate(X_val, y_val))
	model.save('mouth+ear_vs_other.h5')


def evaluate():
	img_model = load_model('mouth+ear_vs_other.h5')
	res = img_model.predict(X, verbose=1)
	correct, total = {}, {}
	for t in all:
		correct[t], total[t] = 0, 0
	for i in range(len(task)):
		total[task[i]] += 1
		if (res[i][0] > 0.5 and y[i][0] > 0.5) or (res[i][1] > 0.5 and y[i][1] > 0.5):
			correct[task[i]] += 1

	mean_acc = 0
	for t in correct:
		acc = correct[t] / total[t]
		mean_acc += acc
		print(t.ljust(24 - len(t)), correct[t], '/', total[t], acc)
	print(mean_acc / len(correct))


if __name__ == "__main__":
	X, y, task = read_pics(simplification=999)
	# fit_model(use_data_generator=True)
	evaluate()





