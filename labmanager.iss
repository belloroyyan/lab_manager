; Lab Manager Installer Script
; ============================

#define MyAppName "Lab Manager"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Bello Royyan A. - UNIOSUN"
#define MyAppExeName "LabManager.exe"
#define MyAppURL "https://github.com/belloroyyan/lab_manager"

[Setup]
AppId={{8F3A9C2E-1B7D-4E5A-9F2C-6D8E0A1B3C4D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={localappdata}\LabManager
DefaultGroupName=Lab Manager
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=LabManager_Setup_v{#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Files]
Source: "LabManager.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\lab_icon.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\lab_icon.ico"; Tasks: desktopicon

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

; Optional: include other files if needed
; Source: "settings.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Dirs]
; Create the user-visible folder on Desktop
Name: "{userdesktop}\Lab Manager"
Name: "{userdesktop}\Lab Manager\reports"
Name: "{userdesktop}\Lab Manager\venvs"
Name: "{userdesktop}\Lab Manager\git_repos"
Name: "{userdesktop}\Lab Manager\backups"

; Create AppData folders
Name: "{userappdata}\LabManager"
Name: "{userappdata}\LabManager\logs"
Name: "{userappdata}\LabManager\temp"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Lab Manager"; Flags: nowait postinstall skipifsilent