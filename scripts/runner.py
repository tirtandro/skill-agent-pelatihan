import ctypes
from ctypes import wintypes
import json
import subprocess
import os

class AgentDesktopRunner:
    def __init__(self, exe_path=None):
        if exe_path:
            self.exe = exe_path
        else:
            default_path = r'C:\Users\Admin\AppData\Roaming\npm\node_modules\agent-desktop\bin\agent-desktop-win32-x64.exe'
            if os.path.exists(default_path):
                self.exe = default_path
            else:
                self.exe = 'agent-desktop-win32-x64.exe'
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

    def run(self, args_list, timeout=15):
        # Ensure thread desktop is Default
        h_default = self.user32.OpenDesktopW('Default', 0, False, 0x1FF)
        if h_default:
            self.user32.SetThreadDesktop(h_default)

        # Setup STARTUPINFO
        class STARTUPINFO(ctypes.Structure):
            _fields_ = [
                ('cb', wintypes.DWORD),
                ('lpReserved', wintypes.LPWSTR),
                ('lpDesktop', wintypes.LPWSTR),
                ('lpTitle', wintypes.LPWSTR),
                ('dwX', wintypes.DWORD),
                ('dwY', wintypes.DWORD),
                ('dwXSize', wintypes.DWORD),
                ('dwYSize', wintypes.DWORD),
                ('dwXCountChars', wintypes.DWORD),
                ('dwYCountChars', wintypes.DWORD),
                ('dwFillAttribute', wintypes.DWORD),
                ('dwFlags', wintypes.DWORD),
                ('wShowWindow', wintypes.WORD),
                ('cbReserved2', wintypes.WORD),
                ('lpReserved2', ctypes.c_char_p),
                ('hStdInput', wintypes.HANDLE),
                ('hStdOutput', wintypes.HANDLE),
                ('hStdError', wintypes.HANDLE),
            ]

        class PROCESS_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('hProcess', wintypes.HANDLE),
                ('hThread', wintypes.HANDLE),
                ('dwProcessId', wintypes.DWORD),
                ('dwThreadId', wintypes.DWORD),
            ]

        class SECURITY_ATTRIBUTES(ctypes.Structure):
            _fields_ = [
                ('nLength', wintypes.DWORD),
                ('lpSecurityDescriptor', ctypes.c_void_p),
                ('bInheritHandle', wintypes.BOOL)
            ]

        sa = SECURITY_ATTRIBUTES()
        sa.nLength = ctypes.sizeof(SECURITY_ATTRIBUTES)
        sa.bInheritHandle = True
        sa.lpSecurityDescriptor = None

        h_read_pipe = wintypes.HANDLE()
        h_write_pipe = wintypes.HANDLE()
        self.kernel32.CreatePipe(ctypes.byref(h_read_pipe), ctypes.byref(h_write_pipe), ctypes.byref(sa), 0)
        self.kernel32.SetHandleInformation(h_read_pipe, 1, 0) # Non-inheritable

        si = STARTUPINFO()
        si.cb = ctypes.sizeof(STARTUPINFO)
        si.lpDesktop = 'WinSta0\\Default'
        si.dwFlags = 0x00000100 # STARTF_USESTDHANDLES
        si.hStdOutput = h_write_pipe
        si.hStdError = h_write_pipe
        si.hStdInput = None

        pi = PROCESS_INFORMATION()

        cmd_str = f'"{self.exe}" ' + ' '.join(args_list)
        res = self.kernel32.CreateProcessW(None, cmd_str, None, None, True, 0, None, None, ctypes.byref(si), ctypes.byref(pi))
        self.kernel32.CloseHandle(h_write_pipe)

        if not res:
            err = ctypes.GetLastError()
            self.kernel32.CloseHandle(h_read_pipe)
            raise RuntimeError(f"CreateProcessW failed with Win32 error {err}")

        # Read output safely without blocking
        import time
        output_chunks = []
        buf = ctypes.create_string_buffer(4096)
        bytes_read = wintypes.DWORD()
        total_avail = wintypes.DWORD()
        
        start_time = time.time()
        while True:
            peek_ok = self.kernel32.PeekNamedPipe(h_read_pipe, None, 0, None, ctypes.byref(total_avail), None)
            if not peek_ok:
                break
            if total_avail.value > 0:
                to_read = min(4096, total_avail.value)
                success = self.kernel32.ReadFile(h_read_pipe, buf, to_read, ctypes.byref(bytes_read), None)
                if success and bytes_read.value > 0:
                    output_chunks.append(buf.raw[:bytes_read.value])
                else:
                    break
            else:
                wait_res = self.kernel32.WaitForSingleObject(pi.hProcess, 50)
                if wait_res == 0: # Process finished
                    # Drain any remaining bytes
                    if self.kernel32.PeekNamedPipe(h_read_pipe, None, 0, None, ctypes.byref(total_avail), None) and total_avail.value > 0:
                        to_read = min(4096, total_avail.value)
                        if self.kernel32.ReadFile(h_read_pipe, buf, to_read, ctypes.byref(bytes_read), None) and bytes_read.value > 0:
                            output_chunks.append(buf.raw[:bytes_read.value])
                    break
                if time.time() - start_time > timeout:
                    self.kernel32.TerminateProcess(pi.hProcess, 1)
                    break

        self.kernel32.CloseHandle(h_read_pipe)
        self.kernel32.CloseHandle(pi.hProcess)
        self.kernel32.CloseHandle(pi.hThread)

        raw_output = b''.join(output_chunks).decode('utf-8', errors='replace')
        try:
            return json.loads(raw_output)
        except Exception:
            return {"raw": raw_output}

_default_runner = AgentDesktopRunner()

def run(args_list, timeout=15):
    return _default_runner.run(args_list, timeout=timeout)

if __name__ == '__main__':
    import sys
    runner = AgentDesktopRunner()
    args = sys.argv[1:]
    if not args:
        args = ['list-windows']
    res = runner.run(args)
    if isinstance(res, dict) and "raw" in res and len(res) == 1:
        print(res["raw"])
    else:
        print(json.dumps(res, indent=2))
