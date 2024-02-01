#ifndef ALLOCATOR_HEADER
#include "allocator.h"
#endif

#include <sys/syscall.h>
#include <unistd.h>

int borrow_fd_from_pid(int pid, int fd){
  int pid_fd = syscall(SYS_pidfd_open, pid, 0); // PIDFD_NONBLOCK
  return syscall(SYS_pidfd_getfd, pid_fd, fd, 0); // PTRACE_MODE_ATTACH_REALCREDS
}
