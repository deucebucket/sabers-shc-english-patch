@echo off
setlocal
title Super Heroine Chronicle - English Patch v3.1
echo.
echo  ==================================================
echo   Super Heroine Chronicle - English Patch v3.1
echo  ==================================================
echo.
set "HERE=%~dp0"
set "TARGET=%~1"
if "%TARGET%"=="" if exist "%HERE%ShcPack.cpk" set "TARGET=%HERE%"
if "%TARGET%"=="" (
  echo  Where is your game's USRDIR folder?
  echo  Tip: open the folder in Explorer, click the address bar, copy it, then
  echo  right-click in this window to paste it.
  echo.
  set /p "TARGET= Paste the USRDIR folder path and press Enter: "
)
set "TARGET=%TARGET:"=%"
if defined TARGET if not "%TARGET:~-1%"=="\" set "TARGET=%TARGET%\"
if not exist "%TARGET%ShcPack.cpk" goto :nocpk
if not exist "%TARGET%hash.csv" goto :nohash
set "X=%HERE%patch_files\xdelta3.exe"
set "P=%HERE%patch_files"

echo  Checking your game files...
call :md5 "%TARGET%ShcPack.cpk" ORIG
if /i "%ORIG%"=="ba93cf943333aec995a00a09b7492b79" (
  echo.
  echo  [OK] This game is ALREADY patched. Nothing to do. Enjoy!
  goto :done
)
if /i not "%ORIG%"=="834351ca822e97d6a24facf01cc5e5f4" (
  echo.
  echo  [X] Your ShcPack.cpk isn't the original Japanese file.
  echo      Expected MD5 834351ca822e97d6a24facf01cc5e5f4
  echo      Yours is     %ORIG%
  echo  Re-copy the original file from your disc dump and run this again.
  goto :fail
)

echo  [OK] Original game found.
echo  Making backups (ShcPack.cpk.original and hash.csv.original)...
if not exist "%TARGET%ShcPack.cpk.original" copy /y "%TARGET%ShcPack.cpk" "%TARGET%ShcPack.cpk.original" >nul || goto :backupfail
if not exist "%TARGET%hash.csv.original" copy /y "%TARGET%hash.csv" "%TARGET%hash.csv.original" >nul || goto :backupfail

echo  Patching, please wait (takes a few seconds)...
"%X%" -d -f -s "%TARGET%ShcPack.cpk.original" "%P%\ShcPack.cpk.xdelta" "%TARGET%ShcPack.cpk" || goto :patchfail
"%X%" -d -f -s "%TARGET%hash.csv.original" "%P%\hash.csv.xdelta" "%TARGET%hash.csv" || goto :patchfail

call :md5 "%TARGET%ShcPack.cpk" NEWMD5
if /i not "%NEWMD5%"=="ba93cf943333aec995a00a09b7492b79" goto :patchfail

echo.
echo  ==================================================
echo   DONE! The game is now in English.
echo  ==================================================
echo   Next: start the game. If it asks to install data,
echo   say yes and let it finish.
goto :done

:patchfail
echo.
echo  [X] Patching failed. Putting your original files back...
copy /y "%TARGET%ShcPack.cpk.original" "%TARGET%ShcPack.cpk" >nul || goto :rollbackfail
copy /y "%TARGET%hash.csv.original" "%TARGET%hash.csv" >nul || goto :rollbackfail
echo  Your game is back the way it was. Nothing was harmed.
goto :fail

:rollbackfail
echo  [!] Couldn't put the originals back automatically.
echo      In USRDIR, rename ShcPack.cpk.original to ShcPack.cpk
echo      and hash.csv.original to hash.csv yourself.
goto :fail

:backupfail
echo  [X] Couldn't make backups. Is the folder read-only, or is the disk full?
goto :fail

:nocpk
echo.
echo  [X] Can't find ShcPack.cpk in:
echo      "%TARGET%"
echo  Make sure you picked the USRDIR folder: SHC\PS3_GAME\USRDIR
goto :fail

:nohash
echo  [X] Can't find hash.csv in that folder. Is this the right game folder?
goto :fail

:md5
set "%2="
for /f "skip=1 delims=" %%h in ('certutil -hashfile "%~1" MD5') do (
  if not defined %2 set "%2=%%h"
)
call set "%2=%%%2: =%%"
exit /b 0

:fail
echo.
echo  Patch NOT installed.
:done
echo.
pause
endlocal
