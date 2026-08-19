; QuoteRenamer (견적서/거래명세서/세금계산서 PDF 리네이머) - Windows 설치 프로그램
; 관리자 권한 없이 현재 사용자 계정에만 설치됩니다 (회사 PC 정책 때문에
; 관리자 권한이 없는 사람도 설치할 수 있어야 해서).

#define MyAppName "QuoteRenamer"
#define MyAppVersion "1.2.3"
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
; 앱 자체적으로도 업데이트 전에 스스로 종료하지만(app.py 참고), 혹시
; 타이밍이 안 맞아 exe가 아직 실행 중이어도 설치가 막히지 않도록 보험 삼아
; 자동으로 앱을 닫고(CloseApplications), 설치 후 다시 띄워준다(RestartApplications).
CloseApplications=yes
RestartApplications=yes

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
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall
