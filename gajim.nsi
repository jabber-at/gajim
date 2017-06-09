﻿; File encoding 'UTF-8 with BOM'

Unicode true
!include "MUI2.nsh"

Name "Gajim"
OutFile "Gajim.exe"
SetCompressor /final /solid lzma

!define myAppName "Gajim"

InstallDir "$PROGRAMFILES\Gajim"
InstallDirRegKey HKCU "Software\Gajim" ""
RequestExecutionLevel admin

Var StartMenuFolder

!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "data\pixmaps\nsis_header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "data\pixmaps\nsis_wizard.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "data\pixmaps\nsis_wizard.bmp"
;!define MUI_COMPONENTSPAGE_CHECKBITMAP "${NSISDIR}\Contrib\Graphics\Checks\colorful.bmp"
!define MUI_COMPONENTSPAGE_SMALLDESC
!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "COPYING"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\Gajim"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\bin\Gajim.exe"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;Show all languages, despite user's codepage
!define MUI_LANGDLL_ALLLANGUAGES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "German"
!insertmacro MUI_LANGUAGE "Italian"
!insertmacro MUI_LANGUAGE "Russian"
!insertmacro MUI_LANGUAGE "Hebrew"
!insertmacro MUI_RESERVEFILE_LANGDLL

; English
LangString NAME_Emoticons ${LANG_ENGLISH} "Emoticons"
LangString NAME_Iconsets ${LANG_ENGLISH} "Iconsets"
LangString NAME_Languages ${LANG_ENGLISH} "Languages"
LangString NAME_SecLanguagesOther ${LANG_ENGLISH} "Other"
LangString NAME_Themes ${LANG_ENGLISH} "Themes"
LangString NAME_SecDesktopIcon ${LANG_ENGLISH} "Create icon on desktop"
LangString NAME_SecAutostart ${LANG_ENGLISH} "Start Gajim when Windows starts"
LangString DESC_SecGajim ${LANG_ENGLISH} "Installs the main Gajim files."
LangString DESC_SecGtk ${LANG_ENGLISH} "Installs Gtk+ 2 (necessary to run Gajim)."
LangString DESC_SecDesktopIcon ${LANG_ENGLISH} "If set, a shortcut for Gajim will be created on the desktop."
LangString DESC_SecAutostart ${LANG_ENGLISH} "If set, Gajim will be automatically started when Windows starts."
LangString STR_Installed ${LANG_ENGLISH} "Apparently, Gajim is already installed. Uninstall it?"
LangString STR_Running ${LANG_ENGLISH} "It appears that Gajim is currently running.$\n\
		Please quit Gajim and restart the uninstaller."

; French
LangString NAME_Emoticons ${LANG_FRENCH} "Emoticônes"
LangString NAME_Iconsets ${LANG_FRENCH} "Bibliothèque d'icônes"
LangString NAME_Languages ${LANG_FRENCH} "Langues"
LangString NAME_SecLanguagesOther ${LANG_FRENCH} "Autre"
LangString NAME_Themes ${LANG_FRENCH} "Thèmes"
LangString NAME_SecDesktopIcon ${LANG_FRENCH} "Créer une icône sur le bureau"
LangString NAME_SecAutostart ${LANG_FRENCH} "Lancer Gajim au démarrage de Windows"
LangString DESC_SecGajim ${LANG_FRENCH} "Installer les fichiers principaux de Gajim."
LangString DESC_SecGtk ${LANG_FRENCH} "Installer Gtk+ 2 (nécessaire à Gajim)."
LangString DESC_SecDesktopIcon ${LANG_FRENCH} "Si selectionné, un raccourci pour Gajim sera créé sur le bureau."
LangString DESC_SecAutostart ${LANG_FRENCH} "Si activé, Gajim sera automatiquement lancé au démarrage de Windows."
LangString STR_Installed ${LANG_FRENCH} "Gajim est apparement déjà installé. Lancer la désinstallation ?"
LangString STR_Running ${LANG_FRENCH} "Gajim est apparament lancé.$\n\
		Fermez-le et redémarrez le désinstallateur."

