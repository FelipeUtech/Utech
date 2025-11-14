@echo off
REM ============================================
REM Script de compilación para Tetris Atari 2600
REM Para Windows
REM ============================================

echo ========================================
echo   Compilando Tetris para Atari 2600
echo ========================================
echo.

REM Verificar que DASM existe
where dasm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: DASM no esta instalado.
    echo.
    echo Descarga DASM desde: https://dasm-assembler.github.io/
    echo.
    pause
    exit /b 1
)

REM Compilar
echo Compilando tetris.asm...
dasm tetris.asm -f3 -otetris.bin -ltetris.lst -stetris.sym

REM Verificar si la compilación fue exitosa
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Compilacion exitosa!
    echo.
    echo Archivos generados:
    echo   - tetris.bin  ^(ROM del juego - 4KB^)
    echo   - tetris.lst  ^(Listado del codigo^)
    echo   - tetris.sym  ^(Simbolos para depuracion^)
    echo.

    REM Verificar si Stella está instalado
    where stella >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo Para jugar, ejecuta:
        echo   stella tetris.bin
        echo.
        set /p respuesta="Quieres jugar ahora? (s/n): "
        if /i "%respuesta%"=="s" (
            stella tetris.bin
        )
    ) else (
        echo Para jugar necesitas instalar Stella:
        echo   https://stella-emu.github.io/
        echo.
        echo Luego ejecuta: stella tetris.bin
    )
) else (
    echo.
    echo Error en la compilacion.
    echo Revisa el archivo tetris.lst para ver los detalles.
    pause
    exit /b 1
)

echo.
pause
