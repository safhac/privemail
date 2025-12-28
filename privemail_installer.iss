; Script generated for Inno Setup
#define MyAppName "Privemail"
#define MyAppVersion "1.0"
#define MyAppPublisher "Privemail Inc"
#define MyAppExeName "Privemail.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
WizardStyle=modern
OutputBaseFilename=Privemail_Setup_v1.0
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 1. YOUR APP FILES (From PyInstaller)
Source: "dist\Privemail\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 2. OLLAMA INSTALLER (Bundled)
Source: "setup_assets\OllamaSetup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 1. Run Ollama Installer if needed
Filename: "{tmp}\OllamaSetup.exe"; StatusMsg: "Installing Ollama AI Engine (Required)..."; Check: OllamaNotInstalled; Flags: waituntilterminated

; 2. Download the Model (The "Brain") - Crucial for 500MB GPU compatibility
Filename: "{cmd}"; Parameters: "/C ollama pull qwen2.5:0.5b"; StatusMsg: "Downloading AI Model (qwen2.5:0.5b)..."; Flags: waituntilterminated runhidden

; 3. Run Privemail after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up temporary data but KEEP THE DATABASE (app_data)
Type: files; Name: "{app}\token.json"
Type: files; Name: "{app}\*.log"

[Code]
function OllamaNotInstalled: Boolean;
var
  ResultCode: Integer;
begin
  if Exec('cmd.exe', '/c ollama --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
    begin
      Log('Ollama is already installed.');
      Result := False;
    end
    else
    begin
      Log('Ollama not found. Proceeding with installation.');
      Result := True;
    end;
  end
  else
  begin
    Result := True;
  end;
end;