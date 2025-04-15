# -*- coding: utf-8 -*-
import subprocess
import time
import win32pipe
import win32file
import pywintypes
from typing import Iterable


class Printer:
    '''A printer that opens in a separate black window. It handles typing in a subprocess and blocks the current process. Only available on Windows.'''

    def __init__(self, path, encoding='utf-8'):
        '''Initialization doesn't use resources. Resources are only allocated when open or __enter__ is called.'''
        self.path = path
        self._pipe = None
        self._subprocess = None
        self.encoding = encoding

    def write(self, text: str):
        '''Type in the subprocess without newline character'''
        b = bytes(text, encoding=self.encoding)
        le = len(b)
        length = le.to_bytes(2, byteorder='little')
        win32file.WriteFile(self._pipe, b'$msg ' + length + b)

    def writeline(self, text: str | Iterable[str]):
        '''Type in the subprocess with newline character'''
        if isinstance(text, str):
            self.write(text + '\n')
        elif isinstance(text, Iterable):
            for s in text:
                self.write(s + '\n')

    def waitkey(self):
        '''Block the current process until Enter is pressed in the subprocess'''
        win32file.WriteFile(self._pipe, b'$wait')
        win32file.ReadFile(self._pipe, 65536, None)

    def clear(self):
        '''Clear the screen'''
        win32file.WriteFile(self._pipe, b'$clr ')

    def __enter__(self):
        self._subprocess = subprocess.Popen(
            f'start python ./meowdock/library/utils/_printer_win.py {self.path} {self.encoding}',
            shell=True,
        )

        for _ in range(10):
            try:
                win32pipe.WaitNamedPipe(fr'\\.\pipe\{self.path}', 1000)
                break
            except pywintypes.error:
                time.sleep(1)

        self._pipe = win32file.CreateFile(
            fr'\\.\pipe\{self.path}',
            win32file.GENERIC_WRITE | win32file.GENERIC_READ,
            0,  # no sharing
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._pipe:
            win32file.CloseHandle(self._pipe)
        if self._subprocess:
            self._subprocess.terminate()
            self._subprocess.wait()
            self._subprocess.kill()

    def open(self):
        '''Uses resources, needs manual close'''
        return self.__enter__()

    def close(self):
        '''Manually release resources'''
        self.__exit__(None, None, None)


if __name__ == '__main__':
    from itertools import batched

    with Printer(r"test_pipe") as printer:
        printer.write("Hello,")
        time.sleep(1.0)
        printer.write(" world!\n")
        printer.waitkey()
        for s in ["test", "test", "test\n"]:
            printer.write(s)
            time.sleep(0.4)
        time.sleep(1.0)
        printer.clear()
        for s in batched(batched.__doc__, 5):
            s = ''.join(s)
            printer.write(s)
        printer.write("Goodbye!\n")
