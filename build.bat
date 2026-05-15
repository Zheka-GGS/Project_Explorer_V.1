@echo off
REM ============================================================================
REM Project Explorer Pro V1 - PyInstaller Build Script
REM ============================================================================
REM This script compiles the Python application into a standalone Windows EXE

setlocal enabledelayedexpansion

REM Set colors for console output
for /F %%A in ('echo prompt $H ^| cmd') do set "BS=%%A"
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "CYAN=[96m"
set "RESET=[0m"

REM ============================================================================
REM Configuration
REM ============================================================================

set "APP_NAME=ProjectExplorerPro"
set "VERSION=1.0.0"
set "ENTRY_POINT=main.py"
set "ICON=ExplorerV.ico"
set "OUTPUT_DIR=dist"
set "BUILD_DIR=build"

echo.
echo %CYAN%╔════════════════════════════════════════════════════════════════╗%RESET%
echo %CYAN%║  Project Explorer Pro V1 - Build Script (PyInstaller)          ║%RESET%
echo %CYAN%╚════════════════════════════════════════════════════════════════╝%RESET%
echo.

REM ============================================================================
REM Step 1: Check Python Installation
REM ============================================================================

echo %YELLOW%[1/5]%RESET% Перевіряю установку Python...
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo %RED%❌ ERROR: Python не встановлено або недоступний в PATH%RESET%
    echo Будь ласка, встановіть Python з https://www.python.org
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set "PYTHON_VER=%%i"
echo %GREEN%✓ %PYTHON_VER% знайдено%RESET%
echo.

REM ============================================================================
REM Step 2: Check PyInstaller Installation
REM ============================================================================

echo %YELLOW%[2/5]%RESET% Перевіряю PyInstaller...
pyinstaller --version >nul 2>&1
if !errorlevel! neq 0 (
    echo %RED%❌ ERROR: PyInstaller не встановлено%RESET%
    echo.
    echo Встановлюю PyInstaller...
    pip install pyinstaller
    if !errorlevel! neq 0 (
        echo %RED%❌ ERROR: Не вдалось встановити PyInstaller%RESET%
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%i in ('pyinstaller --version') do set "PYINSTALLER_VER=%%i"
echo %GREEN%✓ PyInstaller %PYINSTALLER_VER% готовий%RESET%
echo.

REM ============================================================================
REM Step 3: Verify Dependencies
REM ============================================================================

echo %YELLOW%[3/5]%RESET% Перевіряю залежності (requirements.txt)...
if not exist requirements.txt (
    echo %YELLOW%⚠ WARNING: requirements.txt не знайдено%RESET%
) else (
    echo %GREEN%✓ requirements.txt знайдено%RESET%
    echo Встановлюю залежності...
    pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo %YELLOW%⚠ WARNING: Деякі залежності можуть бути установлені неправильно%RESET%
    )
)
echo.

REM ============================================================================
REM Step 4: Clean Previous Build
REM ============================================================================

echo %YELLOW%[4/5]%RESET% Очищаю попередні білди...
if exist %BUILD_DIR% (
    echo Видаляю %BUILD_DIR%...
    rmdir /s /q %BUILD_DIR% >nul 2>&1
    echo %GREEN%✓ %BUILD_DIR% видалено%RESET%
) else (
    echo %GREEN%✓ %BUILD_DIR% не потребує очищення%RESET%
)

if exist %OUTPUT_DIR% (
    echo Видаляю %OUTPUT_DIR%...
    rmdir /s /q %OUTPUT_DIR% >nul 2>&1
    echo %GREEN%✓ %OUTPUT_DIR% видалено%RESET%
) else (
    echo %GREEN%✓ %OUTPUT_DIR% не потребує очищення%RESET%
)
echo.

REM ============================================================================
REM Step 5: Build EXE
REM ============================================================================

echo %YELLOW%[5/5]%RESET% Компілюю EXE файл...
echo.
echo Команда: pyinstaller --onefile --windowed --icon=%ICON% --name=%APP_NAME% --distpath=%OUTPUT_DIR% --workpath=%BUILD_DIR% %ENTRY_POINT%
echo.

if exist %ICON% (
    echo %GREEN%✓ Іконка %ICON% знайдена%RESET%
    pyinstaller --onefile --windowed --icon=%ICON% --name=%APP_NAME% --distpath=%OUTPUT_DIR% --workpath=%BUILD_DIR% %ENTRY_POINT%
) else (
    echo %YELLOW%⚠ Іконка %ICON% не знайдена, компілюю без іконки...%RESET%
    pyinstaller --onefile --windowed --name=%APP_NAME% --distpath=%OUTPUT_DIR% --workpath=%BUILD_DIR% %ENTRY_POINT%
)

REM ============================================================================
REM Step 6: Check Build Result
REM ============================================================================

echo.
if exist %OUTPUT_DIR%\%APP_NAME%.exe (
    echo %GREEN%╔════════════════════════════════════════════════════════════════╗%RESET%
    echo %GREEN%║  ✅ BUILD УСПІШНО ЗАВЕРШЕНО!                                   ║%RESET%
    echo %GREEN%╚════════════════════════════════════════════════════════════════╝%RESET%
    echo.
    
    REM Get file size
    for %%A in (%OUTPUT_DIR%\%APP_NAME%.exe) do set "FILE_SIZE=%%~zA"
    set /A FILE_SIZE_MB=!FILE_SIZE!/1048576
    
    echo %GREEN%✓ Файл створено:%RESET% %OUTPUT_DIR%\%APP_NAME%.exe
    echo %GREEN%✓ Розмір:%RESET% !FILE_SIZE_MB! MB
    echo %GREEN%✓ Версія:%RESET% %VERSION%
    echo.
    echo Детальна інформація про білд:
    echo   - Тип: Standalone EXE (--onefile)
    echo   - Мережа: Windowed GUI (--windowed)
    echo   - Іконка: %ICON%
    echo   - Точка входу: %ENTRY_POINT%
    echo.
    echo Директорія білду: %OUTPUT_DIR%
    echo.
) else (
    echo %RED%╔════════════════════════════════════════════════════════════════╗%RESET%
    echo %RED%║  ❌ ПОМИЛКА: Білд не завершено успішно!                        ║%RESET%
    echo %RED%╚════════════════════════════════════════════════════════════════╝%RESET%
    echo.
    echo Перевірте:
    echo   - Чи встановлені всі залежності (pip install -r requirements.txt)
    echo   - Чи немає помилок в Python коді (python -m py_compile main.py)
    echo   - Чи присутня іконка файлу (%ICON%)
    echo.
    pause
    exit /b 1
)

echo %CYAN%═══════════════════════════════════════════════════════════════════%RESET%
echo.
echo Наступні кроки:
echo   1. Іконка програми: Копіюйте .ico файл разом з EXE для гарної іконки
echo   2. Запуск: %OUTPUT_DIR%\%APP_NAME%.exe
echo   3. Розповсюдження: Архівуйте %OUTPUT_DIR% папку для користувачів
echo   4. Очищення: Видаліть build/ та dist/ для очищення проекту
echo.
echo %CYAN%═══════════════════════════════════════════════════════════════════%RESET%
echo.
echo Для додаткової інформації, див. документацію:
echo   - IMPLEMENTATION_GUIDE.md - Посібник з впровадження
echo   - README.md - Загальна інформація про проект
echo.

pause

endlocal
