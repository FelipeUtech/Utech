; VCS.H
; Version 1.05, 13/November/2003
; Registros del Atari 2600 (TIA y RIOT)

;-------------------------------------------------------------------------------
; RIOT (6532) - RAM, I/O, Timer
;-------------------------------------------------------------------------------

SWCHA   = $0280     ; Puerto A; Joysticks P0 y P1
SWACNT  = $0281     ; Puerto A DDR, joystick control
SWCHB   = $0282     ; Puerto B; Switches de consola
SWBCNT  = $0283     ; Puerto B DDR, switches control
INTIM   = $0284     ; Timer output
INSTAT  = $0285     ; Timer Status

; Leer/Escribir Direcciones

TIM1T   = $0294     ; Timer 1 intervalo
TIM8T   = $0295     ; Timer 8 intervalo
TIM64T  = $0296     ; Timer 64 intervalo
T1024T  = $0297     ; Timer 1024 intervalo

;-------------------------------------------------------------------------------
; TIA - Television Interface Adaptor
;-------------------------------------------------------------------------------

; Direcciones de ESCRITURA

VSYNC   = $00       ; 0000 00x0   Sincronización vertical
VBLANK  = $01       ; xx00 00x0   Vertical blank
WSYNC   = $02       ; ---- ----   Esperar sincronización horizontal
RSYNC   = $03       ; ---- ----   Reset sincronización horizontal
NUSIZ0  = $04       ; 00xx 0xxx   Tamaño jugador/misil 0
NUSIZ1  = $05       ; 00xx 0xxx   Tamaño jugador/misil 1
COLUP0  = $06       ; xxxx xxx0   Color jugador 0
COLUP1  = $07       ; xxxx xxx0   Color jugador 1
COLUPF  = $08       ; xxxx xxx0   Color campo de juego
COLUBK  = $09       ; xxxx xxx0   Color fondo
CTRLPF  = $0A       ; 00xx 0xxx   Control campo de juego
REFP0   = $0B       ; 0000 x000   Reflejar jugador 0
REFP1   = $0C       ; 0000 x000   Reflejar jugador 1
PF0     = $0D       ; xxxx 0000   Campo de juego 0
PF1     = $0E       ; xxxx xxxx   Campo de juego 1
PF2     = $0F       ; xxxx xxxx   Campo de juego 2
RESP0   = $10       ; ---- ----   Reset jugador 0
RESP1   = $11       ; ---- ----   Reset jugador 1
RESM0   = $12       ; ---- ----   Reset misil 0
RESM1   = $13       ; ---- ----   Reset misil 1
RESBL   = $14       ; ---- ----   Reset pelota
AUDC0   = $15       ; 0000 xxxx   Control audio canal 0
AUDC1   = $16       ; 0000 xxxx   Control audio canal 1
AUDF0   = $17       ; 000x xxxx   Frecuencia audio 0
AUDF1   = $18       ; 000x xxxx   Frecuencia audio 1
AUDV0   = $19       ; 0000 xxxx   Volumen audio 0
AUDV1   = $1A       ; 0000 xxxx   Volumen audio 1
GRP0    = $1B       ; xxxx xxxx   Gráfico jugador 0
GRP1    = $1C       ; xxxx xxxx   Gráfico jugador 1
ENAM0   = $1D       ; 0000 00x0   Habilitar misil 0
ENAM1   = $1E       ; 0000 00x0   Habilitar misil 1
ENABL   = $1F       ; 0000 00x0   Habilitar pelota
HMP0    = $20       ; xxxx 0000   Movimiento horizontal jugador 0
HMP1    = $21       ; xxxx 0000   Movimiento horizontal jugador 1
HMM0    = $22       ; xxxx 0000   Movimiento horizontal misil 0
HMM1    = $23       ; xxxx 0000   Movimiento horizontal misil 1
HMBL    = $24       ; xxxx 0000   Movimiento horizontal pelota
VDELP0  = $25       ; 0000 000x   Retraso vertical jugador 0
VDELP1  = $26       ; 0000 000x   Retraso vertical jugador 1
VDELBL  = $27       ; 0000 000x   Retraso vertical pelota
RESMP0  = $28       ; 0000 00x0   Reset misil 0 a jugador 0
RESMP1  = $29       ; 0000 00x0   Reset misil 1 a jugador 1
HMOVE   = $2A       ; ---- ----   Aplicar movimiento horizontal
HMCLR   = $2B       ; ---- ----   Limpiar movimiento horizontal
CXCLR   = $2C       ; ---- ----   Limpiar colisiones

; Direcciones de LECTURA

CXM0P   = $00       ; xx00 0000   Colisión M0-P1, M0-P0
CXM1P   = $01       ; xx00 0000   Colisión M1-P0, M1-P1
CXP0FB  = $02       ; xx00 0000   Colisión P0-PF, P0-BL
CXP1FB  = $03       ; xx00 0000   Colisión P1-PF, P1-BL
CXM0FB  = $04       ; xx00 0000   Colisión M0-PF, M0-BL
CXM1FB  = $05       ; xx00 0000   Colisión M1-PF, M1-BL
CXBLPF  = $06       ; x000 0000   Colisión BL-PF
CXPPMM  = $07       ; xx00 0000   Colisión P0-P1, M0-M1
INPT0   = $08       ; x000 0000   Lectura POT puerto 0
INPT1   = $09       ; x000 0000   Lectura POT puerto 1
INPT2   = $0A       ; x000 0000   Lectura POT puerto 2
INPT3   = $0B       ; x000 0000   Lectura POT puerto 3
INPT4   = $0C       ; x000 0000   Botón joystick 0
INPT5   = $0D       ; x000 0000   Botón joystick 1

; EOF