; German
LangString NAME_Emoticons ${LANG_GERMAN} "Emoticons"
LangString NAME_Iconsets ${LANG_GERMAN} "Symbolsets"
LangString NAME_Languages ${LANG_GERMAN} "Sprachen"
LangString NAME_SecLanguagesOther ${LANG_GERMAN} "Sonstige"
LangString NAME_Themes ${LANG_GERMAN} "Designs"
LangString NAME_SecDesktopIcon ${LANG_GERMAN} "Desktop-Icon erstellen"
LangString NAME_SecAutostart ${LANG_GERMAN} "Gajim mit Windows starten"
LangString DESC_SecGajim ${LANG_GERMAN} "Installiert die Hauptdateien von Gajim."
LangString DESC_SecGtk ${LANG_GERMAN} "Installiert Gtk+ 2 (notwendig um Gajim zu benutzen)."
LangString DESC_SecDesktopIcon ${LANG_GERMAN} "Wenn dies aktiviert wird, wird ein Icon für Gajim auf dem Desktop erstellt."
LangString DESC_SecAutostart ${LANG_GERMAN} "Gajim wird automatisch gestartet, sowie Windows startet, wenn dies aktivier wird."
LangString STR_Installed ${LANG_GERMAN} "Gajim ist bereits installiert. Soll es deinstalliert werden?"
LangString STR_Running ${LANG_GERMAN} "Es scheint, dass Gajim bereits läuft.$\n\
		Bitte beenden Sie es und starten Sie den Installer erneut.."

; Italian
LangString NAME_Emoticons ${LANG_ITALIAN} "Emoticons"
LangString NAME_Iconsets ${LANG_ITALIAN} "Set di icone"
LangString NAME_Languages ${LANG_ITALIAN} "Lingue"
LangString NAME_SecLanguagesOther ${LANG_ITALIAN} "Altre"
LangString NAME_Themes ${LANG_ITALIAN} "Temi"
LangString NAME_SecDesktopIcon ${LANG_ITALIAN} "Crea un'icona sul desktop"
LangString NAME_SecAutostart ${LANG_ITALIAN} "Lancia Gajim quando parte Windows"
LangString DESC_SecGajim ${LANG_ITALIAN} "Installa i file principali di Gajim."
LangString DESC_SecGtk ${LANG_ITALIAN} "Installa Gtk+ 2 (necessario per eseguire Gajim)."
LangString DESC_SecDesktopIcon ${LANG_ITALIAN} "Se selezionato, un'icona verrà creata sul desktop."
LangString DESC_SecAutostart ${LANG_ITALIAN} "Se selezionato, Gajim sarà eseguito all'avvio di Windows."
LangString STR_Installed ${LANG_ITALIAN} "Gajim is apparently already installed. Uninstall it?"
LangString STR_Running ${LANG_ITALIAN} "It appears that Gajim is currently running.$\n\
		Close it and restart uninstaller."

; Russian
LangString NAME_Emoticons ${LANG_RUSSIAN} "Смайлики"
LangString NAME_Iconsets ${LANG_RUSSIAN} "Темы иконок"
LangString NAME_Languages ${LANG_RUSSIAN} "Языки"
LangString NAME_SecLanguagesOther ${LANG_RUSSIAN} "Другое"
LangString NAME_Themes ${LANG_RUSSIAN} "Темы"
LangString NAME_SecDesktopIcon ${LANG_RUSSIAN} "Создать я лык на абочем столе"
LangString NAME_SecAutostart ${LANG_RUSSIAN} "Запускать Gajim при загрузке Windows"
LangString DESC_SecGajim ${LANG_RUSSIAN} "Установка основных файлов Gajim."
LangString DESC_SecGtk ${LANG_RUSSIAN} "Установка Gtk 2 (необходимо для работы Gajim)."
LangString DESC_SecDesktopIcon ${LANG_RUSSIAN} "Если отмечено, на рабочем столе будет создан ярлык Gajim."
LangString DESC_SecAutostart ${LANG_RUSSIAN} "Если отмечено, Gajim будет автоматически запускаться при загрузке Windows."
LangString STR_Installed ${LANG_RUSSIAN} "Похоже, Gajim уже установлен. Деинсталлировать установленную версию?"
LangString STR_Running ${LANG_RUSSIAN} "Похоже, Gajim уже запущен.$\n\
		Закройте его и запустите деинсталлятор снова."


