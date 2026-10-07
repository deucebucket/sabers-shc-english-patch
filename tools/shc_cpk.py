#!/usr/bin/env python3
"""shc_cpk.py - Read Super Heroine Chronicle (PS3) CPK archives.

SHC's CPKs use CRI's LCG-XOR "encryption" on the @UTF tables plus
standard CRILAYLA compression on file contents.

Credits:
- DecryptUTF algorithm: wmltogether/CriPakTools (LibCPK/CPK.cs)
- CRILAYLA decompressor: retro-trans/SRW-Z3 (tools/cpk.py)

Usage:
    python3 shc_cpk.py list ShcPack.cpk
    python3 shc_cpk.py extract ShcPack.cpk "anime/003_Soniko_cutin.csv" -o out.csv
"""
import struct
import sys


def decrypt_utf(data):
    """CRI @UTF table 'encryption': LCG keystream XOR.

    m = 0x655f; per byte: out[i] = in[i] ^ (m & 0xff); m = m * 0x4115 (32-bit).
    Same operation decrypts and re-encrypts.
    """
    m, t = 0x655f, 0x4115
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = b ^ (m & 0xff)
        m = (m * t) & 0xFFFFFFFF
    return bytes(out)


def decompress_crilayla(src):
    """CRILAYLA: LZ variant that emits its output back-to-front.
    (from retro-trans/SRW-Z3 tools/cpk.py)"""
    if src[:8] != b"CRILAYLA":
        return src
    usize, dsize = struct.unpack_from("<II", src, 8)
    header = src[0x10 + dsize: 0x10 + dsize + 0x100]  # raw 0x100 prefix
    out = bytearray(usize)

    pos = 0x10 + dsize - 1   # bits are consumed backwards
    pool = bits = 0

    def take(n):
        nonlocal pos, pool, bits
        v = 0
        while n:
            if not bits:
                pool = src[pos]
                pos -= 1
                bits = 8
            k = min(n, bits)
            v = (v << k) | ((pool >> (bits - k)) & ((1 << k) - 1))
            bits -= k
            n -= k
        return v

    VLE = (2, 3, 5, 8)
    o = usize - 1
    while o >= 0:
        if take(1):
            ref = o + take(13) + 3
            ln = 3
            for width in VLE:
                d = take(width)
                ln += d
                if d != (1 << width) - 1:
                    break
            else:
                while True:
                    d = take(8)
                    ln += d
                    if d != 255:
                        break
            for _ in range(ln):
                out[o] = out[ref]
                o -= 1
                ref -= 1
                if o < 0:
                    break
        else:
            out[o] = take(8)
            o -= 1
    return header + bytes(out)


class UTFReader:
    """Minimal big-endian @UTF table parser (decrypted bytes in)."""

    def __init__(self, data):
        self.data = data
        assert data[:4] == b'@UTF', 'not a @UTF table'
        self.rows_offset = struct.unpack('>I', data[8:12])[0] + 8
        self.strings_offset = struct.unpack('>I', data[12:16])[0] + 8
        self.data_offset = struct.unpack('>I', data[16:20])[0] + 8
        self.num_columns = struct.unpack('>H', data[24:26])[0]
        self.row_length = struct.unpack('>H', data[26:28])[0]
        self.num_rows = struct.unpack('>I', data[28:32])[0]
        self.columns = []
        pos = 32
        for _ in range(self.num_columns):
            flags = data[pos]
            pos += 1
            if flags == 0:
                pos += 3
                flags = data[pos]
                pos += 1
            name = self.cstr(self.strings_offset +
                             struct.unpack('>I', data[pos:pos + 4])[0])
            pos += 4
            col = {'flags': flags, 'name': name}
            if (flags & 0xF0) == 0x30:  # STORAGE_CONSTANT
                col['value'], pos = self.read_typed(pos, flags)
            self.columns.append(col)
        self.rows = []
        for j in range(self.num_rows):
            row, rpos = {}, self.rows_offset + j * self.row_length
            for col in self.columns:
                s = col['flags'] & 0xF0
                if s == 0x30:
                    row[col['name']] = col['value']
                elif s in (0x00, 0x10):
                    row[col['name']] = 0 if s == 0x10 else None
                else:  # STORAGE_PERROW
                    row[col['name']], rpos = self.read_typed(rpos, col['flags'])
            self.rows.append(row)

    def cstr(self, off):
        end = self.data.index(b'\x00', off)
        return self.data[off:end].decode('utf-8', 'replace')

    def read_typed(self, pos, flags):
        d, t = self.data, flags & 0x0F
        if t in (0x00, 0x01):
            return d[pos], pos + 1
        if t in (0x02, 0x03):
            return struct.unpack('>H', d[pos:pos + 2])[0], pos + 2
        if t in (0x04, 0x05):
            return struct.unpack('>I', d[pos:pos + 4])[0], pos + 4
        if t in (0x06, 0x07):
            return struct.unpack('>Q', d[pos:pos + 8])[0], pos + 8
        if t == 0x08:
            return struct.unpack('>f', d[pos:pos + 4])[0], pos + 4
        if t == 0x0A:
            off = struct.unpack('>I', d[pos:pos + 4])[0]
            return self.cstr(self.strings_offset + off), pos + 4
        if t == 0x0B:
            off = struct.unpack('>I', d[pos:pos + 4])[0]
            sz = struct.unpack('>I', d[pos + 4:pos + 8])[0]
            return (self.data_offset + off, sz), pos + 8
        raise ValueError('unknown @UTF type %#x' % t)


