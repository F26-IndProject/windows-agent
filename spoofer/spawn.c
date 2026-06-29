/*
 * spawn.c - Launches a browser with a spoofed parent (explorer.exe) and waits.
 * 
 * This version stays alive to maintain the correct parent-child relationship.
 * 
 * Compile: gcc -o spawn.exe spawn.c -luser32
 *
 * Usage: spawn.exe <full_path_to_browser> <url>
 * Example: .\spawn.exe "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "https://google.com"
 */

#include <windows.h>
#include <stdio.h>

int main(int argc, char* argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <browser_path> <url>\n", argv[0]);
        return 1;
    }

    const char* browserPath = argv[1];
    const char* url = argv[2];
    char fullCmdLine[1024];

    snprintf(fullCmdLine, sizeof(fullCmdLine), "\"%s\" \"%s\"", browserPath, url);

    // 1. Find the target parent process (explorer.exe)
    HWND hwnd = GetShellWindow();
    DWORD parentPid;
    GetWindowThreadProcessId(hwnd, &parentPid);
    HANDLE hParentProcess = OpenProcess(PROCESS_CREATE_PROCESS, FALSE, parentPid);
    if (!hParentProcess) {
        fprintf(stderr, "OpenProcess failed for PID %lu (Error: %lu). Run as Admin?\n", parentPid, GetLastError());
        return 1;
    }

    // 2. Prepare the attribute list for parent spoofing
    SIZE_T attrListSize = 0;
    InitializeProcThreadAttributeList(NULL, 1, 0, &attrListSize);
    PPROC_THREAD_ATTRIBUTE_LIST pAttrList = (PPROC_THREAD_ATTRIBUTE_LIST)HeapAlloc(GetProcessHeap(), 0, attrListSize);
    if (!pAttrList) {
        fprintf(stderr, "HeapAlloc failed.\n");
        CloseHandle(hParentProcess);
        return 1;
    }
    if (!InitializeProcThreadAttributeList(pAttrList, 1, 0, &attrListSize)) {
        fprintf(stderr, "InitializeProcThreadAttributeList failed.\n");
        HeapFree(GetProcessHeap(), 0, pAttrList);
        CloseHandle(hParentProcess);
        return 1;
    }

    if (!UpdateProcThreadAttribute(pAttrList, 0, PROC_THREAD_ATTRIBUTE_PARENT_PROCESS,
                                   &hParentProcess, sizeof(HANDLE), NULL, NULL)) {
        fprintf(stderr, "UpdateProcThreadAttribute failed.\n");
        DeleteProcThreadAttributeList(pAttrList);
        HeapFree(GetProcessHeap(), 0, pAttrList);
        CloseHandle(hParentProcess);
        return 1;
    }

    // 3. Create the spoofed child process
    STARTUPINFOEXA si = {0};
    si.StartupInfo.cb = sizeof(STARTUPINFOEXA);
    si.lpAttributeList = pAttrList;

    PROCESS_INFORMATION pi = {0};

    BOOL success = CreateProcessA(
        browserPath,       // Application name
        fullCmdLine,       // Command line
        NULL, NULL,        // Security attributes
        FALSE,             // Handle inheritance
        CREATE_NEW_CONSOLE | EXTENDED_STARTUPINFO_PRESENT,
        NULL,              // Environment
        NULL,              // Working directory
        &si.StartupInfo,   // Pointer to STARTUPINFOEXA's STARTUPINFO part
        &pi
    );

    if (success) {
        printf("Successfully spawned %s (PID: %lu)\n", browserPath, pi.dwProcessId);
        printf("Waiting for the browser to close...\n");
        // 4. Wait for the browser process to finish before exiting
        WaitForSingleObject(pi.hProcess, INFINITE);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        printf("Browser closed. Exiting.\n");
    } else {
        fprintf(stderr, "CreateProcessA failed. Error: %lu\n", GetLastError());
    }

    // 5. Clean up
    DeleteProcThreadAttributeList(pAttrList);
    HeapFree(GetProcessHeap(), 0, pAttrList);
    CloseHandle(hParentProcess);

    return success ? 0 : 1;
}