; Hebrew
LangString NAME_Emoticons ${LANG_HEBREW} "רגשונים"
LangString NAME_Iconsets ${LANG_HEBREW} "מערכי צלמית"
LangString NAME_Languages ${LANG_HEBREW} "שפות"
LangString NAME_SecLanguagesOther ${LANG_HEBREW} "אחרות"
LangString NAME_Themes ${LANG_HEBREW} "ערכאות נושא"
LangString NAME_SecDesktopIcon ${LANG_HEBREW} "צור סמל בשולחן עבודה"
LangString NAME_SecAutostart ${LANG_HEBREW} "הפעל את Gajim כאשר Windows מתחיל"
LangString DESC_SecGajim ${LANG_HEBREW} "מתקין קבצי Gajim עיקריים."
LangString DESC_SecGtk ${LANG_HEBREW} "מתקין Gtk+ 2 (נחוצה להרצת Gajim)."
LangString DESC_SecDesktopIcon ${LANG_HEBREW} "במידה ונקבעת, קיצור דרך עבור Gajim יושם על שולחן העבודה."
LangString DESC_SecAutostart ${LANG_HEBREW} "במידה ונקבעת, Gajim יופעל אוטומטית כאשר Windows מתחיל."
LangString STR_Installed ${LANG_HEBREW} "כפי הנראה, Gajim כבר מותקן. להסיר אותו?"
LangString STR_Running ${LANG_HEBREW} "נראה שהתוכנית Gajim מורצת כעת.$\n\
        אנא צא מן Gajim ואתחל את מסיר ההתקנה."

Section "Gajim" SecGajim
	SectionIn RO

	SetOutPath "$INSTDIR"
	File "AUTHORS"
	File "COPYING"
	File "THANKS"
	File "THANKS.artists"
	File /r "bin"

	WriteRegStr HKCU "Software\Gajim" "" $INSTDIR
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Gajim" "DisplayName" "Gajim"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Gajim" "UninstallString" "$INSTDIR\Uninstall.exe"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Gajim" "DisplayIcon" "$INSTDIR\bin\Gajim.exe"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Gajim" "DisplayVersion" "0.16.8"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Gajim" "URLInfoAbout" "http://www.gajim.org/"
	WriteUninstaller "$INSTDIR\Uninstall.exe"

	SetOutPath "$INSTDIR\bin"
	!insertmacro MUI_STARTMENU_WRITE_BEGIN Application
		SetShellVarContext current
		CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
		CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Gajim.lnk" "$INSTDIR\bin\Gajim.exe"
		CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Change Theme.lnk" "$INSTDIR\bin\gtk\bin\gtkthemeselector.exe"
		SetShellVarContext all
		CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
		CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Gajim.lnk" "$INSTDIR\bin\Gajim.exe"
		CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Change Theme.lnk" "$INSTDIR\bin\gtk\bin\gtkthemeselector.exe"
	!insertmacro MUI_STARTMENU_WRITE_END

	SetOutPath "$INSTDIR\data"	
	File /r "data\gui"
	File /r "data\moods"
	File /r "data\activities"
	File /r "data\other"
	File /r "data\pixmaps"
	File /r "data\sounds"
	
	SetOutPath "$INSTDIR\icons"	
	File /r "icons\hicolor"
SectionEnd

Section "Gtk+ 2" SecGtk
	SectionIn RO
	SetOutPath "$INSTDIR\bin\gtk"
	File /r "bin\gtk\bin"
	File /r "bin\gtk\etc"
	File /r "bin\gtk\lib"
	File /r "bin\gtk\share"
SectionEnd

Section "Plugins" SecPlugins
	SetOutPath "$INSTDIR\plugins"
	File /r "plugins\plugin_installer"
SectionEnd

SectionGroup $(NAME_Emoticons)

Section "animated" SecEmoticonsAnimated
	SetOutPath "$INSTDIR\data\emoticons"
	File /r "data\emoticons\animated"
SectionEnd

Section "static" SecEmoticonsStatic
	SectionIn RO
	SetOutPath "$INSTDIR\data\emoticons"
	File /r "data\emoticons\static"
SectioNEnd

Section "static-big" SecEmoticonsStaticBig
	SetOutPath "$INSTDIR\data\emoticons"
	File /r "data\emoticons\static-big"
SectionEnd

SectionGroupEnd

SectionGroup $(NAME_Iconsets)

Section "dcraven" SecIconsetsDcraven
	SectionIn RO
	SetOutPath "$INSTDIR\data\iconsets"
	File /r "data\iconsets\dcraven"
SectionEnd

Section "gnome" SecIconsetsGnome
	SetOutPath "$INSTDIR\data\iconsets"
	File /r "data\iconsets\gnome"
SectionEnd

Section "goojim" SecIconsetsGoojim
	SetOutPath "$INSTDIR\data\iconsets"
	File /r "data\iconsets\goojim"
SectionEnd

Section "gota" SecIconsetsGota
	SetOutPath "$INSTDIR\data\iconsets"
	File /r "data\iconsets\gota"
SectionEnd

Section "jabberbulb" SecIconsetsJabberbulb
	SetOutPath "$INSTDIR\data\iconsets"
	File /r "data\iconsets\jabberbulb"
SectionEnd

Section "sun" SecIconsetsSun
	SetOutPath "$INSTDIR\data\iconsets"
	File /r "data\iconsets\sun"
SectionEnd

Section "wroop" SecIconsetsWroop
	SetOutPath "$INSTDIR\data\iconsets"
	File /r "data\iconsets\wroop"
SectionEnd

Section "transports" SecIconsetsTransports
	SetOutPath "$INSTDIR\data\iconsets"
	File /r "data\iconsets\transports"
	SectionIn Ro
SectionEnd

SectionGroupEnd

SectionGroup $(NAME_Languages)

Section "English (UK)" SecLanguagesEnglishUK
	SetOutPath "$INSTDIR\po"
	File /r "po\en_GB"
	SetOutPath "$INSTDIR\bin\gtk\share\locale"
	File /r "bin\gtk\share\locale\en_GB"
SectionEnd

Section "French" SecLanguagesFrench
	SetOutPath "$INSTDIR\po"
	File /r "po\fr"
	SetOutPath "$INSTDIR\bin\gtk\share\locale"
	File /r "bin\gtk\share\locale\fr"
SectionEnd

Section "German" SecLanguagesGerman
	SetOutPath "$INSTDIR\po"
	File /r "po\de"
	SetOutPath "$INSTDIR\bin\gtk\share\locale"
	File /r "bin\gtk\share\locale\de"
SectionEnd

Section "Italian" SecLanguagesItalian
	SetOutPath "$INSTDIR\po"
	File /r "po\it"
	SetOutPath "$INSTDIR\bin\gtk\share\locale"
	File /r "bin\gtk\share\locale\it"
SectionEnd

Section "Spanish" SecLanguagesSpanish
	SetOutPath "$INSTDIR\po"
	File /r "po\es"
	SetOutPath "$INSTDIR\bin\gtk\share\locale"
	File /r "bin\gtk\share\locale\es"
