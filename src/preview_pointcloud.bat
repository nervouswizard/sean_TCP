@echo off
REM ===========================================================================
REM  Launcher for preview_pointcloud.py  --  edit the variables below
REM ===========================================================================

REM -- Python from the ComfyUI conda env (has numpy / open3d / matplotlib) -----
set "PYTHON=D:\anaconda3\envs\comfyui\python.exe"

REM -- PLY file to preview ----------------------------------------------------
set "PLY=D:\ncku\ComfyUI\output\pointcloud_0000.ply"

REM -- Options ----------------------------------------------------------------
REM  COLOR_MODE : rgb  or  view_id
set "COLOR_MODE=rgb"
set "POINT_SIZE=2.0"
REM  BACKEND : auto  or  open3d  or  matplotlib
set "BACKEND=auto"
set "MAX_POINTS=2000000"
set "BG=0.1,0.1,0.1"

REM ===========================================================================
REM  You normally don't need to edit below this line.
REM ===========================================================================
set "SCRIPT=%~dp0preview_pointcloud.py"

echo Previewing: %PLY%
echo   color-mode=%COLOR_MODE%  point-size=%POINT_SIZE%  backend=%BACKEND%
echo.

"%PYTHON%" "%SCRIPT%" "%PLY%" ^
    --color-mode %COLOR_MODE% ^
    --point-size %POINT_SIZE% ^
    --backend %BACKEND% ^
    --max-points %MAX_POINTS% ^
    --bg %BG%

echo.
pause
