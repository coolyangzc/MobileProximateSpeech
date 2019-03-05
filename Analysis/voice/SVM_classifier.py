from sklearn.svm import SVC
from utils.voice_preprocess.mfcc_data_loader import load_ftr_from_chunks_dir, load_ftr_from_wav_dir, apply_subsampling, DataPack, show_shape, train_test_split
from configs.subsampling_config import subsampling_config
import os
from utils.io import *

os.chdir('..')
wkdirs = [
	'Data/Study3/subjects/gfz/trimmed',
	# 'Data/Study3/subjects/gfz/trimmed',
	'Data/Study3/subjects/wty/trimmed',
]

dataset = load_ftr_from_wav_dir(wkdirs, shuffle=False, cache=True)
show_shape(dataset)
dataset = apply_subsampling(*dataset, **subsampling_config, shuffle=True)
show_shape(dataset)
print('data loaded.')

# flatten data
dataset = DataPack([unit.flatten() for unit in dataset.data], dataset.labels, dataset.names)
show_shape(dataset)

train, test = train_test_split(*dataset, test_size=0.1)
show_shape(train.data)
show_shape(test.data)

clf = SVC(kernel='rbf', gamma=3e-5, C=1.0)
clf.fit(train.data, train.labels)
print('on train', clf.score(train.data, train.labels))
print('on test ', clf.score(test.data, test.labels))

# save_to_file(clf, 'voice/model_states/svm98-89.clf')