SectionEnd

Section "Russian" SecLanguagesRussian
	SetOutPath "$INSTDIR\po"
	File /r "po\ru"
	SetOutPath "$INSTDIR\bin\gtk\share\locale"
	File /r "bin\gtk\share\locale\ru"
SectionEnd

Section $(NAME_SecLanguagesOther) SecLanguagesOther
	SetOutPath "$INSTDIR\po"
	File /r "po\be"
	File /r "po\be@latin"
	File /r "po\bg"
	File /r "po\br"
	File /r "po\cs"
	File /r "po\da"
	File /r "po\el"
	File /r "po\eo"
	File /r "po\eu"
	File /r "po\gl"
	File /r "po\he"
	File /r "po\hr"
	File /r "po\lt"
	File /r "po\nb_NO"
	File /r "po\nl"
	File /r "po\pl"
	File /r "po\pt"
	File /r "po\pt_BR"
	File /r "po\sk"
	File /r "po\sr"
	File /r "po\sr@Latn"
	File /r "po\sv"
	File /r "po\uk"
	File /r "po\zh_CN"
	SetOutPath "$INSTDIR\bin\gtk\share\locale"
	File /r "bin\gtk\share\locale\af"
	File /r "bin\gtk\share\locale\am"
	File /r "bin\gtk\share\locale\ang"
	File /r "bin\gtk\share\locale\ar"
	File /r "bin\gtk\share\locale\as"
	File /r "bin\gtk\share\locale\az"
	File /r "bin\gtk\share\locale\az_IR"
	File /r "bin\gtk\share\locale\be"
	File /r "bin\gtk\share\locale\be@latin"
	File /r "bin\gtk\share\locale\bg"
	File /r "bin\gtk\share\locale\bn"
	File /r "bin\gtk\share\locale\bn_IN"
	File /r "bin\gtk\share\locale\br"
	File /r "bin\gtk\share\locale\bs"
	File /r "bin\gtk\share\locale\ca"
	File /r "bin\gtk\share\locale\ca@valencia"
	File /r "bin\gtk\share\locale\cs"
	File /r "bin\gtk\share\locale\cy"
	File /r "bin\gtk\share\locale\da"
	File /r "bin\gtk\share\locale\dz"
	File /r "bin\gtk\share\locale\el"
	File /r "bin\gtk\share\locale\en_CA"
	File /r "bin\gtk\share\locale\eo"
	File /r "bin\gtk\share\locale\et"
	File /r "bin\gtk\share\locale\eu"
	File /r "bin\gtk\share\locale\fa"
	File /r "bin\gtk\share\locale\fi"
	File /r "bin\gtk\share\locale\ga"
	File /r "bin\gtk\share\locale\gl"
	File /r "bin\gtk\share\locale\gu"
	File /r "bin\gtk\share\locale\he"
	File /r "bin\gtk\share\locale\hi"
	File /r "bin\gtk\share\locale\hr"
	File /r "bin\gtk\share\locale\hu"
	File /r "bin\gtk\share\locale\hy"
	File /r "bin\gtk\share\locale\ia"
	File /r "bin\gtk\share\locale\id"
	File /r "bin\gtk\share\locale\io"
	File /r "bin\gtk\share\locale\is"
	File /r "bin\gtk\share\locale\ja"
	File /r "bin\gtk\share\locale\ka"
	File /r "bin\gtk\share\locale\kn"
	File /r "bin\gtk\share\locale\ko"
	File /r "bin\gtk\share\locale\ku"
	File /r "bin\gtk\share\locale\li"
	File /r "bin\gtk\share\locale\lt"
	File /r "bin\gtk\share\locale\lv"
	File /r "bin\gtk\share\locale\mai"
	File /r "bin\gtk\share\locale\mg"
	File /r "bin\gtk\share\locale\mi"
	File /r "bin\gtk\share\locale\mk"
	File /r "bin\gtk\share\locale\ml"
	File /r "bin\gtk\share\locale\mn"
	File /r "bin\gtk\share\locale\mr"
	File /r "bin\gtk\share\locale\ms"
	File /r "bin\gtk\share\locale\nb"
	File /r "bin\gtk\share\locale\ne"
	File /r "bin\gtk\share\locale\nl"
	File /r "bin\gtk\share\locale\nn"
	File /r "bin\gtk\share\locale\nso"
	File /r "bin\gtk\share\locale\oc"
	File /r "bin\gtk\share\locale\or"
	File /r "bin\gtk\share\locale\pa"
	File /r "bin\gtk\share\locale\pl"
	File /r "bin\gtk\share\locale\ps"
	File /r "bin\gtk\share\locale\pt"
	File /r "bin\gtk\share\locale\pt_BR"
	File /r "bin\gtk\share\locale\ro"
	File /r "bin\gtk\share\locale\rw"
	File /r "bin\gtk\share\locale\si"
	File /r "bin\gtk\share\locale\sk"
	File /r "bin\gtk\share\locale\sl"
	File /r "bin\gtk\share\locale\sq"
	File /r "bin\gtk\share\locale\sr"
	File /r "bin\gtk\share\locale\sr@ije"
	File /r "bin\gtk\share\locale\sr@latin"
	File /r "bin\gtk\share\locale\sv"
	File /r "bin\gtk\share\locale\ta"
	File /r "bin\gtk\share\locale\te"
	File /r "bin\gtk\share\locale\th"
	File /r "bin\gtk\share\locale\tk"
	File /r "bin\gtk\share\locale\tl"
	File /r "bin\gtk\share\locale\tr"
	File /r "bin\gtk\share\locale\tt"
	File /r "bin\gtk\share\locale\ug"
	File /r "bin\gtk\share\locale\uk"
	File /r "bin\gtk\share\locale\ur"
	File /r "bin\gtk\share\locale\uz"
	File /r "bin\gtk\share\locale\uz@cyrillic"
	File /r "bin\gtk\share\locale\vi"
	File /r "bin\gtk\share\locale\wa"
	File /r "bin\gtk\share\locale\xh"
	File /r "bin\gtk\share\locale\yi"
	File /r "bin\gtk\share\locale\zh_CN"
	File /r "bin\gtk\share\locale\zh_HK"
	File /r "bin\gtk\share\locale\zh_TW"
