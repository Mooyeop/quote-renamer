; QuoteRenamer (견적서/거래명세서/세금계산서 PDF 리네이머) - Windows 설치 프로그램
; 관리자 권한 없이 현재 사용자 계정에만 설치됩니다 (회사 PC 정책 때문에
; 관리자 권한이 없는 사람도 설치할 수 있어야 해서).

#define MyAppName "QuoteRenamer"
#define MyAppVersion "1.2.5"
#define MyAppExeName "QuoteRenamer.exe"

[Setup]
AppId={{7633398E-B6DC-48F6-9A74-68AF6735E35A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=QuoteRenamer_Setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; 실행 중인 앱을 닫되, 새 앱 실행은 아래 [Run]에서 한 번만 처리한다.
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Files]
Source: "release\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "release\company_aliases.json"; DestDir: "{app}"; Flags: onlyifdoesntexist
Source: "release\tesseract\*"; DestDir: "{app}\tesseract"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

[Run]
; skipifsilent를 안 붙임 - 앱이 백그라운드에서 자동 업데이트를 걸 때도
; (/SILENT로 조용히 설치) 설치 후 자동으로 다시 실행되도록 하기 위해서.
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall runascurrentuser

[Code]
function SetEnvironmentVariable(lpName, lpValue: string): Boolean;
  external 'SetEnvironmentVariableW@kernel32.dll stdcall';

function InitializeSetup(): Boolean;
begin
  { v1.2.3/v1.2.4가 실행한 설치 프로그램도 새 앱을 독립적으로 시작해야 한다.
    이전 앱의 _MEI 임시 폴더는 종료 시 삭제되므로 재사용하지 않는다. }
  Result := SetEnvironmentVariable('PYINSTALLER_RESET_ENVIRONMENT', '1');
  { 구버전 앱은 설치 프로그램을 시작한 뒤 600ms 후 종료한다.
    RestartManager가 그 종료 과정에 끼어들지 않도록 먼저 기다린다. }
  if Result and WizardSilent then
    Sleep(2000);
  if not Result then
    MsgBox('업데이트 실행 환경을 초기화하지 못했습니다. 설치 파일을 직접 실행해 주세요.', mbError, MB_OK);
end;
