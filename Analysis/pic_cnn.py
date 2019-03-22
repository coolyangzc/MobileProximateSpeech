import os
import numpy as np
from PIL import Image
from keras import Model
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

positive = ['竖直对脸，碰触鼻子', '竖直对脸，不碰鼻子',
           '竖屏握持，上端遮嘴', # '水平端起，倒话筒',
           '话筒', '横屏']
negative = ['左耳打电话（不碰）', '右耳打电话（不碰）', '左耳打电话（碰触）', '右耳打电话（碰触）']

# subject_path = '../Data/Study2/fixed subjects'
# pic_path = '../Data/Study2/sorted pics'
pic_path = '../Data/Study2/sorted pics_192_108'


def read_pics():
	X, y = [], []
	type_list = os.listdir(pic_path)
	for type in type_list:
		type_path = os.path.join(pic_path, type)
		if type in positive:
			type = 1
		elif type in negative:
			type = 0
		else:
			continue
		for pic in os.listdir(type_path):
			pic_file = os.path.join(type_path, pic)
			img = Image.open(pic_file)
			arr = img_to_array(img)
			X.append(arr)
			y.append(type)
	X = np.array(X)
	y = np.array(y)
	# mean_px = X.mean().astype(np.float32)
	# std_px = X.std().astype(np.float32)
	# X = (X - mean_px) / std_px
	X /= 255
	X = X.astype(np.float32)
	y = to_categorical(y)
	print(X.shape, y.shape)
	X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.10, shuffle=True)
	return (X_train, y_train), (X_val, y_val)


def add_new_last_layer(base_model, nb_classes):
	x = base_model.output
	x = GlobalAveragePooling2D()(x)
	predictions = Dense(nb_classes, activation='softmax')(x)
	model = Model(inputs=base_model.input, outputs=predictions)
	return model


if __name__ == "__main__":
	(X_train, y_train), (X_val, y_val) = read_pics()
	print(X_train.shape, y_train.shape, X_val.shape, y_val.shape)

	model = DenseNet201(include_top=False)
	model = add_new_last_layer(model, 2)

	model.compile(optimizer=SGD(lr=0.001, momentum=0.9, decay=0.0001, nesterov=True),
				  loss='categorical_crossentropy', metrics=['accuracy'])
	# model.compile(optimizer='RMSprop', loss="categorical_crossentropy", metrics=['acc'])

	batch_size = 32
	epochs = 20

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

	'''
	history = model.fit(X_train, y_train,
						batch_size=batch_size, epochs=epochs,
						validation_data=(X_val, y_val), shuffle=True,
						verbose=1)

	'''
	'''
	history_dict = history.history
	acc_values = history_dict['acc']
	print(acc_values)
	val_acc_values = history_dict['val_acc']
	print(val_acc_values)
	'''

	print(model.evaluate(X_val, y_val))
	model.save('ear_cnn_model.h5')
	#print('Test loss:', loss)
	#print('Test accuracy:', accuracy)
