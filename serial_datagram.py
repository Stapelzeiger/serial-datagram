import struct
from zlib import crc32
import sys
import os

class SerialDatagram:

    END = b'\xC0'
    ESC = b'\xDB'
    ESC_END = b'\xDC'
    ESC_ESC = b'\xDD'

    class DecodeError(Exception):
        pass

    @staticmethod
    def crc32(data):
        return struct.pack('>I', crc32(data) & 0xffffffff)

    @classmethod
    def decode(cls, buf):

        buf = buf.replace(cls.ESC + cls.ESC_END,  # replace order matters !
                          cls.END)
        buf = buf.replace(cls.ESC + cls.ESC_ESC,
                          cls.ESC)
        frame = b''+buf[:-4]
        if len(buf) < 4:
            raise cls.DecodeError('frame error')
        elif SerialDatagram.crc32(frame) != buf[-4:]:
            raise cls.DecodeError('crc error')
        else:
            return frame

    @classmethod
    def encode(cls, dtgrm):
        crc = SerialDatagram.crc32(dtgrm)
        frame = dtgrm + crc
        frame = frame.replace(cls.ESC,  # replace order matters !
                              cls.ESC + cls.ESC_ESC)
        frame = frame.replace(cls.END,
                              cls.ESC + cls.ESC_END)
        return frame + cls.END

    def __init__(self, file_desc):
        self.file_desc = file_desc

    def send(self, dtgrm):
        self.file_desc.write(SerialDatagram.encode(dtgrm))

    def receive(self):
        def getframe(fdesc):
            buf = b''
            while True:
                b = fdesc.read(1)
                if b == SerialDatagram.END:
                    break
                buf += b
            return buf
        while True:
            try:
                yield SerialDatagram.decode(getframe(self.file_desc))
            except SerialDatagram.DecodeError as e:
                print(e)


if __name__ == "__main__":
    import argparse

    def w(fdesc):
        for line in sys.stdin.readlines():
            SerialDatagram(fdesc).send(line.encode('ascii', 'ignore')+b'\0')
            fdesc.flush()

    def r(fdesc):
        for dtgrm in SerialDatagram(fdesc).receive():
            print(dtgrm)

    if len(sys.argv) > 1:
        if sys.argv[1] == 'r':
            fd = os.fdopen(sys.stdin.fileno(), "rb")
            r(fd)
        if sys.argv[1] == 'rs':
            import serial
            if len(sys.argv) > 3:
                baud = sys.argv[3]
            else:
                baud = 115200
            fd = serial.Serial(sys.argv[2], baudrate=baud)
            r(fd)
        if sys.argv[1] == 'w':
            fd = os.fdopen(sys.stdout.fileno(), "wb")
            w(fd)
        if sys.argv[1] == 'ws':
            import serial
            if len(sys.argv) > 3:
                baud = sys.argv[3]
            else:
                baud = 115200
            fd = serial.Serial(sys.argv[2], baudrate=baud)
            r(fd)
    else:
        print("usage: {} r # to read".format(sys.argv[0]))
        print("usage: {} w # to write".format(sys.argv[0]))
