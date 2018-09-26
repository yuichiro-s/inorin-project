import sys
import os
import re

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
        nodes[next].classList.add('playing');
        videoPlayer.src = items[next];
        videoPlayer.playbackRate = speed;
        videoPlayer.play();
    } else {
        playing = false;
    }
    next++;
}

function toggle() {
    if (playing) {
        let cur = next - 1;
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

    document.addEventListener('keydown', (event) => {
        const keyName = event.key;
        if (keyName === 'e') {
            toggle();
        } else if (keyName === '+') {
            speedUp();
        } else if (keyName === '-') {
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

def make(names):
    content = ''
    for name in names:
        content += '<div class="item">{}</div>'.format(name)
        content += '\n'

    html = '''
<html lang="en">
<head>
<meta charset="utf-8"/>
<style type="text/css">
.playing {background-color:blue;}
.music {
    color: red;
}
.item {
    margin: 5 5;
    padding: 5px;
    border: medium solid black;
    }
</style>
</head>
<body>
<ul>
<li>クリック: 再生する.wavを切り替え</li>
<li>e: アノテーション切り替え</li>
<li>→: 次</li>
<li>←: 前</li>
<li>+: 速く</li>
<li>-: 遅く</li>
</ul>
<div id="playlist">''' + content + '''
</div>
<form><textarea id="result" style="width: 500px; height: 500px;"></textarea></form>
<audio id="videoPlayer" src="" autobuffer controls>
'''  + js + '''
</body>
</html>
    '''
    return html

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
    html = make(names)

    with open('index.html', 'w') as f:
        print(html, file=f)
    print('Written to index.html', file=sys.stderr)

    import http.server
    import socketserver
    PORT = args.port
    Handler = http.server.SimpleHTTPRequestHandler
    print('Starting server...', file=sys.stderr)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()


if __name__ == '__main__':
    main()

