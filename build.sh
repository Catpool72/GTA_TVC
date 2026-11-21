#!/bin/sh
set -e
cd "$(dirname "$0")"
SJ=${SJASMPLUS:-sjasmplus}
python3 gen.py
$SJ --nologo --sym=gtt6.sym --lst=gtt6.lst gtt6.asm
python3 mkcas.py gtt6.bin gtt6.cas
