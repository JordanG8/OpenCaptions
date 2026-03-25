; ============================================================
;  Free KAPS — Inno Setup Installer Script
;  Builds a proper Windows installer (.exe) for the plugin.
;
;  To compile:
;    1. Install Inno Setup from https://jrsoftware.org/isinfo.php
;    2. Open this .iss file in Inno Setup Compiler
;    3. Click Build > Compile  (or Ctrl+F9)
;    4. Output: installer/Output/FreeKAPS-Setup.exe
; ============================================================

#define MyAppName "Free KAPS"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Jordan Goren"
#define MyAppURL "https://github.com/yosepov/OpenCaps"

[Setup]
AppId={{B7F2A1C3-5E4D-4F8A-9B1C-2D3E4F5A6B7C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={userappdata}\Adobe\CEP\extensions\com.freekaps.hebrewcaptions
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=Output
OutputBaseFilename=FreeKAPS-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableDirPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Welcome to Free KAPS
WelcomeLabel2=This will install Free KAPS — AI-powered Hebrew captions for Adobe Premiere Pro.%n%nEverything runs 100%% offline on your machine. No data leaves your computer.%n%nRequirements:%n  - Adobe Premiere Pro 2020+%n  - Python 3.10+%n  - FFmpeg on PATH

[Files]
; CEP Extension files
Source: "..\com.freekaps.hebrewcaptions\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
; Enable unsigned CEP extensions (PlayerDebugMode) for all known CSXS versions
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.9";  ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.10"; ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.11"; ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.12"; ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.13"; ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist

[Run]
; Post-install: Install Python dependencies (auto-detect GPU)
Filename: "python"; Parameters: """{app}\python\install_deps.py"""; \
  StatusMsg: "Installing Python dependencies (auto-detecting GPU)..."; \
  Flags: runhidden waituntilterminated; Check: PythonExists
; Post-install: Download AI model
Filename: "python"; Parameters: """{app}\python\download_model.py"""; \
  StatusMsg: "Downloading AI model (~1-2 GB, one-time)..."; \
  Description: "Download AI model (required, ~1-2 GB)"; \
  Flags: postinstall waituntilterminated

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// ── Pascal Script helpers ───────────────────────────────────

function PythonExists(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function FFmpegExists(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('ffmpeg', '-version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

procedure InitializeWizard();
begin
  // Custom font for the wizard
  WizardForm.WelcomeLabel1.Font.Size := 14;
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Warnings: String;
begin
  Result := True;

  // After welcome page, check prerequisites
  if CurPageID = wpWelcome then
  begin
    Warnings := '';

    if not PythonExists() then
      Warnings := Warnings + '- Python was NOT found on your PATH.' + #13#10 +
                  '  Install Python 3.10+ from python.org and check "Add to PATH".' + #13#10#13#10;

    if not FFmpegExists() then
      Warnings := Warnings + '- FFmpeg was NOT found on your PATH.' + #13#10 +
                  '  Download from ffmpeg.org and add it to your system PATH.' + #13#10#13#10;

    if Warnings <> '' then
    begin
      Result := (MsgBox('Some prerequisites are missing:' + #13#10#13#10 +
                        Warnings +
                        'The extension will install, but transcription won''t work until these are fixed.' + #13#10#13#10 +
                        'Continue anyway?',
                        mbConfirmation, MB_YESNO) = IDYES);
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Log success
    Log('Free KAPS installed to: ' + ExpandConstant('{app}'));
    Log('Registry keys set for CSXS 9-13');
  end;
end;
