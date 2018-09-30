import pickle
import sys
import os
import hashlib
import numpy as np

import librosa
import tqdm
import sklearn
import multiprocessing
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, GradientBoostingClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

from util import extract_features


def read_list(path):
    with open(path) as f:
        return set([line.strip() for line in f.readlines()])


def load(path):
    wav, sr = librosa.load(path)
    x1 = extract_features(wav)
    return x1


def main(args):
    all_paths = read_list(args.all)
    noise_paths = read_list(args.noise)
    print(f'# Total: {len(all_paths)}', file=sys.stderr)
    print(f'# Noise: {len(noise_paths)}', file=sys.stderr)

    cache_path = 'cache-' + str(hashlib.sha224(str(sorted(all_paths) + sorted(noise_paths)).encode('utf-8')).hexdigest())
    print('Cache: ' + cache_path, file=sys.stderr)
    if os.path.exists(cache_path):
        print('Reusing cache.', file=sys.stderr)
        with open(cache_path, 'rb') as f:
            x, y = pickle.load(f)
    else:
        print('Loading data...', file=sys.stderr)
        x = []
        y = []
        pool = multiprocessing.Pool()
        ys = list(map(lambda path: int(path in noise_paths), all_paths))
        for x1, y1 in tqdm.tqdm(zip(pool.imap(load, all_paths), ys), total=len(all_paths)):
            x.append(x1)
            y.append(y1)
        x = np.squeeze(np.stack(x))
        y = np.squeeze(np.stack(y))
        with open(cache_path, 'wb') as f:
            pickle.dump((x, y), f)

    if args.no_test:
        x_train = x
        y_train = y
        x_test = []
        y_test = []
    else:
        if args.test_num is not None:
            test_size = args.test_num
        else:
            test_size = args.test_ratio
        x_train, x_test, y_train, y_test = sklearn.model_selection.train_test_split(x, y, test_size=test_size, random_state=0)
    print(f'# Train: {len(x_train)}', file=sys.stderr)
    print(f'  # Positive: {(y_train == 1).sum()}', file=sys.stderr)
    print(f'  # Negative: {(y_train == 0).sum()}', file=sys.stderr)
    print(f'# Test: {len(x_test)}', file=sys.stderr)

    print('Using ' + args.classifier, file=sys.stderr)
    clf = eval(args.classifier)

    print('Fitting model...', file=sys.stderr)
    clf.fit(x_train, y_train)

    if not args.no_test:
        y_pred = clf.predict(x_test)
        conf = sklearn.metrics.confusion_matrix(y_test, y_pred)
        print('Confusion matrix:', file=sys.stderr)
        print(conf, file=sys.stderr)
        acc = (y_pred == y_test).sum() / len(y_test)
        print(f'Accuracy: {acc}', file=sys.stderr)

    with open(args.out, 'wb') as f:
        pickle.dump(clf, f)


def classify(model, wav):
    x = extract_features(wav)
    prob = model.predict_proba(x)[0, 1]
    return prob


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Train a classifier that classifies .wav files into those with/without noise')
    parser.add_argument('all', help='list of all .wav files')
    parser.add_argument('noise', help='list of noise .wav files')
    parser.add_argument('out', help='output path')
    parser.add_argument('--test-ratio', default=0.1, type=float, help='ratio of test data')
    parser.add_argument('--test-num', default=None, type=int, help='number of examples in test data')
    parser.add_argument('--no-test', action='store_true', help='use all examples for training data')
    parser.add_argument('--classifier',
                        default='RandomForestClassifier(n_estimators = 60, min_samples_leaf = 5, min_samples_split=10)',
                        help='classifier to use')

    main(parser.parse_args())
