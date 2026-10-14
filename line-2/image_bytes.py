"""Small RGB PNG reader/writer and baseline JPEG thumbnail encoder, stdlib only.

These utilities prepare delivery bytes, not the painting: its pigment is generated
by the installed image tool. The JPEG uses custom valid canonical Huffman tables.
"""
import math
import struct
import zlib


def read_png(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG')
    offset, compressed = 8, bytearray()
    while offset < len(data):
        size = int.from_bytes(data[offset:offset+4], 'big')
        kind = data[offset+4:offset+8]
        body = data[offset+8:offset+8+size]
        crc = int.from_bytes(data[offset+8+size:offset+12+size], 'big')
        if zlib.crc32(kind + body) != crc:
            raise ValueError('PNG CRC mismatch')
        if kind == b'IHDR':
            w, h, bits, color, compression, filters, interlace = struct.unpack('>IIBBBBB', body)
            if (bits, color, compression, filters, interlace) != (8, 2, 0, 0, 0):
                raise ValueError('only noninterlaced 8-bit RGB PNG supported')
        elif kind == b'IDAT':
            compressed.extend(body)
        elif kind == b'IEND':
            break
        offset += size + 12
    raw = zlib.decompress(compressed)
    stride = w * 3
    if len(raw) != (stride + 1) * h:
        raise ValueError('PNG decompressed length mismatch')
    pixels, previous = bytearray(), bytearray(stride)
    for y in range(h):
        filter_type = raw[y*(stride+1)]
        row = bytearray(raw[y*(stride+1)+1:(y+1)*(stride+1)])
        for i in range(stride):
            a = row[i-3] if i >= 3 else 0
            b = previous[i]
            c = previous[i-3] if i >= 3 else 0
            if filter_type == 1:
                prediction = a
            elif filter_type == 2:
                prediction = b
            elif filter_type == 3:
                prediction = (a+b)//2
            elif filter_type == 4:
                p = a+b-c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                prediction = a if pa <= pb and pa <= pc else b if pb <= pc else c
            elif filter_type == 0:
                prediction = 0
            else:
                raise ValueError('bad PNG filter')
            row[i] = (row[i] + prediction) & 255
        pixels.extend(row)
        previous = row
    return w, h, pixels


def png(w, h, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data))
    raw = b''.join(b'\0' + pixels[y*w*3:(y+1)*w*3] for y in range(h))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def resize(w, h, pixels, edge=512):
    # Area averaging keeps the rough stone/pigment at thumbnail scale.
    result = bytearray(edge*edge*3)
    for y in range(edge):
        y0, y1 = y*h//edge, max(y*h//edge+1, (y+1)*h//edge)
        for x in range(edge):
            x0, x1 = x*w//edge, max(x*w//edge+1, (x+1)*w//edge)
            total = [0, 0, 0]
            for sy in range(y0, y1):
                for sx in range(x0, x1):
                    start = (sy*w+sx)*3
                    for c in range(3):
                        total[c] += pixels[start+c]
            count = (x1-x0)*(y1-y0)
            index = (y*edge+x)*3
            result[index:index+3] = bytes(v//count for v in total)
    return result


def jpeg(w, h, pixels, quality=52):
    """Baseline 4:2:0 JFIF JPEG; dimensions must be multiples of 16."""
    if w % 16 or h % 16:
        raise ValueError('JPEG dimensions must be multiples of 16')
    zigzag = []
    for diagonal in range(15):
        positions = [(y, diagonal-y) for y in range(8) if 0 <= diagonal-y < 8]
        if diagonal % 2 == 0:
            positions.reverse()
        zigzag.extend(y*8+x for y, x in positions)
    base_quant = [16,11,10,16,24,40,51,61,12,12,14,19,26,58,60,55,
                  14,13,16,24,40,57,69,56,14,17,22,29,51,87,80,62,
                  18,22,37,56,68,109,103,77,24,35,55,64,81,104,113,92,
                  49,64,78,87,103,121,120,101,72,92,95,98,112,100,103,99]
    scale = 5000/quality if quality < 50 else 200-2*quality
    quant = [max(1, min(255, int((q*scale+50)//100))) for q in base_quant]
    cos = [[math.cos((2*x+1)*u*math.pi/16)*(1/math.sqrt(2) if u == 0 else 1)/2
            for x in range(8)] for u in range(8)]
    ac_symbols = [0, 240] + [r*16+s for r in range(16) for s in range(1, 11)]
    ac_codes = {symbol: i for i, symbol in enumerate(ac_symbols)}
    entropy = bytearray()
    accumulator = count = 0

    def bits(value, length):
        nonlocal accumulator, count
        accumulator = (accumulator << length) | value
        count += length
        while count >= 8:
            count -= 8
            byte = (accumulator >> count) & 255
            entropy.append(byte)
            if byte == 255:
                entropy.append(0)
        accumulator &= (1 << count)-1

    def magnitude(value):
        size = abs(value).bit_length()
        return size, value if value >= 0 else (1 << size)-1+value

    def coefficients(values):
        rows = [[sum(values[y*8+x]*cos[u][x] for x in range(8)) for u in range(8)]
                for y in range(8)]
        return [round(sum(rows[y][u]*cos[v][y] for y in range(8))/quant[v*8+u])
                for v in range(8) for u in range(8)]

    previous = [0, 0, 0]

    def block(values, channel):
        coeff = coefficients(values)
        delta = coeff[0]-previous[channel]
        previous[channel] = coeff[0]
        size, value = magnitude(delta)
        if size > 11:
            raise ValueError('DC category exceeds baseline JPEG')
        bits(size, 4)
        bits(value, size)
        zeros = 0
        for index in zigzag[1:]:
            value = coeff[index]
            if not value:
                zeros += 1
                continue
            while zeros >= 16:
                bits(ac_codes[240], 8)
                zeros -= 16
            size, encoded = magnitude(value)
            if size > 10:
                raise ValueError('AC category exceeds baseline JPEG')
            bits(ac_codes[zeros*16+size], 8)
            bits(encoded, size)
            zeros = 0
        if zeros:
            bits(ac_codes[0], 8)

    for my in range(0, h, 16):
        for mx in range(0, w, 16):
            ys, cbs, crs = [], [], []
            for dy in range(16):
                for dx in range(16):
                    p = ((my+dy)*w+mx+dx)*3
                    r, g, b = pixels[p:p+3]
                    ys.append(.299*r+.587*g+.114*b-128)
                    cbs.append(-.168736*r-.331264*g+.5*b)
                    crs.append(.5*r-.418688*g-.081312*b)
            for by, bx in ((0, 0), (0, 8), (8, 0), (8, 8)):
                block([ys[(by+y)*16+bx+x] for y in range(8) for x in range(8)], 0)
            for channel, values in ((1, cbs), (2, crs)):
                block([sum(values[(y*2+dy)*16+x*2+dx] for dy in range(2) for dx in range(2))/4
                       for y in range(8) for x in range(8)], channel)
    if count:
        bits((1 << (8-count))-1, 8-count)

    def segment(marker, body):
        return bytes([255, marker]) + struct.pack('>H', len(body)+2) + body
    dc_counts = bytes([0,0,0,12]+[0]*12)
    ac_counts = bytes([0]*7+[162]+[0]*8)
    return (b'\xff\xd8' + segment(224, b'JFIF\0\x01\x01\0\0\x01\0\x01\0\0') +
            segment(219, b'\0'+bytes(quant[i] for i in zigzag)) +
            segment(192, struct.pack('>BHHB', 8, h, w, 3)+b'\x01\x22\0\x02\x11\0\x03\x11\0') +
            segment(196, b'\0'+dc_counts+bytes(range(12))+b'\x10'+ac_counts+bytes(ac_symbols)) +
            segment(218, b'\x03\x01\0\x02\0\x03\0\0\x3f\0') + entropy + b'\xff\xd9')