SectionEnd

SectionGroupEnd

SectionGroup $(NAME_Themes)

Section "Clearlooks" SecThemesClearlooks
	SetOutPath "$INSTDIR\bin\gtk\share\themes"
	File /r "bin\gtk\share\themes\Clearlooks"
SectionEnd

Section "Default GTK" SecThemesDefault
	SetOutPath "$INSTDIR\bin\gtk\share\themes"
	File /r "bin\gtk\share\themes\Default"
SectionEnd

Section "Glossy" SecThemesGlossy
	SetOutPath "$INSTDIR\bin\gtk\share\themes"
	File /r "bin\gtk\share\themes\Glossy"
SectionEnd

Section "Glossy-js" SecThemesGlossyJs
	SectionIn RO
	SetOutPath "$INSTDIR\bin\gtk\share\themes"
	File /r "bin\gtk\share\themes\Glossy-js"
SectionEnd

Section "MS-Windows" SecThemesMSWindows
	SetOutPath "$INSTDIR\bin\gtk\lib\gtk-2.0\2.10.0\engines"
	File "bin\gtk\lib\gtk-2.0\2.10.0\engines\libwimp.dll"
	SetOutPath "$INSTDIR\bin\gtk\share\themes"
	File /r "bin\gtk\share\themes\MS-Windows"
SectionEnd

SectionGroupEnd

Section $(NAME_SecDesktopIcon) SecDesktopIcon
	SetShellVarContext current
	SetOutPath "$INSTDIR\bin"
	CreateShortCut "$DESKTOP\Gajim.lnk" "$INSTDIR\bin\Gajim.exe"
