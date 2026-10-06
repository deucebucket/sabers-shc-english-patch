#!/usr/bin/env python3
"""shc_repack.py - Rebuild an SHC CPK with replaced files.

Surgical approach: file contents are re-laid out, but the @UTF tables are
patched in-place (numeric fields only), so their size and structure never
change. Patched files are recompressed with CRILAYLA.

Usage:
    python3 shc_repack.py orig.cpk out.cpk replacements.json
    replacements.json: {"internal/path/file.csv": "/local/new_file.csv", ...}
    (local files are raw uncompressed bytes)
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shc_cpk import decrypt_utf, UTFReader, read_chunk
from crilayla_comp import compress_crilayla


def skip_typed(data, pos, flags):
    t = flags & 0x0F
    if t in (0x00, 0x01):
        return pos + 1
    if t in (0x02, 0x03):
        return pos + 2
    if t in (0x04, 0x05):
        return pos + 4
    if t in (0x06, 0x07):
        return pos + 8
    if t == 0x08:
        return pos + 4
    if t == 0x0A:
        return pos + 4
    if t == 0x0B:
        return pos + 8
    raise ValueError('bad type %#x' % t)


def utf_field_offsets(data):
    """Map (row_idx, col_name) -> (byte_offset_in_data, type) for PERROW fields."""
    assert data[:4] == b'@UTF'
    rows_offset = struct.unpack('>I', data[8:12])[0] + 8
    strings_offset = struct.unpack('>I', data[12:16])[0] + 8
    num_columns = struct.unpack('>H', data[24:26])[0]
    row_length = struct.unpack('>H', data[26:28])[0]
    num_rows = struct.unpack('>I', data[28:32])[0]
    cols = []
    pos = 32
    for _ in range(num_columns):
        flags = data[pos]
        pos += 1
        if flags == 0:
            pos += 3
            flags = data[pos]
            pos += 1
        name_off = struct.unpack('>I', data[pos:pos + 4])[0]
        pos += 4
        end = data.index(b'\x00', strings_offset + name_off)
        name = data[strings_offset + name_off:end].decode('utf-8', 'replace')
        cols.append((name, flags))
        if (flags & 0xF0) == 0x30:
            pos = skip_typed(data, pos, flags)
    offsets = {}
    for j in range(num_rows):
        rpos = rows_offset + j * row_length
        for (name, flags) in cols:
            if (flags & 0xF0) != 0x50:
                continue
            offsets[(j, name)] = (rpos, flags & 0x0F)
            rpos = skip_typed(data, rpos, flags)
    return offsets


def patch_u32(blob, off, val):
    return blob[:off] + struct.pack('>I', val) + blob[off + 4:]


def patch_u64(blob, off, val):
    return blob[:off] + struct.pack('>Q', val) + blob[off + 8:]


def get_toc_info(orig):
    hdr = read_chunk(orig, 0, b'CPK ')
    info = hdr.rows[0]
    toc_off = info['TocOffset']
    content_off = info.get('ContentOffset', 0)
    ftoc = toc_off if toc_off <= 0x800 else 0x800
    add_off = content_off if content_off < ftoc else ftoc
    # raw (still encrypted) TOC packet bounds
    tsize = struct.unpack('<q', orig[toc_off + 8:toc_off + 16])[0]
    return hdr, info, toc_off, tsize, add_off


def repack(orig_path, replacements, out_path):
    """replacements: {internal_cpk_path: local_file_with_new_raw_bytes}"""
    with open(orig_path, 'rb') as f:
        orig = f.read()
    assert orig[:4] == b'CPK '

    hdr, info, toc_off, toc_size, add_off = get_toc_info(orig)
    align = info.get('Align', 2048)
    content_off = info.get('ContentOffset', 0)
    # --- parse TOC rows ---
    toc_packet = orig[toc_off + 16:toc_off + 16 + toc_size]
    toc_dec = decrypt_utf(toc_packet)
    toc = UTFReader(toc_dec)
    toc_offsets = utf_field_offsets(toc_dec)

    # --- decrypt header for patching ---
    hdr_size = struct.unpack('<q', orig[8:16])[0]
    hdr_packet = orig[16:16 + hdr_size]
    hdr_dec = decrypt_utf(hdr_packet)
    hdr_offsets = utf_field_offsets(hdr_dec)

    # --- build new content area ---
    new_content = bytearray()
    new_rows = []  # (FileOffset, FileSize, ExtractSize)
    cur = content_off
    for j, r in enumerate(toc.rows):
        ipath = ((r.get('DirName') or '') + '/' + (r.get('FileName') or '')).lstrip('/')
        orig_off = r['FileOffset'] + add_off
        orig_size = r['FileSize']
        if ipath in replacements:
            with open(replacements[ipath], 'rb') as f:
                new_raw = f.read()
            comp = compress_crilayla(new_raw)
            extract_size = len(new_raw)
            print('PATCH %s: %d -> %d bytes' % (ipath, orig_size, len(comp)))
        else:
            comp = orig[orig_off:orig_off + orig_size]
            extract_size = r['ExtractSize']
        # align
        pad = (-cur) % align
        new_content += b'\x00' * pad
        cur += pad
        # TOC FileOffset is relative to add_off (reader does FileOffset+add_off)
        new_rows.append((cur - add_off, len(comp), extract_size))
        new_content += comp
        cur += len(comp)

    # --- patch TOC @UTF in place ---
    toc_new = toc_dec
    for j, (foff, fsize, esize) in enumerate(new_rows):
        for col, val, patch in (('FileOffset', foff, patch_u64),
                                ('FileSize', fsize, patch_u32),
                                ('ExtractSize', esize, patch_u32)):
            off, typ = toc_offsets[(j, col)]
            toc_new = patch(toc_new, off, val)
    assert len(toc_new) == len(toc_dec)
    toc_enc = decrypt_utf(toc_new)  # XOR is symmetric

    # --- ETOC: copy chunk as-is, place after content ---
    etoc_off = info['EtocOffset']
    etoc_size = info['EtocSize']
    etoc_chunk = orig[etoc_off:etoc_off + 16 + etoc_size]
    assert etoc_chunk[:4] == b'ETOC'
    new_etoc_off = cur + ((-cur) % align)

    # --- patch header @UTF in place ---
    hdr_new = hdr_dec
    content_size = cur - content_off
    off, typ = hdr_offsets[(0, 'ContentSize')]
    hdr_new = patch_u64(hdr_new, off, content_size)
    off, typ = hdr_offsets[(0, 'EtocOffset')]
    hdr_new = patch_u64(hdr_new, off, new_etoc_off)
    assert len(hdr_new) == len(hdr_dec)
    hdr_enc = decrypt_utf(hdr_new)

    # --- assemble ---
    out = bytearray()
    out += b'CPK '
    out += struct.pack('<i', 0)
    out += struct.pack('<q', len(hdr_enc))
    out += hdr_enc
    # pad to 0x7FA, write (c)CRI, TOC at 0x800
    out += b'\x00' * (0x7FA - len(out))
    out += b'(c)CRI'
    assert len(out) == 0x800
    out += b'TOC '
    out += struct.pack('<i', 0)
    out += struct.pack('<q', len(toc_enc))
    out += toc_enc
    out += b'\x00' * (content_off - len(out))
    assert len(out) == content_off
    out += new_content
    out += b'\x00' * (new_etoc_off - len(out))
    assert len(out) == new_etoc_off
    out += etoc_chunk

    with open(out_path, 'wb') as f:
        f.write(out)
    print('wrote %s (%d bytes), %d files' % (out_path, len(out), len(new_rows)))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit('usage: shc_repack.py orig.cpk out.cpk replacements.json')
    repack(sys.argv[1], json.load(open(sys.argv[3])), sys.argv[2])
