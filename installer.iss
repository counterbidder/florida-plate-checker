; Inno Setup script - run via build.bat or open in the Inno Setup compiler.
#define MyAppName "Florida Plate Checker"
#define MyAppVersion "1.0.0"
#define MyAppExe "FloridaPlateChecker.exe"

[Setup]
AppId={{E3A9FC4A-9204-4551-A15F-637F07C9BABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\FloridaPlateChecker
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=FloridaPlateChecker-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExe}
SetupIconFile=app.ico

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; Flags: unchecked

[Files]
Source: "dist\FloridaPlateChecker\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
