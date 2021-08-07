#!/usr/bin/env python3

import sys
import struct


class ext4_file_header:
    def __init__(self, buf):
        self.magic, \
            self.major, \
            self.minor, \
            self.file_header_size, \
            self.chunk_header_size, \
            self.block_size, \
            self.total_blocks, \
            self.total_chunks, \
            self.crc32, \
            = struct.unpack("<IHHHHIIII", buf)


class ext4_chunk_header:
    def __init__(self, buf):
        self.type,\
            self.reserved,\
            self.chunk_size,\
            self.total_size,\
            = struct.unpack("<HHII", buf)


if len(sys.argv) == 3:
    file_in = sys.argv[1]
    file_out = sys.argv[2]
else:
    print("Usage: simg2img.py <in> <out>")
    sys.exit(1)
ifd = open(file_in, "rb")

ifd.seek(0, 2)
file_len = ifd.tell()
print(file_len)
ifd.seek(0, 0)

buf = ifd.read(28)
file_header = ext4_file_header(buf)

EXT4_FILE_HEADER_MAGIC = 0xED26FF3A
EXT4_CHUNK_HEADER_SIZE = 12

if file_header.magic != EXT4_FILE_HEADER_MAGIC:
    print("Not a compressed ext4 fileecho")
    sys.exit(1)

total_chunks = file_header.total_chunks
print(f"total chunk = {total_chunks}")

ofd = open(file_out, "wb")

sector_base = 82528
output_len = 0

while total_chunks > 0:
    buf = ifd.read(EXT4_CHUNK_HEADER_SIZE)
    chunk_header = ext4_chunk_header(buf)
    sector_size = (chunk_header.chunk_size * file_header.block_size) >> 9

    if chunk_header.type == 0xCAC1:  # raw type
        data = ifd.read(chunk_header.total_size - EXT4_CHUNK_HEADER_SIZE)
        print(f"len data:{len(data)}, sector_size:{sector_size << 9}")
        if len(data) != (sector_size << 9):
            sys.exit(1)
        else:
            ofd.write(data)
            output_len += len(data)
            print(f"write raw data in {sector_base} size {sector_size} n")
            print(f"output len:{output_len}")

            sector_base += sector_size
    else:
        if chunk_header.type == 0xCAC2:  # fill type
            data = b"\0" * (sector_size << 9)
            ofd.write(data)
            output_len += len(data)
            print(f"chunk_size:{chunk_header.chunk_size}")
            print(f"output len:{output_len}")
            sector_base += sector_size
        else:
            if chunk_header.type == 0xCAC3:  # don't care type
                data = b"\0" * (sector_size << 9)
                ofd.write(data)
                output_len += len(data)
                sector_base += sector_size
            else:
                data = b"\0" * (sector_size << 9)
                ofd.write(data)
                sector_base += sector_size

    total_chunks -= 1
    print(f"remaining chunks = {total_chunks}")

print("done")

ifd.close()
ofd.close()
