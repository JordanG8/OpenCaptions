; ============================================================
;  OpenCaptions — Inno Setup Installer Script
;  Builds a proper Windows installer (.exe) for the plugin.
;
;  IMPORTANT: Run build_installer.py FIRST to download the
;  bundled Python + FFmpeg into com.opencaptions.hebrewcaptions/vendor/
;
;  To compile:
;    1. python installer/build_installer.py
;    2. Output: installer/Output/OpenCaptions-Setup-1.0.0.exe
; ============================================================

#define MyAppName "OpenCaptions"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "Jordan Goren"
#define MyAppURL "https://github.com/JordanG8/OpenCaptions"

[Setup]
AppId={{B7F2A1C3-5E4D-4F8A-9B1C-2D3E4F5A6B7C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={userappdata}\Adobe\CEP\extensions\com.opencaptions.hebrewcaptions
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=Output
OutputBaseFilename=OpenCaptions-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=compiler:SetupClassicIcon.ico
VersionInfoVersion=1.2.0
VersionInfoCompany=Jordan Goren
VersionInfoDescription=OpenCaptions - AI Hebrew Captions for Premiere Pro
VersionInfoProductName=OpenCaptions
DisableDirPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Welcome to OpenCaptions
WelcomeLabel2=This will install OpenCaptions — AI-powered Hebrew captions for Adobe Premiere Pro.%n%nEverything runs 100%% offline on your machine. No data leaves your computer.%n%nPython, FFmpeg, and the AI model are all included — no extra downloads.%n%nIMPORTANT: Right-click the installer and select "Run as Administrator" if installation fails. This is needed to set Adobe registry keys.%n%nRequirements:%n  - Adobe Premiere Pro 2020+

[Files]
; CEP Extension files (includes vendor/python and vendor/ffmpeg)
Source: "..\com.opencaptions.hebrewcaptions\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
; Enable unsigned CEP extensions (PlayerDebugMode) for all known CSXS versions
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.9";  ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.10"; ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.11"; ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.12"; ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.13"; ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.14"; ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "SOFTWARE\Adobe\CSXS.15"; ValueName: "PlayerDebugMode"; ValueType: string; ValueData: "1"; Flags: createvalueifdoesntexist

[Run]
; Post-install: Install Python dependencies using BUNDLED Python (auto-detect GPU)
; Console window is visible so user can see download progress and disk stats
Filename: "{app}\vendor\python\python.exe"; Parameters: "-u ""{app}\python\install_deps.py"""; \
  StatusMsg: "Installing AI packages (see console window for progress)..."; \
  Flags: waituntilterminated
; AI model is bundled in vendor/models/ — no download needed

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// ── Pascal Script helpers ───────────────────────────────────

procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel1.Font.Size := 14;
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];
end;

function VendorPythonExists(): Boolean;
begin
  // Verify the bundled Python was included in the package
  Result := FileExists(ExpandConstant('{app}\vendor\python\python.exe'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    Log('OpenCaptions installed to: ' + ExpandConstant('{app}'));
    Log('Registry keys set for CSXS 9-13');

    if not VendorPythonExists() then
    begin
      MsgBox('WARNING: Bundled Python was not found.' + #13#10 +
             'The installer may have been built without running build_installer.py first.' + #13#10#13#10 +
             'AI transcription will not work until Python is set up manually.' + #13#10 +
             'See the project README for manual installation steps.',
             mbError, MB_OK);
    end;
  end;
end;
