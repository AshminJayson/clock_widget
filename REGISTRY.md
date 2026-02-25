# Windows Registry Changes

## What the "Start with Windows" toggle does

When enabled via the right-click menu, the app writes a single registry value:

- **Key**: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- **Value name**: `ClockWidget`
- **Value data**: `"<path_to_pythonw.exe>" "<path_to_main.py>"`
- **Type**: `REG_SZ` (string)

This is the standard Windows mechanism for auto-starting apps at user login. It only affects the current user (`HKCU`), not system-wide. No admin rights required.

## How to undo

### Option 1: From the app
Right-click the clock widget and uncheck "Start with Windows". The registry value is deleted immediately.

### Option 2: From Task Manager
1. Open Task Manager (`Ctrl+Shift+Esc`)
2. Go to the **Startup** tab
3. Find **ClockWidget**, right-click, and select **Disable**

### Option 3: From the registry directly
1. Press `Win+R`, type `regedit`, press Enter
2. Navigate to `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
3. Find the `ClockWidget` entry on the right side
4. Right-click it and select **Delete**

### Option 4: From the command line
```cmd
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v ClockWidget /f
```

## Verifying current state

Check if the entry exists:
```cmd
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v ClockWidget
```

If the entry exists, you'll see the value data. If not, you'll see an error message.
