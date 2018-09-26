import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import sys
import signal
import os
import re
import tempfile
import numpy as np
import multiprocessing

import librosa
import librosa.display
import tqdm

js = '''
<script type="text/javascript">
let playlist = document.getElementById("playlist");
let nodes = [];
let children = playlist.children;
let items = [];
let next = 0;
let speed = 1;
let set = new Set();
let playing = false;

function playNext() {
    let videoPlayer = document.getElementById('videoPlayer');
    if (0 <= next && next < items.length) {
        playing = true;
        videoPlayer.pause();
        for (let node of nodes) {
            node.classList.remove('playing');
        }
        let node = nodes[next];

        Element.prototype.documentOffsetTop = function () {
            return this.offsetTop + ( this.offsetParent ? this.offsetParent.documentOffsetTop() : 0 );
        };
        var top = node.documentOffsetTop() - ( window.innerHeight / 2 );
        window.scrollTo(0, top);


        node.classList.add('playing');
        videoPlayer.src = items[next];
        videoPlayer.playbackRate = speed;
        videoPlayer.play();
    } else {
        playing = false;
    }
    next++;
}

function toggle() {
    let cur = next - 1;
    if (0 <= cur && cur < items.length) {
        if (set.has(cur)) {
            set.delete(cur);
        } else {
            set.add(cur);
        }
        for (let node of nodes) {
            node.classList.remove('music');
        }
        let result = document.getElementById('result');
        result.textContent = "";
        for (let a of set) {
            result.textContent += items[a];
            result.textContent += "\\n";
            nodes[a].classList.add('music');
        }
    }
}

function speedUp() {
    let videoPlayer = document.getElementById('videoPlayer');
    speed = speed + 0.5;
    videoPlayer.playbackRate = speed;
}

function speedDown() {
    let videoPlayer = document.getElementById('videoPlayer');
    speed = Math.max(speed - 0.5, 0.5);
    videoPlayer.playbackRate = speed;
}

function init() {
    for (var i = 0; i < children.length; i++) {
        let child = children[i];
        let text = child.textContent;
        nodes.push(child);
        items.push(text);
        const idx = i;
        child.addEventListener('click', (e) => {
            console.log(idx);
            next = idx;
            playNext();
        });
    }

    playNext();
    videoPlayer.onended = function () {
        playNext();
    }

    document.getElementById("copy-button").addEventListener('click', (e) => {
        let result = document.getElementById('result');
        result.select();
        document.execCommand('copy');
    });

    document.addEventListener('keydown', (event) => {
        const keyName = event.key;
        if (keyName === 'e') {
            toggle();
        } else if (keyName === '>') {
            speedUp();
        } else if (keyName === '<') {
            speedDown();
        } else if (keyName === 'ArrowLeft') {
            next = Math.max(0, next - 2);
            playNext();
        } else if (keyName === 'ArrowRight') {
            next = Math.min(items.length, next);
            playNext();
        }
        console.log(keyName);
    });
}

setTimeout(init, 100);
</script>
'''

def sort(names):
    def f(name):
        items = list(re.split('[-_\./]', name))
        new_items = []
        for item in items:
            try:
                item = int(item)
            except Exception as ex:
                pass
            new_items.append(item)
        return new_items
    names.sort(key=f)
    return names

def make(names, paths):
    content = ''
    for name, path in zip(names, paths):
        content += '<div class="item", style="background-position: center right; background-repeat: no-repeat; background-image: url(\'{}\');"><p>{}</p></div>'.format(path, name)
        content += '\n'

    html = '''
<html lang="en">
<head>
<meta charset="utf-8"/>
<style type="text/css">
#copy-button {font-size: 32px;}
.playing {
    border-color: lime;
    border-width: 5px;
}
.music {
    background-color: red;
    font-weight: bold;
}
.item {
    border-style: solid;
    margin: 3px 3px
    }
</style>
</head>
<body>
<ul>
<li>クリック: 再生する.wavを切り替え</li>
<li>e: アノテーション切り替え</li>
<li>→: 次</li>
<li>←: 前</li>
<li>&gt;: 速く</li>
<li>&lt;: 遅く</li>
</ul>
<div id="playlist">''' + content + '''
</div>
<button id="copy-button">Copy to clipboard</button>
<form><textarea id="result" style="width: 500px; height: 500px;"></textarea></form>
<audio id="videoPlayer" src="" autobuffer controls></audio>
'''  + js + '''
</body>
</html>
    '''
    return html

def process(args):
    name, path = args
    arr = librosa.feature.melspectrogram(*librosa.load(name), n_mels=80, fmax=8000)
    arr = arr ** 1.2
    #im = Image.fromarray(arr)
    #im.save(path[1])
    plt.figure(figsize=(10, 1))
    librosa.display.specshow(librosa.power_to_db(arr, ref=np.max), fmax=8000)
    #plt.colorbar()
    plt.tight_layout()
    plt.savefig(path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('wav_dir')
    parser.add_argument('--port', type=int, default=8080)

    args = parser.parse_args()

    names = []
    for a, _, c in os.walk(args.wav_dir):
        for p in c:
            if p.endswith('.wav'):
                names.append(os.path.join(a, p))
    names = sort(names)
    print(names, file=sys.stderr)

    dpath = tempfile.mkdtemp(dir='.')
    def mk_path(p):
        p = tempfile.mkstemp(dir=dpath, suffix='.png')[1]
        basepath = os.path.dirname(__file__)
        prefix = os.path.commonprefix([basepath, p])
        return os.path.relpath(p, prefix)
    paths = list(map(mk_path, names))
    html = make(names, paths)

    with open('index.html', 'w') as f:
        print(html, file=f)
    print('Written to index.html', file=sys.stderr)

    original_sigint = signal.getsignal(signal.SIGINT)
    def exit_gracefully(signum, frame):
        # restore the original signal handler as otherwise evil things will happen
        # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
        signal.signal(signal.SIGINT, original_sigint)
        for path in paths:
            os.remove(path)
        os.rmdir(dpath)
    signal.signal(signal.SIGINT, exit_gracefully)

    import http.server
    import socketserver
    PORT = args.port
    Handler = http.server.SimpleHTTPRequestHandler
    print('Starting server...', file=sys.stderr)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print('Rendering images...', file=sys.stderr)
        pool = multiprocessing.Pool()
        list(tqdm.tqdm(pool.imap(process, zip(names, paths)), total=len(paths)))

        print("serving at port", PORT)
        httpd.serve_forever()



if __name__ == '__main__':
    main()

