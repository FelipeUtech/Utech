# 🎮 TETRIS para Atari 2600

¡Un Tetris básico programado especialmente para niños de 8 años!

## 🌟 Características

- ✨ 4 tipos de piezas Tetris
- 🎯 Movimiento con el joystick (izquierda/derecha)
- 🔄 Rotación con el botón del joystick
- 📊 Tablero de 10x20
- 🎨 Colores brillantes y divertidos

## 🛠️ Requisitos

Para compilar y jugar este juego necesitas:

1. **DASM** - El ensamblador para Atari 2600
2. **Stella** - El emulador de Atari 2600

### Instalación de herramientas

#### En Linux/Ubuntu:
```bash
# Instalar DASM
sudo apt-get update
sudo apt-get install dasm

# Instalar Stella
sudo apt-get install stella
```

#### En macOS:
```bash
# Con Homebrew
brew install dasm
brew install stella
```

#### En Windows:
- Descarga DASM de: https://dasm-assembler.github.io/
- Descarga Stella de: https://stella-emu.github.io/

## 🎯 Compilar el juego

### Opción 1: Usar el script (Linux/Mac)
```bash
chmod +x compile.sh
./compile.sh
```

### Opción 2: Compilar manualmente
```bash
dasm tetris.asm -f3 -otetris.bin
```

Si todo va bien, verás un mensaje como:
```
Complete. (0)
```

Y se generará el archivo `tetris.bin`

## 🎮 Jugar

Una vez compilado, ejecuta:

```bash
stella tetris.bin
```

O simplemente arrastra el archivo `tetris.bin` a la ventana de Stella.

## 🕹️ Controles

- **Joystick Izquierda** ⬅️ - Mover pieza a la izquierda
- **Joystick Derecha** ➡️ - Mover pieza a la derecha
- **Botón del Joystick** 🔴 - Rotar la pieza
- La pieza cae automáticamente

## 📚 Para aprender más

Este código está bien comentado para que puedas aprender cómo funciona. Algunos conceptos interesantes:

- **Ensamblador 6502**: El lenguaje del procesador del Atari
- **VSYNC y VBLANK**: Cómo sincronizar con la TV
- **RAM limitada**: ¡Solo 128 bytes para todo!
- **Dibujo línea por línea**: No hay framebuffer, se dibuja en tiempo real

## 🎨 Personalización

Puedes cambiar los colores editando estas líneas en `tetris.asm`:

```asm
COLOR_BG        = $00   ; Negro - Cambia esto por otro color
COLOR_PIECE     = $28   ; Rojo
COLOR_BOARD     = $0E   ; Blanco
COLOR_SCORE     = $1C   ; Amarillo
```

### Tabla de colores del Atari 2600:
- `$00` - Negro
- `$0E` - Blanco
- `$1C` - Amarillo
- `$28` - Rojo
- `$3C` - Rojo brillante
- `$84` - Azul
- `$C4` - Verde
- `$D4` - Verde claro

## 🐛 Solución de problemas

### Error al compilar
- Verifica que DASM esté instalado: `dasm --version`
- Asegúrate de que los archivos `vcs.h` y `macro.h` estén en la misma carpeta

### El juego no se ve bien
- Ajusta la configuración de video en Stella
- Prueba diferentes modos de TV (NTSC/PAL/SECAM)

### El joystick no responde
- En Stella, ve a `Options > Input Settings`
- Configura las teclas del teclado para el joystick

## 🎓 Mejoras futuras

Este es un Tetris básico. Aquí hay ideas para mejorarlo:

1. ✅ Agregar más tipos de piezas
2. ✅ Implementar detección completa de líneas
3. ✅ Agregar niveles de velocidad
4. ✅ Mostrar próxima pieza
5. ✅ Agregar efectos de sonido
6. ✅ Pantalla de Game Over

## 📖 Recursos para aprender

- **Stella Manual**: https://stella-emu.github.io/docs/
- **Atari 2600 Programming**: http://www.randomterrain.com/atari-2600-memories.html
- **8bitworkshop**: https://8bitworkshop.com/ (IDE online para Atari 2600)

## 👨‍👩‍👦 Para padres

Este proyecto es educativo y muestra conceptos fundamentales de programación:
- **Memoria limitada**: Gestión eficiente de recursos
- **Tiempo real**: Sincronización precisa con el hardware
- **Lógica de juego**: Algoritmos y estructuras de datos
- **Bajo nivel**: Comprensión de cómo funciona el hardware

¡Disfruta jugando Tetris en tu Atari 2600! 🎉