SectionEnd

Section $(NAME_SecAutostart) SecAutostart
	SetShellVarContext current
	SetOutPath "$INSTDIR\bin"
	CreateShortCut "$SMSTARTUP\Gajim.lnk" "$INSTDIR\bin\Gajim.exe"
SectionEnd

Section "Uninstall"
	RMDir /r "$INSTDIR\bin\gtk\bin"
	RMDir /r "$INSTDIR\bin\gtk\etc"
	RMDir /r "$INSTDIR\bin\gtk\lib"
	RMDir /r "$INSTDIR\bin\gtk\share"
	RMDir "$INSTDIR\bin\gtk"
	RMDir "$INSTDIR\bin\win32com"
	RMDir /r "$INSTDIR\bin"
	RMDir /r "$INSTDIR\data\gui"
	RMDir /r "$INSTDIR\data\moods"
	RMDir /r "$INSTDIR\data\activities"
	RMDir /r "$INSTDIR\data\other"
	RMDir /r "$INSTDIR\data\pixmaps"
	RMDir /r "$INSTDIR\data\sounds"
	RMDir /r "$INSTDIR\data\emoticons\animated"
	RMDir /r "$INSTDIR\data\emoticons\static"
	RMDir /r "$INSTDIR\data\emoticons\static-big"
	RMDir "$INSTDIR\data\emoticons"
	RMDir /r "$INSTDIR\data\iconsets\dcraven"
	RMDir /r "$INSTDIR\data\iconsets\gnome"
	RMDir /r "$INSTDIR\data\iconsets\goojim"
	RMDir /r "$INSTDIR\data\iconsets\gota"
	RMDir /r "$INSTDIR\data\iconsets\jabberbulb"
	RMDir /r "$INSTDIR\data\iconsets\sun"
	RMDir /r "$INSTDIR\data\iconsets\wroop"
	RMDir /r "$INSTDIR\data\iconsets\transports"
	RMDir "$INSTDIR\data\iconsets"
	RMDir "$INSTDIR\data"
	RMDir /r "$INSTDIR\plugins\plugin_installer"
	RMDir "$INSTDIR\plugins"
	RMDir /r "$INSTDIR\icons\hicolor"
	RMDir "$INSTDIR\icons"
	RMDir /r "$INSTDIR\po\be"
	RMDir /r "$INSTDIR\po\be@latin"
	RMDir /r "$INSTDIR\po\bg"
	RMDir /r "$INSTDIR\po\br"
	RMDir /r "$INSTDIR\po\cs"
	RMDir /r "$INSTDIR\po\da"
	RMDir /r "$INSTDIR\po\de"
	RMDir /r "$INSTDIR\po\el"
	RMDir /r "$INSTDIR\po\en_GB"
	RMDir /r "$INSTDIR\po\eo"
	RMDir /r "$INSTDIR\po\es"
	RMDir /r "$INSTDIR\po\eu"
	RMDir /r "$INSTDIR\po\fr"
	RMDir /r "$INSTDIR\po\gl"
	RMDir /r "$INSTDIR\po\he"
	RMDir /r "$INSTDIR\po\hr"
	RMDir /r "$INSTDIR\po\it"
	RMDir /r "$INSTDIR\po\lt"
	RMDir /r "$INSTDIR\po\nb_NO"
	RMDir /r "$INSTDIR\po\nl"
	RMDir /r "$INSTDIR\po\pl"
	RMDir /r "$INSTDIR\po\pt"
	RMDir /r "$INSTDIR\po\pt_BR"
	RMDir /r "$INSTDIR\po\ru"
	RMDir /r "$INSTDIR\po\sk"
	RMDir /r "$INSTDIR\po\sr"
	RMDir /r "$INSTDIR\po\sr@Latn"
	RMDir /r "$INSTDIR\po\sv"
	RMDir /r "$INSTDIR\po\uk"
	RMDir /r "$INSTDIR\po\zh_CN"
	RMDir "$INSTDIR\po"
	Delete "$INSTDIR\AUTHORS"
	Delete "$INSTDIR\COPYING"
	Delete "$INSTDIR\THANKS"
	Delete "$INSTDIR\THANKS.artists"
	Delete "$INSTDIR\Uninstall.exe"
	RMDir "$INSTDIR"

	!insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder

	SetShellVarContext current
	Delete "$SMPROGRAMS\$StartMenuFolder\Gajim.lnk"
	Delete "$SMPROGRAMS\$StartMenuFolder\Change Theme.lnk"
	RMDir "$SMPROGRAMS\$StartMenuFolder"
	Delete "$DESKTOP\Gajim.lnk"
	Delete "$SMSTARTUP\Gajim.lnk"
	SetShellVarContext all
	Delete "$SMPROGRAMS\$StartMenuFolder\Gajim.lnk"
	Delete "$SMPROGRAMS\$StartMenuFolder\Change Theme.lnk"
	RMDir "$SMPROGRAMS\$StartMenuFolder"

	DeleteRegKey /ifempty HKCU "Software\Gajim"
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Gajim"
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
	!insertmacro MUI_DESCRIPTION_TEXT ${SecGajim} $(DESC_SecGajim)
	!insertmacro MUI_DESCRIPTION_TEXT ${SecGtk} $(DESC_SecGtk)
	!insertmacro MUI_DESCRIPTION_TEXT ${SecDesktopIcon} $(DESC_SecDesktopIcon)
	!insertmacro MUI_DESCRIPTION_TEXT ${SecAutostart} $(DESC_SecAutostart)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Function un.onInit
