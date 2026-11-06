@echo off
rem Install the xp_hud_overlay mod into the Kronos client. The user launches the game; this script only copies.
setlocal
set "MOD=%~dp0mod"
set "DST=D:\Games\Shrekinator\Call of Duty\cod25\kronos\mods\xp_hud_overlay"
set "OTHER=D:\Games\Shrekinator\Call of Duty\cod25\kronos\mods\xp_hud\lua\zm_hud_post.lua"

tasklist /NH /FI "IMAGENAME eq cod25-cod.exe" 2>nul | find /I "cod25-cod.exe" >nul
if not errorlevel 1 (
  echo REFUSED: cod25-cod.exe is running. Close the game first.
  exit /b 1
)
if not exist "%MOD%\mod.json" (
  echo MISSING: %MOD%\mod.json
  exit /b 1
)

echo Installing xp_hud_overlay -^> %DST%
if exist "%OTHER%" (
  echo.
  echo NOTE: mods\xp_hud carries its own operator bar in zm_hud_post.lua.
  echo       Two copies of this bar load two bars; keep one of the two mods enabled.
)
echo.

rem Renamed 2026-11-06 (D39): the old folder would load a second copy of the bar. It holds only this mod's own files.
set "OLD=D:\Games\Shrekinator\Call of Duty\cod25\kronos\mods\zm_xp_hud"
if exist "%OLD%\mod.json" (
  echo   removing the pre-rename folder: %OLD%
  rmdir /S /Q "%OLD%"
)

if not exist "%DST%" mkdir "%DST%"
if not exist "%DST%\lua" mkdir "%DST%\lua"
if not exist "%DST%\images" mkdir "%DST%\images"
rem v1 shipped this file as zm_hud_post.lua. Leaving it beside the renamed file loads both.
if exist "%DST%\lua\zm_hud_post.lua" (
  echo   removing the stale v1 file name: lua\zm_hud_post.lua
  del /Q "%DST%\lua\zm_hud_post.lua"
)
copy /Y "%MOD%\mod.json" "%DST%\mod.json" >nul
copy /Y "%MOD%\lua\xp_hud_overlay_post.lua" "%DST%\lua\xp_hud_overlay_post.lua" >nul
copy /Y "%MOD%\images\*.png" "%DST%\images\" >nul
if not exist "%DST%\scripts" mkdir "%DST%\scripts"
copy /Y "%MOD%\scripts\xp_hud_overlay_store.gsc" "%DST%\scripts\xp_hud_overlay_store.gsc" >nul

echo   side  file                       bytes   sha256
call :hash "%MOD%\mod.json"                    src  "mod.json"
call :hash "%DST%\mod.json"                    dst  "mod.json"
call :hash "%MOD%\lua\xp_hud_overlay_post.lua"      src  "lua\xp_hud_overlay_post.lua"
call :hash "%DST%\lua\xp_hud_overlay_post.lua"      dst  "lua\xp_hud_overlay_post.lua"
call :hash "%MOD%\scripts\xp_hud_overlay_store.gsc" src  "scripts\xp_hud_overlay_store.gsc"
call :hash "%DST%\scripts\xp_hud_overlay_store.gsc" dst  "scripts\xp_hud_overlay_store.gsc"
for %%f in ("%MOD%\images\*.png") do call :one "%%~ff" src
for %%f in ("%DST%\images\*.png") do call :one "%%~ff" dst
echo.
echo Rollback: delete %DST%
echo Then launch from cod25\KronosLauncher.exe and look for the [XpHudOverlay] lines in the console.
exit /b 0

:one
call :hash "%~1" %~2 "images\%~nx1"
exit /b 0

:hash
set "H="
for /f "skip=1 delims=" %%h in ('certutil -hashfile "%~1" SHA256') do if not defined H set "H=%%h"
set "SZ=0"
for %%z in ("%~1") do set "SZ=%%~zz"
echo   %~2  %~3  %SZ% B  %H:~0,16%
exit /b 0
