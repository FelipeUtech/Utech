; ============================================
; TETRIS BASICO PARA ATARI 2600
; Programado para un niño de 8 años
; ============================================
; Este es un Tetris simplificado con:
; - 4 tipos de piezas
; - Movimiento izquierda/derecha con joystick
; - Botón para rotar
; - Líneas que se borran
; - Puntuación básica
; ============================================

    processor 6502
    include "vcs.h"
    include "macro.h"

; ============================================
; CONSTANTES
; ============================================
BOARD_WIDTH     = 10
BOARD_HEIGHT    = 20
PIECE_SIZE      = 4

; Colores
COLOR_BG        = $00   ; Negro
COLOR_PIECE     = $28   ; Rojo
COLOR_BOARD     = $0E   ; Blanco
COLOR_SCORE     = $1C   ; Amarillo

; ============================================
; VARIABLES EN RAM (128 bytes total!)
; ============================================
    SEG.U variables
    ORG $80

; Posición de la pieza actual
PieceX          ds 1    ; Posición X (0-9)
PieceY          ds 1    ; Posición Y (0-19)
PieceType       ds 1    ; Tipo de pieza (0-3)
PieceRotation   ds 1    ; Rotación (0-3)

; Tablero - 20 filas x 10 columnas = 200 bits
; Usamos 20 bytes (cada byte representa una fila, bits 0-9 para columnas)
Board           ds 20   ; 20 bytes para el tablero

; Puntuación y estado del juego
Score           ds 2    ; Puntuación (2 bytes, BCD)
GameState       ds 1    ; Estado: 0=jugando, 1=game over
FrameCounter    ds 1    ; Contador de frames
DropSpeed       ds 1    ; Velocidad de caída
LinesCleared    ds 1    ; Líneas borradas

; Joystick
JoyOld          ds 1    ; Estado anterior del joystick
ButtonOld       ds 1    ; Estado anterior del botón

; Temporal
Temp            ds 1
Temp2           ds 1

; ============================================
; INICIO DEL PROGRAMA
; ============================================
    SEG code
    ORG $F000

Start:
    SEI
    CLD
    LDX #$FF
    TXS
    LDA #0

    ; Limpiar RAM
ClearRAM:
    STA $80,X
    DEX
    BNE ClearRAM

    ; Inicializar juego
    JSR InitGame

; ============================================
; BUCLE PRINCIPAL
; ============================================
MainLoop:
    ; VSYNC - 3 líneas de sincronización vertical
    LDA #2
    STA VSYNC
    STA WSYNC
    STA WSYNC
    STA WSYNC
    LDA #0
    STA VSYNC

    ; VBLANK - 37 líneas de tiempo de retroceso vertical
    LDA #2
    STA VBLANK
    LDX #37
VBlankLoop:
    STA WSYNC
    DEX
    BNE VBlankLoop

    ; Aquí procesamos la lógica del juego durante VBLANK
    JSR ProcessInput
    JSR UpdateGame

    ; Apagar VBLANK
    LDA #0
    STA VBLANK

    ; ============================================
    ; DIBUJADO DE LA PANTALLA (192 líneas)
    ; ============================================
    LDX #192
DrawScreen:
    ; Color de fondo
    LDA #COLOR_BG
    STA COLUBK

    ; Dibujar algo simple por ahora
    CPX #96
    BCS UpperHalf
    LDA #COLOR_PIECE
    JMP SetColor
UpperHalf:
    LDA #COLOR_BOARD
SetColor:
    STA COLUPF

    STA WSYNC
    DEX
    BNE DrawScreen

    ; OVERSCAN - 30 líneas
    LDA #2
    STA VBLANK
    LDX #30
OverscanLoop:
    STA WSYNC
    DEX
    BNE OverscanLoop

    LDA #0
    STA VBLANK

    JMP MainLoop

; ============================================
; INICIALIZAR JUEGO
; ============================================
InitGame:
    ; Limpiar tablero
    LDX #19
    LDA #0
ClearBoard:
    STA Board,X
    DEX
    BPL ClearBoard

    ; Inicializar valores
    LDA #5
    STA PieceX          ; Centrar pieza
    LDA #0
    STA PieceY          ; Arriba
    STA PieceType
    STA PieceRotation
    STA Score
    STA Score+1
    STA GameState
    STA LinesCleared

    LDA #60             ; Velocidad inicial
    STA DropSpeed

    RTS

