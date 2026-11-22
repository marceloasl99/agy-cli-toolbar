Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\ma038\.antigravity-custom"
WshShell.Run """C:\Python314\pythonw.exe"" ""C:\Users\ma038\.antigravity-custom\tray_app.pyw""", 0, False
