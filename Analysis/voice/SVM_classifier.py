from sklearn.svm import SVC
from utils.voice_preprocess.voice_data_loader import load_ftr_from_dir, apply_subsampling, DataPack, show_shape, train_test_split
from configs.subsampling_config import subsampling_config
import os
from utils.io import *

os.chdir('..')
wkdir = 'Data/Sounds/yzc/'

dataset = load_ftr_from_dir(wkdir)
dataset = apply_subsampling(*dataset, **subsampling_config)
show_shape(dataset.data)
dataset = DataPack([unit.flatten() for unit in dataset.data], dataset.labels, dataset.names)
show_shape(dataset.data)

train, test = train_test_split(*dataset, test_size=0.1)

clf = SVC(kernel='rbf', gamma=3e-5, C=1.0)
clf.fit(train.data, train.labels)
print('on train', clf.score(train.data, train.labels))
print('on test ', clf.score(test.data, test.labels))

save_to_file(clf, 'voice/model_states/svm98-89.clf')
