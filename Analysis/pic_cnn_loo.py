import os
import gc
import sys
import random
import numpy as np
from PIL import Image
from keras import Model
from keras.callbacks import ModelCheckpoint
from keras.models import load_model
from keras.models import Sequential
from keras.optimizers import SGD
from keras.layers import Dense, GlobalAveragePooling2D
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array
from keras.utils.np_utils import to_categorical
from keras.applications.densenet import DenseNet201, preprocess_input

positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
           '竖屏握持，上端遮嘴', # '水平端起，倒话筒',
           '话筒', '横屏']
negative = ['左耳打电话（不碰）', '右耳打电话（不碰）', '左耳打电话（碰触）', '右耳打电话（碰触）']

'''
positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
           '竖屏握持，上端遮嘴', # '水平端起，倒话筒',
           '话筒', '横屏',
			'左耳打电话（不碰）', '右耳打电话（不碰）', '左耳打电话（碰触）', '右耳打电话（碰触）']

negative = ['手中', '打字', '拍照', '浏览',
			'自拍', '摇晃（前后）', '摇晃（左右）', '裤兜']
'''

all_type = positive + negative
pic_path = '../Data/Study2/sorted pics_192_108'
model_path = '../Data/Study2/sorted pics_192_108/models'

X_train, y_train, X_test, y_test, t_test = [], [], [], [], []
pic_sources = []
users = []


def read_pic_sources():
	for type in all_type:
		type_path = os.path.join(pic_path, type)
		pic_sources.append({})
		for pic in os.listdir(type_path):
			user = pic.split('_')[0]
			if user not in users:
				users.append(user)
			if user not in pic_sources[-1]:
				pic_sources[-1][user] = []
			pic_sources[-1][user].append(pic)


def read_pic(pic_file):
	img = Image.open(pic_file)
	arr = img_to_array(img)
	return arr


def add_new_last_layer(base_model, nb_classes):
	x = base_model.output
	x = GlobalAveragePooling2D()(x)
	predictions = Dense(nb_classes, activation='softmax')(x)
	model = Model(inputs=base_model.input, outputs=predictions)
	return model


def fit_model(use_data_generator=True, user_name='noname'):
	global X_train, y_train, X_test, y_test, t_test, output
	print(X_train.shape, y_train.shape, X_test.shape, y_test.shape)

	model = DenseNet201(include_top=False)
	model = add_new_last_layer(model, 2)

	model.compile(optimizer=SGD(lr=0.001, momentum=0.9, decay=0.0001, nesterov=True),
				  loss='categorical_crossentropy', metrics=['accuracy'])

	batch_size = 32
	epochs = 10

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
		# datagen.fit(X_train)
		model_file_name = os.path.join(model_path, user_name + '.h5')
		checkpoint = ModelCheckpoint(filepath=model_file_name, monitor='val_acc',
									 save_best_only='True', save_weights_only='True')
		history = model.fit_generator(datagen.flow(X_train, y_train, batch_size=batch_size),
									  epochs=epochs, steps_per_epoch=len(X_train) // batch_size,
									  validation_data=datagen.flow(X_test, y_test, batch_size=batch_size),
									  validation_steps=len(X_test) // batch_size,
									  verbose=2, callbacks=[checkpoint])
		del datagen
		gc.collect()
	else:
		history = model.fit(X_train, y_train,
							batch_size=batch_size, epochs=epochs,
							validation_data=(X_test, y_test), shuffle=True,
							verbose=2)

	model.load_weights(model_file_name)
	# model = load_model(model_file_name)
	res = model.predict(X_test, verbose=1)
	del model, history
	gc.collect()
	correct, total = {}, {}
	for t in all_type:
		correct[t], total[t] = 0, 0
	for i in range(len(t_test)):
		total[t_test[i]] += 1
		if (res[i][0] > 0.5 and y_test[i][0] > 0.5) or (res[i][1] > 0.5 and y_test[i][1] > 0.5):
			correct[t_test[i]] += 1

	user_mean_acc, user_cnt = 0, 0
	for t in total:
		if total[t] > 0:
			acc = correct[t] / total[t]
			user_mean_acc += acc
			user_cnt += 1
			print(t.ljust(24 - len(t)), correct[t], '/', total[t], acc)
			output.write(t + ' ' + str(correct[t]) + ' / ' + str(total[t]) + ' ' + str(acc) + '\n')
	print(user_mean_acc / user_cnt)
	output.write(str(user_mean_acc / user_cnt) + '\n')


def leave_one_out_validation(loo, simplification=-1):
	global X_train, y_train, X_test, y_test, t_test, output
	print(loo)
	if not os.path.exists(model_path):
		os.makedirs(model_path)
	res_path = os.path.join(pic_path, 'results')
	if not os.path.exists(res_path):
		os.makedirs(res_path)
	out_file = os.path.join(res_path, loo + '.txt')
	output = open(out_file, 'w', encoding='utf-8')

	output.write('user ' + loo + '\n')
	X_train, y_train, X_test, y_test, t_test = [], [], [], [], []
	for i in range(len(pic_sources)):
		if i >= len(positive):
			label = 0
		else:
			label = 1
		train_files, test_files = [], []
		for user in pic_sources[i]:
			if user == loo:
				test_files.extend(pic_sources[i][user])
			else:
				train_files.extend(pic_sources[i][user])
		if len(train_files) > simplification:
			random.shuffle(train_files)
			train_files = train_files[:simplification]
		for pic in train_files:
			X_train.append(read_pic(os.path.join(pic_path, all_type[i], pic)))
			y_train.append(label)
		for pic in test_files:
			X_test.append(read_pic(os.path.join(pic_path, all_type[i], pic)))
			y_test.append(label)
			t_test.append(all_type[i])
	randnum = random.randint(0, 32768)
	random.seed(randnum)
	random.shuffle(X_train)
	random.seed(randnum)
	random.shuffle(y_train)
	X_train, y_train = np.array(X_train), np.array(y_train)
	X_test, y_test = np.array(X_test), np.array(y_test)
	X_train /= 255
	X_test /= 255
	X_train, X_test = X_train.astype(np.float32), X_test.astype(np.float32)
	y_train, y_test = to_categorical(y_train), to_categorical(y_test)
	fit_model(use_data_generator=True, user_name=loo)
	del X_train, X_test, y_train, y_test, t_test
	gc.collect()


if __name__ == "__main__":
	read_pic_sources()
	leave_one_out_validation(sys.argv[1], simplification=1000)