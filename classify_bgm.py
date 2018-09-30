import librosa
import pickle

import tqdm

from util import extract_features


def main(args):
    model = pickle.load(open(args.model, 'rb'))
    with open(args.list) as f:
        lines = f.readlines()
        for line in tqdm.tqdm(lines):
            path = line.strip()
            y, sr = librosa.load(path)
            prob = classify(model, y)
            label = int(prob > args.threshold)
            print('{}\t{:.3f}\t{}'.format(label, float(prob), path))


def classify(model, wav):
    x = extract_features(wav)
    prob = model.predict_proba(x)[0, 1]
    return prob


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Classify segmented .wav files into those with/without BGM')
    parser.add_argument('model', help='model file')
    parser.add_argument('list', help='list of .wav files')
    parser.add_argument('--threshold', type=float, default=0.5, help='threshold')

    main(parser.parse_args())
