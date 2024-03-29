import ctypes
import fcntl
import logging
import os

from v4l2_io import _IOW, _IOWR

_log = logging.getLogger("dma_heap")
heapNames = [
    "/dev/dma_heap/reserved",
    "/dev/dma_heap/linux,cma",
    "/dev/dma_heap/vidbuf_cached"
]


# Kernel stuff from linux/dma-buf.h
class dma_buf_sync(ctypes.Structure):
    _fields_ = [
        ('flags', ctypes.c_uint64),
    ]


DMA_BUF_SYNC_READ = (1 << 0)
DMA_BUF_SYNC_WRITE = (2 << 0)
DMA_BUF_SYNC_RW = (DMA_BUF_SYNC_READ | DMA_BUF_SYNC_WRITE)
DMA_BUF_SYNC_START = (0 << 2)
DMA_BUF_SYNC_END = (1 << 2)

DMA_BUF_BASE = 'b'
DMA_BUF_IOCTL_SYNC = _IOW(DMA_BUF_BASE, 0, dma_buf_sync)

DMA_BUF_SET_NAME = _IOW(DMA_BUF_BASE, 1, ctypes.c_char_p)


class dma_buf_export_sync_file(ctypes.Structure):
    _fields_ = [
        ('flags', ctypes.c_uint32),
        ('fd', ctypes.c_int32),
    ]


class dma_buf_import_sync_file(ctypes.Structure):
    _fields_ = [
        ('flags', ctypes.c_uint32),
        ('fd', ctypes.c_int32),
    ]


DMA_BUF_IOCTL_EXPORT_SYNC_FILE = _IOWR(DMA_BUF_BASE, 2, dma_buf_export_sync_file)
DMA_BUF_IOCTL_IMPORT_SYNC_FILE = _IOW(DMA_BUF_BASE, 3, dma_buf_import_sync_file)


# Kernel stuff from linux/dma-heap.h
class dma_heap_allocation_data(ctypes.Structure):
    _fields_ = [
        ('len', ctypes.c_uint64),
        ('fd', ctypes.c_uint32),
        ('fd_flags', ctypes.c_uint32),
        ('heap_flags', ctypes.c_uint64)
    ]


DMA_HEAP_IOC_MAGIC = 'H'

DMA_HEAP_IOCTL_ALLOC = _IOWR(DMA_HEAP_IOC_MAGIC, 0, dma_heap_allocation_data)


# Libcamera C++ classes
class UniqueFD:
    """Libcamera UniqueFD Class"""

    def __init__(self, fd=-1):
        print("init UniqueFD", fd)
        if isinstance(fd, UniqueFD):
            self.__fd = fd.release()
        else:
            self.__fd = fd

    def release(self):
        fd = self.__fd
        self.__fd = -1
        return fd

    def get(self):
        return self.__fd

    def isValid(self):
        return self.__fd >= 0


class DmaHeap:
    """DmaHeap"""

    def __init__(self):
        self.__dmaHeapHandle = UniqueFD()
        for name in heapNames:
            try:
                print(f"Opening {name} | {os.O_CLOEXEC | os.O_RDWR}")
                self.dmaHeap_fd = os.open(name, os.O_CLOEXEC | os.O_RDWR)
                print(f"ret {self.dmaHeap_fd}")
                print(f"type(ret) {type(self.dmaHeap_fd)}")
            except FileNotFoundError:
                _log.info(f"Failed to open {name}")
                continue

            self.__dmaHeapHandle = UniqueFD(self.dmaHeap_fd)
            break

        if not self.__dmaHeapHandle.isValid():
            raise RuntimeError("Could not open any dmaHeap device")

    @property
    def isValid(self):
        return self.__dmaHeapHandle.isValid()

    def alloc(self, name, size) -> UniqueFD:
        alloc = dma_heap_allocation_data()
        alloc.len = size
        alloc.fd_flags = os.O_CLOEXEC | os.O_RDWR
        ret = fcntl.ioctl(self.__dmaHeapHandle.get(), DMA_HEAP_IOCTL_ALLOC, alloc)
        if ret < 0:
            _log.error(f"dmaHeap allocation failure for {name}")
            return UniqueFD()

        allocFd = UniqueFD(alloc.fd)
        print(f"alloc.fd {alloc.fd}")
        print(f"allocFd.get() {allocFd.get()}")

        ret = fcntl.ioctl(allocFd.get(), DMA_BUF_SET_NAME, name)
        if not isinstance(ret, bytes) and ret < 0:
            _log.error(f"dmaHeap naming failure for {name}")
            return UniqueFD()

        sync_file = dma_buf_export_sync_file()
        sync_file.flags = DMA_BUF_SYNC_READ | DMA_BUF_SYNC_WRITE
        ret = fcntl.ioctl(allocFd.get(), DMA_BUF_IOCTL_EXPORT_SYNC_FILE, sync_file)
        if not isinstance(ret, bytes) and ret < 0:
            _log.error(f"dmaHeap export sync file failure for {name}")
            return UniqueFD()

        print("sync_file fd", sync_file.fd)

        return allocFd

    def connect(self, fd) -> UniqueFD:
        sync_file = dma_buf_import_sync_file()
        sync_file.flags = DMA_BUF_SYNC_READ | DMA_BUF_SYNC_WRITE
        sync_file.fd = fd
        ret = fcntl.ioctl(self.__dmaHeapHandle.get(), DMA_BUF_IOCTL_IMPORT_SYNC_FILE, sync_file)
        if not isinstance(ret, bytes) and ret < 0:
            _log.error(f"dmaHeap export sync file failure")
            return UniqueFD()
        print("ret", ret)
        return ret
