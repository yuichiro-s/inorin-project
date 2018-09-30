import librosa
import numpy as np


def extract_features(wav):
    s_full, _ = librosa.magphase(librosa.stft(wav))
    spec = librosa.amplitude_to_db(s_full, ref=np.max)
    spec_mean = np.mean(spec, axis=1)
    spec_max = np.max(spec, axis=1)
    spec_min = np.min(spec, axis=1)
    x = np.concatenate((spec_mean, spec_max, spec_min))
    x = x.reshape((1, -1))
    return x
