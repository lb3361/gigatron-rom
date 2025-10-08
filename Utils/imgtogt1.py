#!/usr/bin/env python3

import sys, os, argparse, re
from PIL import Image
import PIL


# ----------------------------------------
# UTILITIES

verbose = 0
progname = 'imgtogt1'

def convert(args):
    im = Image.open(args.infile).convert('RGB')
    size = im.size
    if args.verbose > 0:
        print(f"original image size {size}")
    if args.aspect:
        newsize = (args.maxw, args.maxh)
    else:
        scalefactor = min(args.maxw / size[0], args.maxh / size[1])
        newsize = ( int(size[0] * scalefactor), int(size[1] * scalefactor) )
    if args.verbose > 0:
        print(f"scaled image size {newsize}")
    scaled_im = im.resize(newsize, resample=getattr(Image.Resampling, args.method))
    starth = (args.start & 0xff00) >> 8
    startl = args.start & 0xff;
    if (starth + newsize[1] > 256):
        raise RuntimeError(f"image extends beyond 64k boundary")
    if (startl + newsize[0] > 256):
        raise RuntimeError(f"image rows extends beyond page boundary")
    with open(args.outfile, "wb") as fo:
        for y in range(newsize[1]):
            fo.write(bytes((y+starth,startl, newsize[0] & 0xff)))
            row = []
            for x in range(newsize[0]):
                r, g, b = scaled_im.getpixel((x, y))
                row.append( (r//85) + 4*(g//85) + 16*(b//85) )
            fo.write(bytes(row))
        fo.write(bytes((0,0x00,0x00)))


# ----------------------------------------
# MAIN


def main(argv):
    global verbose
    parser = argparse.ArgumentParser(
        usage='imgtogt1.py [options] infile [outfile.gt1]',
        description='Convert an image into a GT1 file')
    parser.add_argument('-s', '--size', action='store', type=str, default='160x120',
                        help='requested image size')
    parser.add_argument('-m', '--method', action='store', type=str, default='LANCZOS',
                        help='resampling method (default: LANCZOS)')
    parser.add_argument('-a', '--aspect', action='store_true',
                        help='do not maintain scaling ratio')
    parser.add_argument('--start', action='store', type=str, default='0x800',
                        help='starting address in memory')
    parser.add_argument('-f', '--force', action='store_true',
                        help='overwrites output file')
    parser.add_argument('-v', '--verbose', action='count',
                        help='print verbose message')
    parser.add_argument('infile', help='input file')
    parser.add_argument('outfile', nargs='?', help='output file')
    args = parser.parse_args(argv)
    args.verbose = args.verbose or 0
    if not args.outfile:
        (stem,ext) = os.path.splitext(args.infile)
        args.outfile = stem + '.gt1'
    if not args.outfile.endswith('.gt1'):
        print(f"{progname}: warning: {s}", file=sys.stderr)
    if os.path.exists(args.outfile) and not args.force:
        raise RuntimeError(f"not overwriting existing file '{args.outfile}'")
    try:
        match = re.match(r"([0-9]+)x([0-9]+)", args.size)
        args.maxw = int(match.group(1))
        args.maxh = int(match.group(2))
    except:
        raise RuntimeError(f"Cannot parse size argument {args.size}")
    try:
        args.start = int(args.start, 0)
    except:
        raise RuntimeError(f"Cannot parse start argument {args.start}")
    if not 1 < args.maxw <= 256 or not 1 < args.maxh <= 120:
        raise RuntimeError(f"requested size {args.w}x{args.h} out of range")
    if not hasattr(Image.Resampling,args.method):
        raise RuntimeError(f"unknown resampling method: {args.method}")
        

    convert(args)

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except RuntimeError as err:
        print(f"imgtogt1: error: {str(err)}")
    except Exception as err:
        print(f"imgtogt1: error: {repr(err)}")
    sys.exit(10)

