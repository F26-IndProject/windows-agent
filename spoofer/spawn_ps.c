/*
 * spawn_ps.c — Launches a process hidden with spoofed parent (explorer.exe).
 *              Finds explorer.exe by name, not GetShellWindow().
 *
 * Compile: gcc -o spawn_ps.exe spawn_ps.c -luser32
 *
 * Usage: spawn_ps.exe <exe_path> <args>
 * Example: spawn_ps.exe "C:\Windows\...\powershell.exe" "-NonInteractive -Command \"Get-Date\""
 */
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>

static DWORD find_explorer_pid() {
    DWORD pid = 0;
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) return 0;
    PROCESSENTRY32 pe = {0};
    pe.dwSize = sizeof(PROCESSENTRY32);
    if (Process32First(snap, &pe)) {
        do {
            if (_stricmp(pe.szExeFile, "explorer.exe") == 0) {
                pid = pe.th32ProcessID;
                break;
            }
        } while (Process32Next(snap, &pe));
    }
    CloseHandle(snap);
    return pid;
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <exe_path> <args>\n", argv[0]);
        return 1;
    }

    const char* exePath = argv[1];
    const char* args    = argv[2];

    char fullCmdLine[4096];
    snprintf(fullCmdLine, sizeof(fullCmdLine), "\"%s\" %s", exePath, args);

    // 1. Find explorer.exe by name
    DWORD parentPid = find_explorer_pid();
    if (!parentPid) {
        fprintf(stderr, "Could not find explorer.exe\n");
        return 1;
    }

    HANDLE hParentProcess = OpenProcess(PROCESS_CREATE_PROCESS, FALSE, parentPid);
    if (!hParentProcess) {
        fprintf(stderr, "OpenProcess failed (Error: %lu)\n", GetLastError());
        return 1;
    }

    // 2. Prepare attribute list for parent spoofing
    SIZE_T attrListSize = 0;
    InitializeProcThreadAttributeList(NULL, 1, 0, &attrListSize);
    PPROC_THREAD_ATTRIBUTE_LIST pAttrList =
        (PPROC_THREAD_ATTRIBUTE_LIST)HeapAlloc(GetProcessHeap(), 0, attrListSize);
    if (!pAttrList) { CloseHandle(hParentProcess); return 1; }
    InitializeProcThreadAttributeList(pAttrList, 1, 0, &attrListSize);
    UpdateProcThreadAttribute(pAttrList, 0, PROC_THREAD_ATTRIBUTE_PARENT_PROCESS,
                              &hParentProcess, sizeof(HANDLE), NULL, NULL);

    // 3. Launch hidden — no console window
    STARTUPINFOEXA si = {0};
    si.StartupInfo.cb          = sizeof(STARTUPINFOEXA);
    si.StartupInfo.dwFlags     = STARTF_USESHOWWINDOW;
    si.StartupInfo.wShowWindow = SW_HIDE;
    si.lpAttributeList         = pAttrList;

    PROCESS_INFORMATION pi = {0};
    BOOL success = CreateProcessA(
        exePath, fullCmdLine,
        NULL, NULL, FALSE,
        CREATE_NO_WINDOW | EXTENDED_STARTUPINFO_PRESENT,
        NULL, NULL,
        &si.StartupInfo, &pi
    );

    if (success) {
        WaitForSingleObject(pi.hProcess, INFINITE);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        fprintf(stderr, "CreateProcessA failed (Error: %lu)\n", GetLastError());
    }

    DeleteProcThreadAttributeList(pAttrList);
    HeapFree(GetProcessHeap(), 0, pAttrList);
    CloseHandle(hParentProcess);
    return success ? 0 : 1;
}