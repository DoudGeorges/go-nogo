@REM Édouard Chassé
@REM 2026-04-01
@echo off

set "ENV_NAME=muselsl"
set "PYTHON_VERSION=3.10"
set "CONDA_ROOT="

where conda >nul 2>&1
if not errorlevel 1 goto :conda_ready

call :try_path "C:\Apps\anaconda3"
call :try_path "%ProgramData%\Anaconda3"
call :try_path "%ProgramData%\anaconda3"
call :try_path "%ProgramData%\Miniconda3"
call :try_path "%ProgramData%\miniconda3"
call :try_path "%USERPROFILE%\Anaconda3"
call :try_path "%USERPROFILE%\anaconda3"
call :try_path "%USERPROFILE%\Miniconda3"
call :try_path "%USERPROFILE%\miniconda3"
call :try_path "%LOCALAPPDATA%\Anaconda3"
call :try_path "%LOCALAPPDATA%\anaconda3"
call :try_path "%LOCALAPPDATA%\Miniconda3"
call :try_path "%LOCALAPPDATA%\miniconda3"

if defined CONDA_ROOT goto :conda_ready

echo Conda introuvable.
echo.
echo Installez Anaconda ou Miniconda, puis relancez ce script.
echo.
echo Anaconda : https://www.anaconda.com/download
echo Miniconda : https://docs.conda.io/en/latest/miniconda.html
echo.
pause
exit /b 1

:try_path
if defined CONDA_ROOT exit /b 0
if exist "%~1\condabin\activate.bat" (
    echo Conda dans %~1
    set "CONDA_ROOT=%~1"
    call "%~1\condabin\activate.bat" "%~1"
    exit /b 0
)
if exist "%~1\Scripts\activate.bat" (
    echo Conda dans %~1
    set "CONDA_ROOT=%~1"
    call "%~1\Scripts\activate.bat" "%~1"
    exit /b 0
)
exit /b 0

:conda_ready
call conda env list | findstr /c:"%ENV_NAME%" >nul 2>&1
if not errorlevel 1 goto :env_ready

echo Environnement "%ENV_NAME%" introuvable. Installation en cours...
echo.

call conda create -n %ENV_NAME% python=%PYTHON_VERSION% -y
if errorlevel 1 (
    echo.
    echo Impossible de construire l'environnement "%ENV_NAME%".
    echo Consultez votre espace disque et votre connexion.
    echo.
    pause
    exit /b 1
)

call conda activate %ENV_NAME%
if errorlevel 1 (
    echo.
    echo Activation de l'environnement "%ENV_NAME%" impossible.
    echo.
    pause
    exit /b 1
)

pip install --isolated muselsl
if errorlevel 1 (
    echo.
    echo Installation de muselsl impossible.
    echo Consultez votre connexion.
    echo.
    pause
    exit /b 1
)

echo muselsl disponible.
echo.

:env_ready
if not defined CONDA_ROOT (
    start "muselsl" cmd /k "conda activate %ENV_NAME% && echo Environnement %ENV_NAME% actif. && echo Tapez 'muselsl' pour voir les commandes disponibles."
) else (
    start "muselsl" cmd /k "call %CONDA_ROOT%\condabin\activate.bat %CONDA_ROOT% && conda activate %ENV_NAME% && echo Environnement %ENV_NAME% actif. && echo Tapez 'muselsl' pour voir les commandes disponibles."
)
exit