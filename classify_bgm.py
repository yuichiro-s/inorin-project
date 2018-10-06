import sys
import pickle
import multiprocessing

import tqdm
import librosa
import numpy as np

from util import extract_features


def load(path):
    wav, _ = librosa.load(path)
    x = extract_features(wav)
    return x


def process(xs, model, threshold, paths):
    xs = np.vstack(xs)
    probs = model.predict_proba(xs)[:, 1]
    label = (probs > threshold).astype(np.int32)
    for p, l, path in zip(probs, label, paths):
        print('{}\t{:.3f}\t{}'.format(int(l), float(p), path))
    sys.stdout.flush()


def main(args):
    model = pickle.load(open(args.model, 'rb'))
    pool = multiprocessing.Pool()
    with open(args.list) as f:
        lines = f.readlines()
        paths = list(map(lambda line: line.strip(), lines))
        current_xs = []
        current_paths = []
        for x, path in tqdm.tqdm(zip(pool.imap(load, paths), paths), total=len(paths)):
            current_xs.append(x)
            current_paths.append(path)
            if len(current_xs) >= args.batch:
                process(current_xs, model, args.threshold, current_paths)
                current_xs = []
                current_paths = []
        if len(current_xs) > 0:
            process(current_xs, model, args.threshold, current_paths)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Classify segmented .wav files into those with/without BGM')
    parser.add_argument('model', help='model file')
    parser.add_argument('list', help='list of .wav files')
    parser.add_argument('--threshold', type=float, default=0.5, help='threshold')
    parser.add_argument('--batch', type=int, default=128, help='batch size')

    main(parser.parse_args())
