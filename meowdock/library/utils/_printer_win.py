# -*- coding: utf-8 -*-
import sys, os
import win32file, pywintypes, win32pipe


pipe = None
path = sys.argv[1]
encoding = sys.argv[2]

def msg(b):
    print(str(b, encoding=encoding), end='', flush=True)

def wait():
    input('Press ENTER to continue...')
    win32file.WriteFile(pipe, b'a')

def clear():
    os.system('cls')

try:
    pipe = win32pipe.CreateNamedPipe(
        fr'\\.\pipe\{path}',
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_WAIT,
        1, 65536, 65536,
        0, None)

    win32pipe.ConnectNamedPipe(pipe, None)

    while True:
        result, cmd = win32file.ReadFile(pipe, 5, None)

        if cmd == b'$msg ':
            result, le = win32file.ReadFile(pipe, 2, None)
            length = int.from_bytes(le, byteorder='little')
            result, data = win32file.ReadFile(pipe, length, None)
            msg(data)
        elif cmd == b'$wait':
            wait()
        elif cmd == b'$clr ':
            clear()
        else:
            print("Unknown command:", cmd)

finally:
    if pipe:
        win32pipe.DisconnectNamedPipe(pipe)
        win32file.CloseHandle(pipe)
    input('Press ENTER to EXIT...')
