#!/bin/bash
# ============================================
# Script de compilación para Tetris Atari 2600
# ============================================

echo "🎮 Compilando Tetris para Atari 2600..."
echo ""

# Verificar que DASM está instalado
if ! command -v dasm &> /dev/null
then
    echo "❌ ERROR: DASM no está instalado."
    echo ""
    echo "Para instalar DASM:"
    echo "  Ubuntu/Debian: sudo apt-get install dasm"
    echo "  macOS: brew install dasm"
    echo "  Windows: Descarga desde https://dasm-assembler.github.io/"
    echo ""
    exit 1
fi

# Compilar
echo "⚙️  Compilando tetris.asm..."
dasm tetris.asm -f3 -otetris.bin -ltetris.lst -stetris.sym

# Verificar si la compilación fue exitosa
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Compilación exitosa!"
    echo ""
    echo "📁 Archivos generados:"
    echo "  - tetris.bin  (ROM del juego - 4KB)"
    echo "  - tetris.lst  (Listado del código)"
    echo "  - tetris.sym  (Símbolos para depuración)"
    echo ""

    # Mostrar tamaño del ROM
    size=$(ls -lh tetris.bin | awk '{print $5}')
    echo "📊 Tamaño del ROM: $size"
    echo ""

    # Verificar si Stella está instalado
    if command -v stella &> /dev/null
    then
        echo "🎮 Para jugar, ejecuta:"
        echo "  stella tetris.bin"
        echo ""
        echo "¿Quieres jugar ahora? (s/n)"
        read -r respuesta
        if [ "$respuesta" = "s" ] || [ "$respuesta" = "S" ]; then
            stella tetris.bin
        fi
    else
        echo "ℹ️  Para jugar necesitas instalar Stella:"
        echo "  Ubuntu/Debian: sudo apt-get install stella"
        echo "  macOS: brew install stella"
        echo "  Windows: https://stella-emu.github.io/"
        echo ""
        echo "Luego ejecuta: stella tetris.bin"
    fi
else
    echo ""
    echo "❌ Error en la compilación."
    echo "Revisa el archivo tetris.lst para ver los detalles del error."
    exit 1
fi