;	Check that Gajim is not running before uninstalling
	FindWindow $0 "gdkWindowToplevel" "Gajim"
	StrCmp $0 0 Remove
	MessageBox MB_ICONSTOP|MB_OK $(STR_Running)
	Quit
Remove:
	!insertmacro MUI_UNGETLANGUAGE
FunctionEnd

Function .onInit
	BringToFront
;	Check if already running
;	If so don't open another but bring to front
	System::Call "kernel32::CreateMutexA(i 0, i 0, t '$(^Name)') i .r0 ?e"
	Pop $0
	StrCmp $0 0 launch
	StrLen $0 "$(^Name)"
	IntOp $0 $0 + 1
	FindWindow $1 '#32770' '' 0 $1
	IntCmp $1 0 +3
	System::Call "user32::ShowWindow(i r1,i 9) i."         ; If minimized then maximize
	System::Call "user32::SetForegroundWindow(i r1) i."    ; Bring to front
	Abort

launch:
;	Check to see if old install (inno setup) is already installed
	ReadRegStr $R0 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Gajim_is1" "UninstallString"
;	remove first and last " char
	StrLen $0 $R0
	IntOp $0 $0 - 2
	strcpy $1 $R0 $0 1
	IfFileExists $1 +1 NotInstalled
	MessageBox MB_YESNO|MB_DEFBUTTON2|MB_TOPMOST $(STR_Installed) IDNO Quit
	StrCmp $R1 2 Quit +1
	ExecWait '$R0 _?=$INSTDIR' $R2
	StrCmp $R2 0 +1 Quit

NotInstalled:	
;	Check to see if new installer (NSIS)already installed
	ReadRegStr $R3 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Gajim" "UninstallString"
	IfFileExists $R3 +1 ReallyNotInstalled
	MessageBox MB_YESNO|MB_DEFBUTTON2|MB_TOPMOST $(STR_Installed) IDNO Quit
	StrCmp $R4 2 Quit +1
	ExecWait '$R3 _?=$INSTDIR' $R5
	StrCmp $R5 0 ReallyNotInstalled Quit
Quit:
	Quit
 
ReallyNotInstalled:
	!insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd
