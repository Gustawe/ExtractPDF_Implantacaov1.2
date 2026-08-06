#ifndef AppVersion
  #define AppVersion "0.5.2"
#endif

#define AppName "Conversor de Folhas — Implantação"
#define AppExecutable "ConversorFolhas.exe"

[Setup]
AppId={{F7B3731E-4551-4C60-A695-B9BE5586BCDA}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Equipe de Infraestrutura de TI
DefaultDirName={localappdata}\Programs\Conversor de Folhas
DefaultGroupName=Conversor de Folhas
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=output
OutputBaseFilename=Conversor-de-Folhas-Setup-{#AppVersion}
SetupIconFile=..\src\conversor_folhas\resources\app.ico
UninstallDisplayIcon={app}\{#AppExecutable}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Files]
Source: "..\dist\ConversorFolhas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Conversor de Folhas"; Filename: "{app}\{#AppExecutable}"
Name: "{autodesktop}\Conversor de Folhas"; Filename: "{app}\{#AppExecutable}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExecutable}"; Description: "Abrir o Conversor de Folhas"; Flags: nowait postinstall
