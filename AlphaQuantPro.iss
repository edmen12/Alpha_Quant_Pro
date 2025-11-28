; Alpha Quant Pro Installer Script
; Inno Setup 6.x required

#define MyAppName "Alpha Quant Pro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Alpha Quant"
#define MyAppExeName "Start_AlphaQuant.bat"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".aqp"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{8A9F2E3B-1C4D-5E6F-7A8B-9C0D1E2F3A4B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir=.\Installer
OutputBaseFilename=AlphaQuantPro_Setup
SetupIconFile=Alpha_Quant_Pro_logo.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 核心程序文件（安装到 Program Files）
Source: "AlphaQuantPro_Portable\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: shellexec postinstall skipifsilent

[Dirs]
; 创建用户数据目录 (AppData)
Name: "{userappdata}\{#MyAppName}"; Flags: uninsneveruninstall

[UninstallDelete]
; 卸载时清理文件
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}\logs"
Type: filesandordirs; Name: "{localappdata}\{#MyAppName}"

[Code]
// 检测是否已安装旧版本
function InitializeSetup(): Boolean;
var
  OldVersion: String;
  AppId: String;
  UninstallKey: String;
begin
  Result := True;
  
  // 使用 AppId 查找已安装版本
  AppId := '{8A9F2E3B-1C4D-5E6F-7A8B-9C0D1E2F3A4B}';
  UninstallKey := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' + AppId + '_is1';
  
  // 检查 HKLM (所有用户安装)
  if RegQueryStringValue(HKLM, UninstallKey, 'DisplayVersion', OldVersion) then
  begin
    MsgBox('检测到已安装版本: ' + OldVersion + #13#10#13#10 + 
           '即将自动升级到新版本 {#MyAppVersion}' + #13#10#13#10 +
           '您的用户数据和配置将被保留。', 
           mbInformation, MB_OK);
    Result := True;
  end
  // 检查 HKCU (当前用户安装)
  else if RegQueryStringValue(HKCU, UninstallKey, 'DisplayVersion', OldVersion) then
  begin
    MsgBox('检测到已安装版本: ' + OldVersion + #13#10#13#10 + 
           '即将自动升级到新版本 {#MyAppVersion}' + #13#10#13#10 +
           '您的用户数据和配置将被保留。', 
           mbInformation, MB_OK);
    Result := True;
  end;
end;

// 卸载后清理逻辑
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDataDir: String;
  Response: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDataDir := ExpandConstant('{userappdata}\{#MyAppName}');
    
    // 询问用户是否删除用户数据
    Response := MsgBox('是否同时删除用户数据（日志、配置）？' + #13#10#13#10 +
                       '位置: ' + AppDataDir + #13#10#13#10 +
                       '选择"是"将完全卸载' + #13#10 +
                       '选择"否"将保留您的设置（方便重新安装）',
                       mbConfirmation, MB_YESNO);
    
    if Response = IDYES then
    begin
      if DirExists(AppDataDir) then
        DelTree(AppDataDir, True, True, True);
    end;
  end;
end;
