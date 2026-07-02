@echo off
REM ===========================================================================
REM  Launcher for depth_to_pointcloud.py  --  edit the variables below
REM ===========================================================================

REM -- Python from the ComfyUI conda env (has numpy / pillow / open3d) --------
set "PYTHON=D:\anaconda3\envs\comfyui\python.exe"

REM -- Input depth image ------------------------------------------------------
set "DEPTH=D:\ncku\sean_TCP\data\DA2\human.png"

REM -- Optional RGB image to colour the points (leave blank to skip) ----------
set "RGB=D:\ncku\sean_TCP\data\input\human.png"

REM -- Output PLY -------------------------------------------------------------
set "OUT=D:\ncku\sean_TCP\data\point_cloud\human_from_depth.ply"

REM -- Options ----------------------------------------------------------------
REM  DEPTH_MODE : inverse (bright=near, DA2/Marigold PNG) or linear (bright=far,
REM               e.g. Marigold-DC .npy converted to an image where 0=near,1=far)
set "DEPTH_MODE=inverse"
set "ZNEAR=1.0"
set "ZFAR=4.0"
set "FOV=60"
REM  STRIDE : sample every Nth pixel (1 = full resolution)
set "STRIDE=1"

REM ===========================================================================
REM  You normally don't need to edit below this line.
REM ===========================================================================
set "SCRIPT=%~dp0depth_to_pointcloud.py"

set "RGB_ARG="
if not "%RGB%"=="" set "RGB_ARG=--rgb "%RGB%""

echo Depth  : %DEPTH%
echo Output : %OUT%
echo   depth-mode=%DEPTH_MODE%  z=[%ZNEAR%,%ZFAR%]  fov=%FOV%  stride=%STRIDE%
echo.

"%PYTHON%" "%SCRIPT%" "%DEPTH%" ^
    -o "%OUT%" ^
    %RGB_ARG% ^
    --depth-mode %DEPTH_MODE% ^
    --z-near %ZNEAR% ^
    --z-far %ZFAR% ^
    --fov %FOV% ^
    --stride %STRIDE%

echo.
pause
