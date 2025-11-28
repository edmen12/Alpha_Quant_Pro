#define MyAppName "Alpha Quant Pro"
#define MyAppVersion "1.0.0"
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
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Industry Standard: Install to Program Files (requires admin)
PrivilegesRequired=admin
OutputDir=Installer
OutputBaseFilename=AlphaQuantPro_Setup
SetupIconFile=Alpha_Quant_Pro_logo.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Core Executable (pythonw.exe renamed)
Source: "build_industry\AlphaQuantPro.exe"; DestDir: "{app}"; Flags: ignoreversion

; Runtime & Dependencies
Source: "build_industry\runtime\*"; DestDir: "{app}\runtime"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "build_industry\AlphaQuantPro_Runner.exe"; DestDir: "{app}"; Flags: ignoreversion

; Service (Compiled Code)
Source: "build_industry\service\*"; DestDir: "{app}\service"; Flags: ignoreversion recursesubdirs createallsubdirs

; UI Assets
Source: "build_industry\ui\*"; DestDir: "{app}\ui"; Flags: ignoreversion recursesubdirs createallsubdirs

; Updater (Integrated in main app)
; Source: "build_industry\updater\*"; DestDir: "{app}\updater"; Flags: ignoreversion recursesubdirs createallsubdirs

; VBS Launcher (Backup)
Source: "build_industry\AlphaQuantPro.vbs"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Main Shortcut: Runs AlphaQuantPro.exe (pythonw) with script argument
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "service/terminal_apple.pyc"; WorkingDir: "{app}"; IconFilename: "{app}\ui\assets\logo.png"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "service/terminal_apple.pyc"; WorkingDir: "{app}"; IconFilename: "{app}\ui\assets\logo.png"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "service/terminal_apple.pyc"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Dirs]
; Create AppData directories
Name: "{userappdata}\{#MyAppName}"; Flags: uninsalwaysuninstall
Name: "{userappdata}\{#MyAppName}\models"
Name: "{userappdata}\{#MyAppName}\configs"
Name: "{userappdata}\{#MyAppName}\workspace"
Name: "{localappdata}\{#MyAppName}"; Flags: uninsalwaysuninstall
Name: "{localappdata}\{#MyAppName}\logs"
Name: "{localappdata}\{#MyAppName}\cache"

[Code]
// Helper to check if app is running
function InitializeSetup(): Boolean;
begin
  Result := True;
  // Check if running
  // (Optional: Add logic to check if AlphaQuantPro.exe is running)
end;

// Uninstall cleanup
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Ask user to remove data?
    if MsgBox('Do you want to delete all user data (Models, Configs, Logs)?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{userappdata}\{#MyAppName}'), True, True, True);
      DelTree(ExpandConstant('{localappdata}\{#MyAppName}'), True, True, True);
    end;
  end;
end;