; ============================================
; PROCESAR ENTRADA DEL JUGADOR
; ============================================
ProcessInput:
    ; Leer joystick
    LDA SWCHA           ; Joystick del jugador 1

    ; Mover izquierda (bit 6 = 0)
    AND #$40
    BNE NotLeft
    LDA JoyOld
    AND #$40
    BEQ NotLeft         ; Ya estaba presionado

    ; Mover pieza a la izquierda
    DEC PieceX
    LDA PieceX
    BPL NotLeft
    LDA #0
    STA PieceX
NotLeft:

    ; Mover derecha (bit 7 = 0)
    LDA SWCHA
    AND #$80
    BNE NotRight
    LDA JoyOld
    AND #$80
    BEQ NotRight

    ; Mover pieza a la derecha
    INC PieceX
    LDA PieceX
    CMP #BOARD_WIDTH
    BCC NotRight
    LDA #BOARD_WIDTH-1
    STA PieceX
NotRight:

    ; Botón para rotar
    LDA INPT4           ; Botón del joystick
    AND #$80
    BNE NotButton
    LDA ButtonOld
    AND #$80
    BEQ NotButton

    ; Rotar pieza
    INC PieceRotation
    LDA PieceRotation
    AND #$03
    STA PieceRotation
NotButton:

    ; Guardar estado actual
    LDA SWCHA
    STA JoyOld
    LDA INPT4
    STA ButtonOld

    RTS

; ============================================
; ACTUALIZAR LÓGICA DEL JUEGO
; ============================================
UpdateGame:
    ; Incrementar contador de frames
    INC FrameCounter

    ; Verificar si es hora de bajar la pieza
    LDA FrameCounter
    CMP DropSpeed
    BCC NoDropYet

    ; Resetear contador
    LDA #0
    STA FrameCounter

    ; Bajar pieza
    INC PieceY

    ; Verificar si llegó al fondo
    LDA PieceY
    CMP #BOARD_HEIGHT-1
    BCC NoDropYet

    ; Pieza llegó al fondo - crear nueva
    JSR PlacePiece
    JSR CheckLines
    JSR NewPiece

NoDropYet:
    RTS

; ============================================
; COLOCAR PIEZA EN EL TABLERO
; ============================================
PlacePiece:
    ; Simplificado: marcar la posición actual
    LDY PieceY
    LDA Board,Y
    ORA #$01            ; Marcar bit 0
    STA Board,Y
    RTS

; ============================================
; VERIFICAR LÍNEAS COMPLETAS
; ============================================
CheckLines:
    ; Simplificado para esta versión básica
    ; Aquí iría la lógica para detectar líneas completas
    RTS

; ============================================
; CREAR NUEVA PIEZA
; ============================================
NewPiece:
    ; Resetear posición
    LDA #5
    STA PieceX
    LDA #0
    STA PieceY

    ; Tipo aleatorio simple (usar frame counter)
    LDA FrameCounter
    AND #$03
    STA PieceType

    LDA #0
    STA PieceRotation

    RTS

; ============================================
; TABLAS DE DATOS DE PIEZAS
; ============================================
; Cada pieza tiene 4 rotaciones
; Formato simplificado para este ejemplo

PieceData:
    ; Pieza I (línea)
    .byte %00001111, %00000000, %00000000, %00000000
    .byte %00000100, %00000100, %00000100, %00000100

    ; Pieza O (cuadrado)
    .byte %00001100, %00001100, %00000000, %00000000
    .byte %00001100, %00001100, %00000000, %00000000

    ; Pieza T
    .byte %00001110, %00000100, %00000000, %00000000
    .byte %00000100, %00001100, %00000100, %00000000

    ; Pieza L
    .byte %00001110, %00001000, %00000000, %00000000
    .byte %00000110, %00000010, %00000010, %00000000

; ============================================
; VECTORES DE INTERRUPCIÓN
; ============================================
    ORG $FFFC
    .word Start         ; RESET
    .word Start         ; IRQ/BRK
