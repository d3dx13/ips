import time
from time import sleep
import os
from dma_heap import *
import mmap
import numpy as np
import ctypes
import psutil
import zmq
import array
import os, errno
import socket

dmaHeap = DmaHeap()


def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e:  # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred


frame_size = 1024 * 1024 * 512

fd = dmaHeap.alloc(f"test", frame_size)
memory = mmap.mmap(fd.get(), frame_size, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
arr = np.ndarray(shape=(1024, 1024, 512), dtype=np.uint8, buffer=memory)

print(os.getpid())
print(fd.get())

while True:
    val = int(time.monotonic()) % 256
    rand_arr = np.random.randint(val, val + 1, size=(1024, 1024, 512), dtype=np.uint8)

    t_start = time.monotonic_ns()
    arr[:] = rand_arr[:]
    t_end = time.monotonic_ns()
    freq = np.prod(arr.shape) * arr.dtype.itemsize / (t_end - t_start)

    print()
    print(np.mean(arr))
    print(f" freq = {freq:.6f} Gb pub / sec")
