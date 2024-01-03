#!/usr/bin/env python3

import sys, os, argparse, re
from PIL import Image
import PIL


# ----------------------------------------
# UTILITIES

progname = 'imgtogt1'

def lo(x):
    return x & 0xff

def hi(x):
    return (x >> 8) & 0xff

def convert(args):
    address = args.start
    outbytes = bytearray()
    
    # basic lines
    with open(args.infile,'r') as fin:
        for line in fin:
            line = line.strip()
            number, text = '', ''
            for c in line:
                if c.isdigit() and len(text) == 0:
                    number += c;
                else:
                    text += c;
            number = int(number) if len(number) > 0 else 0
            if len(text) > 28:
                msg = 'is too long' if len(line) < 26 else 'has been truncated'
                print(f"{progname}: warning: line {number} {msg}")
            text=text[0:28]
            outbytes.extend([hi(address), lo(address), len(text)+3, lo(number), hi(number)])
            outbytes.extend([ord(c) for c in text] + [0])
            if args.verbose >= 1:
                print(f"{address:04x}: {number:5d} {text}")
            address += 32
            if address & 255 == 0:
                address += 160
            if address >= 0x7fa0:
                raise RuntimeError(f"program is too big")

    # startup command
    outbytes.extend([hi(address+2), lo(address+2), 4])
    outbytes.extend([ord(c) for c in "RUN"] + [0])

    # boot code
    buffer = args.start - 32
    boot=  [ 0x59, 0xef,                     #  LDI    SYS_ReadRomDir
             0x2b, 0x22,                     #  STW    sysFn
             0x59, 0x00,                     #  LDI    0
             0xb4, 0xe6,                     #  SYS    80
             0x2b, 0x30,                     #  STW    $30
             0x35, 0x3f, 0xe9,               #  BEQ    loop
             0x11, 0x54, 0x69,               #  LDWI   $6954
             0xfc, 0x24,                     #  XORW   $24
             0x35, 0x72, 0xe9,               #  BNE    loop
             0x11, 0x6e, 0x79,               #  LDWI   $796e
             0xfc, 0x26,                     #  XORW   $26
             0x35, 0x72, 0xe9,               #  BNE    loop
             0x11, 0x42, 0x41,               #  LDWI   $4142
             0xfc, 0x28,                     #  XORW   $28
             0x35, 0x72, 0xe9,               #  BNE    loop
             0x11, 0x53, 0x49,               #  LDWI   $4953
             0xfc, 0x2a,                     #  XORW   $2a
             0x35, 0x72, 0xe9,               #  BNE    loop
             0x21, 0x30,                     #  LDW    $30
             0x2b, 0x24,                     #  STW    sysArgs
             0x59, 0xad,                     #  LDI    SYS_Exec_88
             0x2b, 0x22,                     #  STW    sysFn
             0xcd, 0xd7,                     #  DEF    *+2
             0xb4, 0xe2,                     #  SYS    88
             0xcf, 0x18,                     #  CALL   vAC
             0x11, lo(buffer), hi(buffer),   #  LDWI   buffer
             0x2b, 0x30,                     #  STW    $30
             0x11, lo(address), hi(address), #  LDWI   $7777
             0xf3, 0x30,                     #  DOKE   $30
             0x11, 0x00, 0x02,               #  LDWI   $0200
             0x2b, 0x1a,                     #  STW    vLR
             0xff,                           #  RET
             0x21, 0x30,               # loop:  LDW    $30
             0x35, 0x72, 0xa4,               #  BNE    $0206
             0xb4, 0x80 ]                    #  HALT

    outbytes.extend([0x7f, 0xa0, len(boot)])
    outbytes.extend(boot)
    outbytes.extend([0, 0x7f, 0xa0])
    # write gt1
    with open(args.outfile,"wb") as fout:
        fout.write(outbytes)


# ----------------------------------------
# MAIN


def main(argv):
    parser = argparse.ArgumentParser(
        usage='gtbtogt1.py [options] infile [outfile.gt1]',
        description='Convert an image into a GT1 file')
    parser.add_argument('--start', action='store', type=str, default='0x1bc0',
                        help='starting address of basic programs')
    parser.add_argument('-f', '--force', action='store_true',
                        help='overwrites output file')
    parser.add_argument('-v', '--verbose', action='count',
                        help='print verbose message')
    parser.add_argument('infile', help='input file')
    parser.add_argument('outfile', nargs='?', help='output file')
    args = parser.parse_args(argv)
    args.verbose = args.verbose or 0

    stem = args.infile
    if args.infile.endswith('.gtb'):
        stem = args.infile[0:-4]
    if not args.infile.endswith('.gtb'):
        print(f"{progname}: warning: input file '{args.infile}' does not end with suffix '.gtb'", file=sys.stderr)
    if not args.outfile:
        args.outfile = stem + '.gt1'
    if not args.outfile.endswith('.gt1'):
        print(f"{progname}: warning: output file '{args.outfile}' does not end with suffix '.gt1'", file=sys.stderr)
    if os.path.exists(args.outfile) and not args.force:
        raise RuntimeError(f"not overwriting existing file '{args.outfile}'")
    try:
        args.start = int(args.start, 0)
    except:
        raise RuntimeError(f"Cannot parse start address {args.start}")

    convert(args)

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except RuntimeError as err:
        print(f"gt1z: error: {str(err)}")
    except Exception as err:
        print(f"gt1z: error: {repr(err)}")
    sys.exit(10)

