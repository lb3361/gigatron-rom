#!/usr/bin/env python3

import sys, os, argparse, re

# ----------------------------------------
# UTILITIES

progname = 'gtbtogt1'

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

    r'''
        [ 0 p= \SYS_ReadRomDir_v5_80 _sysFn=
          [do p 80!! p=
            $6954 _sysArgs0^ if<>0loop
            $796e _sysArgs2^ if<>0loop
            $4142 _sysArgs4^ if<>0loop
            $4953 _sysArgs6^ if<>0loop]
          p _sysArgs0= \SYS_Exec_88 _sysFn= [def 88!!] call
          \buffer p= \address p: $200 _vLR= ret ]
    '''

    boot = [ 0x59, 0x00, 0x2b, 0x30, 0x59, 0xef, 0x2b, 0x22, 0x21,
             0x30, 0xb4, 0xe6, 0x2b, 0x30, 0x11, 0x54, 0x69, 0xfc,
             0x24, 0x35, 0x72, 0xa6, 0x11, 0x6e, 0x79, 0xfc, 0x26,
             0x35, 0x72, 0xa6, 0x11, 0x42, 0x41, 0xfc, 0x28, 0x35,
             0x72, 0xa6, 0x11, 0x53, 0x49, 0xfc, 0x2a, 0x35, 0x72,
             0xa6, 0x21, 0x30, 0x2b, 0x24, 0x59, 0xad, 0x2b, 0x22,
             0xcd, 0xd8, 0xb4, 0xe2, 0xcf, 0x18, 0x11, lo(buffer),
             hi(buffer), 0x2b, 0x30, 0x11, lo(address), hi(address),
             0xf3, 0x30, 0x11, 0x00, 0x02, 0x2b, 0x1a, 0xff ]

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
        print(f"gtbtogt1: error: {str(err)}")
    except Exception as err:
        print(f"gtbtogt1: error: {repr(err)}")
    sys.exit(10)

