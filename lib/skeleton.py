#
#       PEDA - Python Exploit Development Assistance for GDB
#
#       Copyright (C) 2012 Long Le Dinh <longld at vnsecurity.net>
#
#       License: see LICENSE file for details
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

class ExploitSkeleton(object):
    """
    Wrapper for exploit skeleton codes
    """
    def __init__(self):
        self.skeleton_basic = """
#!/usr/bin/env python
#
# Template for #TYPE# exploit code, generated by PEDA
#
import os
import sys
import struct
import resource
import time

def usage():
    print "Usage: %s #USAGE#" % sys.argv[0]
    return

def pattern(size=1024, start=0):
    try:
        bytes = open("pattern.txt").read(size+start)
        return bytes[start:]
    except:
        return "A"*size

def nops(size=1024):
    return "\\x90"*size

def int2hexstr(num, intsize=4):
    if intsize == 8:
        if num < 0:
            result = struct.pack("<q", num)
        else:
            result = struct.pack("<Q", num)
    else:
        if num < 0:
            result = struct.pack("<l", num)
        else:
            result = struct.pack("<L", num)
    return result

i2hs = int2hexstr

def list2hexstr(intlist, intsize=4):
    result = ""
    for value in intlist:
        if isinstance(value, str):
            result += value
        else:
            result += int2hexstr(value, intsize)
    return result

l2hs = list2hexstr
"""

        self.skeleton_local_argv = self.skeleton_basic
        self.skeleton_local_argv = self.skeleton_local_argv.replace("#TYPE#", "local argv")
        self.skeleton_local_argv = self.skeleton_local_argv.replace("#USAGE#", "target_program")
        self.skeleton_local_argv += """
def exploit(vuln):
    padding = pattern(0)
    payload = [padding]
    payload += ["PAYLOAD"] # put your payload here
    payload = list2hexstr(payload)
    args = [vuln, payload]
    env = {"PEDA":nops()}
    resource.setrlimit(resource.RLIMIT_STACK, (-1, -1))
    resource.setrlimit(resource.RLIMIT_CORE, (-1, -1))
    os.execve(vuln, args, env)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
    else:
        exploit(sys.argv[1])
    """

        self.skeleton_local_env = self.skeleton_basic
        self.skeleton_local_env = self.skeleton_local_env.replace("#TYPE#", "local env")
        self.skeleton_local_env = self.skeleton_local_env.replace("#USAGE#", "target_program")
        self.skeleton_local_env += """
from ctypes import *
from ctypes.util import find_library

def exploit(vuln):
    libc = cdll.LoadLibrary(find_library("c"))
    execve = libc.execve
    padding = pattern(0)
    payload = [padding]
    payload += ["PAYLOAD"] # put your payload here
    payload = list2hexstr(payload)
    args = sys.argv[1:] + [None]
    # create custom env with NULL value
    env = [
        "EGG",
        "A","","", # 0x00000041
        "B"*2,"", # 0x00004242
        "C"*3, # 0x00434343
        "D"*4, # 0x44444444
        payload,
        "X", # padding
        None ]
    l = len(env)
    envp = (c_char_p*l)()
    for i in range(l):
        envp[i] = cast(env[i], c_char_p)

    # create custom argv with null: A "" "" BB "" CCC DDDD
    l = len(args)
    argp = (c_char_p*l)()
    for i in range(l):
        argp[i] = cast(args[i], c_char_p)

    resource.setrlimit(resource.RLIMIT_STACK, (-1, -1))
    resource.setrlimit(resource.RLIMIT_CORE, (-1, -1))
    execve(vuln, argp, envp)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
    else:
        exploit(sys.argv[1])
    """

        self.skeleton_local_stdin = self.skeleton_basic
        self.skeleton_local_stdin = self.skeleton_local_stdin.replace("#TYPE#", "local stdin")
        self.skeleton_local_stdin = self.skeleton_local_stdin.replace("#USAGE#", "target_program")
        self.skeleton_local_stdin += """
from subprocess import *
def exploit(vuln):
    padding = pattern(0)
    payload = [padding]
    payload += ["PAYLOAD"] # put your payload here
    payload = list2hexstr(payload)
    env = {"PEDA":nops()}
    args = sys.argv[1:]
    resource.setrlimit(resource.RLIMIT_STACK, (-1, -1))
    resource.setrlimit(resource.RLIMIT_CORE, (-1, -1))
    P = Popen(args, stdin=PIPE)
    P.stdin.write(payload + "\\n")
    while True:
        line = sys.stdin.readline()
        P.poll()
        ret = P.returncode
        if ret == None:
            P.stdin.write(line)
        else:
            if ret == -11:
                print "Child program crashed with SIGSEGV"
            else:
                print "Child program exited with code %d" % ret
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
    else:
        exploit(sys.argv[1])
    """

        self.skeleton_remote_tcp = self.skeleton_basic
        self.skeleton_remote_tcp = self.skeleton_remote_tcp.replace("#TYPE#", "remote TCP")
        self.skeleton_remote_tcp = self.skeleton_remote_tcp.replace("#USAGE#", "host port")
        self.skeleton_remote_tcp += """
from socket import *
import telnetlib
class TCPClient():
    def __init__(self, host, port, debug=0):
        self.debug = debug
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((host, port))

    def debug_log(self, size, data, cmd):
        if self.debug != 0:
            print "%s(%d): %s" % (cmd, size, repr(data))

    def send(self, data, delay=0):
        if delay:
            time.sleep(delay)
        nsend = self.sock.send(data)
        if self.debug > 1:
            self.debug_log(nsend, data, "send")
        return nsend

    def sendline(self, data, delay=0):
        nsend = self.send(data + "\\n", delay)
        return nsend

    def recv(self, size=1024, delay=0):
        if delay:
            time.sleep(delay)
        buf = self.sock.recv(size)
        if self.debug > 0:
            self.debug_log(len(buf), buf, "recv")
        return buf

    def recv_until(self, delim):
        buf = ""
        while True:
            c = self.sock.recv(1)
            buf += c
            if delim in buf:
                break
        self.debug_log(len(buf), buf, "recv")
        return buf

    def recvline(self):
        buf = self.recv_until("\\n")
        return buf

    def close(self):
        self.sock.close()

def exploit(host, port):
    port = int(port)
    client = TCPClient(host, port, debug=1)
    padding = pattern(0)
    payload = [padding]
    payload += ["PAYLOAD"] # put your payload here
    payload = list2hexstr(payload)
    raw_input("Enter to continue")
    client.send(payload)
    try:
        t = telnetlib.Telnet()
        t.sock = client.sock
        t.interact()
        t.close()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage()
    else:
        exploit(sys.argv[1], sys.argv[2])
    """
