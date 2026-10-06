#!/usr/bin/env python3
"""CRILAYLA compressor — produces valid streams for SHC's CPK repacker.

Round-trip property: decompress_crilayla(compress_crilayla(x)) == x
(decompressor from retro-trans/SRW-Z3 tools/cpk.py).
"""
import struct


def compress_crilayla(data):
    """Compress bytes into CRILAYLA format."""
    # First 0x100 bytes are stored raw; the rest is LZ-compressed back-to-front.
    raw_prefix = data[:0x100]
    tail = data[0x100:]
    usize = len(tail)

    # --- tokenize back-to-front ---
    # The decompressor fills output BACKWARDS: a match token at position o
    # covers output[o-ln+1 .. o], copying from already-decoded ref = o+off+3.
    # So each token covers a segment ENDING at i; find the longest match for
    # input[i-ln+1 .. i] sourced from input[j-ln+1 .. j], j in i+3..i+8194.
    tokens = []  # (is_match, off_or_byte, length)
    i = usize - 1
    n = usize
    while i >= 0:
        best_len, best_off = 0, 0
        for j in range(i + 3, min(i + 8195, n)):
            ln = 0
            while i - ln >= 0 and j - ln >= 0 and tail[i - ln] == tail[j - ln]:
                ln += 1
            if ln > best_len:
                best_len, best_off = ln, j - i
        if best_len >= 3:
            tokens.append((True, best_off, best_len))
            i -= best_len
        else:
            tokens.append((False, tail[i], 0))
            i -= 1

    # --- emit bits in token order ---
    bits = []  # list of 0/1, first bit = first read by decompressor

    def emit(value, width):
        for b in range(width - 1, -1, -1):
            bits.append((value >> b) & 1)

    def emit_length(ln):
        extra = ln - 3
        for width, mx in ((2, 3), (3, 7), (5, 31)):
            d = min(extra, mx)
            emit(d, width)
            extra -= d
            if d < mx:
                return
        while True:
            d = min(extra, 255)
            emit(d, 8)
            extra -= d
            if d < 255:
                return

    for tok in tokens:
        if tok[0]:
            _, off, ln = tok
            emit(1, 1)
            emit(off - 3, 13)
            emit_length(ln)
        else:
            _, byte, _ = tok
            emit(0, 1)
            emit(byte, 8)

    # --- pack bits: first bit -> MSB of LAST byte ---
    nbytes = (len(bits) + 7) // 8
    packed = bytearray(nbytes)
    for i, b in enumerate(bits):
        if b:
            byte_idx = nbytes - 1 - (i // 8)
            bit_pos = 7 - (i % 8)
            packed[byte_idx] |= (1 << bit_pos)

    dsize = len(packed)
    out = bytearray()
    out += b'CRILAYLA'
    out += struct.pack('<II', usize, dsize)
    out += bytes(packed)
    out += raw_prefix
    # pad raw prefix to 0x100 if short
    if len(raw_prefix) < 0x100:
        out += b'\x00' * (0x100 - len(raw_prefix))
    return bytes(out)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/tmp')
    from shc_cpk import decompress_crilayla
    data = open(sys.argv[1], 'rb').read()
    c = compress_crilayla(data)
    rt = decompress_crilayla(c)
    print('orig:', len(data), 'compressed:', len(c), 'roundtrip_ok:', rt == data)
