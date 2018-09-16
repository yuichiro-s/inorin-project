import os
import json
import jaconv
import librosa

DEFAULT_CONFIDENCE = 1.0


def process(words):
    current_segment = []
    segments = []

    def make_segment():
        nonlocal current_segment

        if len(current_segment) <= 1:
            return

        # TODO: trim first word if its duration is too long
        start_time_first = current_segment[0][4]
        end_time_first = current_segment[0][5]
        duration_first = end_time_first - start_time_first
        if duration_first >= 1:
            current_segment.pop(0)

        if len(current_segment) == 0:
            return

        _, _, _, _, start_time, _ = current_segment[0]
        _, _, _, _, _, end_time = current_segment[-1]

        kanji_str = ''.join(map(lambda x: x[0], current_segment))
        yomi_str = ''.join(map(lambda x: x[1], current_segment))

        for a, b, c, d, _, _ in \
                current_segment:
            print('\t'.join(map(str, [a, b, c, d])))
        print()

        duration = end_time - start_time
        if duration > 0 and len(kanji_str) > 0 and len(yomi_str) > 0:
            segments.append((kanji_str, yomi_str, start_time, duration))

        current_segment = []

    for word in words:
        start_time = float(word['startTime'][:-1])
        end_time = float(word['endTime'][:-1])
        duration = end_time - start_time

        confidence = float(word.get('confidence', DEFAULT_CONFIDENCE))

        word = word['word']
        es = word.split('|')
        if len(es) == 1:
            yomi = es[0]
            kanji = yomi
        else:
            yomi = es[1].split(',')[0]
            kanji = es[0]
        yomi = jaconv.kata2hira(yomi)

        n = len(yomi)
        if (n >= 2 and duration > n * 0.2) or (n == 1 and duration > 0.5):
            make_segment()

        current_segment.append(
            (kanji, yomi, confidence, duration, start_time, end_time))

    if len(current_segment) > 0:
        make_segment()

    yield from segments


def main(args):
    with open(args.txt) as f, open(args.csv_out, 'w') as f_csv:
        obj = json.load(f)
        response = obj['response']['results']

        idx = 1
        for item in response:
            for alternative in item['alternatives']:
                words = alternative['words']

                for kanji_str, yomi_str, start_time, duration in process(words):
                    id_str = os.path.basename(args.wav).replace('.wav',
                                                                '') + '-' + str(idx)
                    wav_out = os.path.join(args.wav_out, id_str + '.wav')

                    y, sr = librosa.load(args.wav, offset=start_time+0.1, duration=duration+0.3)
                    librosa.output.write_wav(wav_out, y, sr)
                    print('|'.join([id_str, kanji_str, yomi_str]), file=f_csv)
                    idx += 1


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Make LJSpeech format dataset')
    parser.add_argument('wav', help='.wav file')
    parser.add_argument('txt', help='ASR output in JSON')
    parser.add_argument('wav_out', help='output directory of split wav files')
    parser.add_argument('csv_out', help='metadata')

    main(parser.parse_args())
