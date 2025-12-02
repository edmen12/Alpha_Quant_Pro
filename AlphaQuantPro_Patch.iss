#define MyAppName "Alpha Quant Pro (Patch)"
#define MyAppVersion "1.3.4"
#define MyAppPublisher "Alpha Quant"
#define MyAppURL "https://github.com/edmen12/Alpha_Quant_Pro"
#define MyAppExeName "AlphaQuantPro.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Alpha Quant Pro
DisableProgramGroupPage=yes
; Industry Standard: Install to Program Files (requires admin)
PrivilegesRequired=admin
OutputDir=Installer
OutputBaseFilename=AlphaQuantPro_Patch_Setup
SetupIconFile=Alpha_Quant_Pro_logo.ico
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
; CRITICAL: Allow overwriting existing files without uninstalling
DisableDirPage=yes
DirExistsWarning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Only bundle the main executable (Lightweight Patch)
Source: "dist\AlphaQuantPro\AlphaQuantPro.exe"; DestDir: "{app}"; Flags: ignoreversion

; Optional: Bundle Agents if strategy changed
; Source: "agents\*"; DestDir: "{app}\agents"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
