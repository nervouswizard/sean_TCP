@echo off
REM ===========================================================================
REM  Launcher for preview_pointcloud.py  --  edit the variables below
REM ===========================================================================

REM -- Python from the ComfyUI conda env (has numpy / open3d / matplotlib) -----
set "PYTHON=C:\Users\sean\miniconda3\envs\pointcloud\python.exe"

REM -- PLY file to preview ----------------------------------------------------
set "PLY=%~dp0..\data\point_cloud\lotus2.ply"

REM -- Options ----------------------------------------------------------------
REM  COLOR_MODE : rgb  or  view_id
set "COLOR_MODE=rgb"
set "POINT_SIZE=2.0"
REM  BACKEND : auto  or  open3d  or  matplotlib
set "BACKEND=auto"
set "MAX_POINTS=2000000"
set "BG=0.1,0.1,0.1"
REM  ASPECT : rescale X so width:height matches. 'W:H', 'WxH', or an image
REM           path (uses its pixel size). Leave blank to disable.
@REM set "ASPECT=%~dp0..\data\input\lotus2.png"

REM ===========================================================================
REM  You normally don't need to edit below this line.
REM ===========================================================================
set "SCRIPT=%~dp0preview_pointcloud.py"

set "ASPECT_ARG="
if not "%ASPECT%"=="" set "ASPECT_ARG=--aspect "%ASPECT%""

echo Previewing: %PLY%
echo   color-mode=%COLOR_MODE%  point-size=%POINT_SIZE%  backend=%BACKEND%
echo.

"%PYTHON%" "%SCRIPT%" "%PLY%" ^
    --color-mode %COLOR_MODE% ^
    --point-size %POINT_SIZE% ^
    --backend %BACKEND% ^
    --max-points %MAX_POINTS% ^
    --bg %BG% ^
    %ASPECT_ARG%

echo.
pause