def read_chunk(data, off, magic):
    """Read a (possibly encrypted) @UTF chunk: magic + LE u32 + LE u64 size."""
    assert data[off:off + 4] == magic, 'no %s at %#x' % (magic, off)
    size = struct.unpack('<q', data[off + 8:off + 16])[0]
    packet = data[off + 16:off + 16 + size]
    if packet[:4] != b'@UTF':
        packet = decrypt_utf(packet)
    return UTFReader(packet)


def get_files(path):
    """Returns (cpk_bytes, [file dicts]) for a CPK path."""
    with open(path, 'rb') as fh:
        data = fh.read()
    assert data[:4] == b'CPK '
    hdr = read_chunk(data, 0, b'CPK ')
    info = hdr.rows[0]
    toc_off = info.get('TocOffset')
    content_off = info.get('ContentOffset', 0)
    # add_offset logic from CriPakTools ReadTOC
    ftoc = toc_off if toc_off <= 0x800 else 0x800
    add_off = content_off if content_off < ftoc else ftoc
    toc = read_chunk(data, toc_off, b'TOC ')
    files = []
    for r in toc.rows:
        files.append({
            'dir': r.get('DirName') or '',
            'name': r.get('FileName'),
            'size': r.get('FileSize'),
            'extract_size': r.get('ExtractSize'),
            'offset': r.get('FileOffset') + add_off,
        })
    return data, files


def extract_file(data, f):
    raw = data[f['offset']:f['offset'] + f['size']]
    return decompress_crilayla(raw)


def cmd_list(path):
    data, files = get_files(path)
    print('%d files' % len(files))
    for f in files:
        print('  %s/%s  size=%s extract=%s off=%#x'
              % (f['dir'], f['name'], f['size'], f['extract_size'], f['offset']))


def cmd_extract(path, target, out):
    data, files = get_files(path)
    for f in files:
        if ('%s/%s' % (f['dir'], f['name'])).lstrip('/') == target.lstrip('/'):
            raw = extract_file(data, f)
            with open(out, 'wb') as fh:
                fh.write(raw)
            print('wrote %d bytes to %s' % (len(raw), out))
            return
    sys.exit('not found: %s' % target)




def cmd_tocinfo(path):
    """Dump @UTF schemas: CPK header, TOC, and ETOC if present.

    Diagnostic for the issue #5 repacker gap (per-file checksum not updated):
    run against the real ShcPack.cpk to see every column name and storage
    type, so a checksum/CRC field can be identified by name. It does not
    interpret the values, it only lists the schema.
    """
    with open(path, 'rb') as fh:
        data = fh.read()
    assert data[:4] == b'CPK ', 'not a CPK'
    hdr = read_chunk(data, 0, b'CPK ')
    info = hdr.rows[0]
    print('CPK header columns:')
    for col in hdr.columns:
        print('  %-16s storage=%#04x' % (col['name'], col['flags'] & 0xF0))
    toc = read_chunk(data, info.get('TocOffset'), b'TOC ')
    print('TOC columns (%d rows):' % toc.num_rows)
    for col in toc.columns:
        print('  %-16s storage=%#04x' % (col['name'], col['flags'] & 0xF0))
    etoc_off = info.get('EtocOffset')
    if etoc_off and info.get('EtocSize'):
        etoc = read_chunk(data, etoc_off, b'ETOC')
        print('ETOC columns (%d rows):' % etoc.num_rows)
        for col in etoc.columns:
            print('  %-16s storage=%#04x' % (col['name'], col['flags'] & 0xF0))
    else:
        print('no ETOC chunk')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit('usage: shc_cpk.py list|extract|tocinfo <cpk> [path] [-o out]')
    cmd = sys.argv[1]
    if cmd == 'list':
        cmd_list(sys.argv[2])
    elif cmd == 'extract':
        out = sys.argv[5] if len(sys.argv) > 5 and sys.argv[4] == '-o' else 'out.bin'
        cmd_extract(sys.argv[2], sys.argv[3], out)
    elif cmd == 'tocinfo':
        cmd_tocinfo(sys.argv[2])
    else:
        sys.exit('unknown command: %s' % cmd)
