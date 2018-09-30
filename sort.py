import sys
import re

def main():
    lines = []
    for line in sys.stdin:
        line = line.strip()
        es = []
        for e in re.split('[-_\./]', line):
            try:
                e = int(e)
            except:
                pass
            es.append(e)
        lines.append((es, line))
    lines.sort()
    for _, line in lines:
        print(line)

if __name__ == '__main__':
    main()
