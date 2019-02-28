import pickle


# IO support
def load_from_file(filename):
	with open(filename, 'rb') as f:
		obj = pickle.load(f)
	return obj


def save_to_file(obj, filename):
	with open(filename, 'wb') as f:
		pickle.dump(obj, f)
