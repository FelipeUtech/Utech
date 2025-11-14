; MACRO.H
; Version 1.06, 05/SEP/2020
; Macros útiles para programación de Atari 2600

;-------------------------------------------------------------------------------
; SLEEP - Esperar N ciclos
;-------------------------------------------------------------------------------
        MAC SLEEP
            IF {1} = 1
                ECHO "ERROR: SLEEP no puede ser 1"
                ERR
            ENDIF
            IF {1} & 1
                nop
                REPEAT ({1}-3)/2
                    nop
                REPEND
            ELSE
                REPEAT ({1})/2
                    nop
                REPEND
            ENDIF
        ENDM

;-------------------------------------------------------------------------------
; VERTICAL_SYNC - Rutina estándar de sincronización vertical
;-------------------------------------------------------------------------------
        MAC VERTICAL_SYNC
            LDA #2
            STA WSYNC
            STA VSYNC
            STA WSYNC
            STA WSYNC
            LSR
            STA VSYNC
        ENDM

;-------------------------------------------------------------------------------
; VERTICAL_BLANK - Tiempo de retroceso vertical
;-------------------------------------------------------------------------------
        MAC VERTICAL_BLANK
            LDX #37
.LoopVBlank
            STA WSYNC
            DEX
            BNE .LoopVBlank
        ENDM

;-------------------------------------------------------------------------------
; CLEAN_START - Inicialización limpia de la máquina
;-------------------------------------------------------------------------------
        MAC CLEAN_START
            SEI
            CLD
            LDX #$FF
            TXS
            LDA #0
.Clear
            STA 0,X
            DEX
            BNE .Clear
        ENDM

;-------------------------------------------------------------------------------
; BOUNDARY - Verificar alineación de página
;-------------------------------------------------------------------------------
        MAC BOUNDARY
            IF (* & $FF) > {1}
                ALIGN 256
            ENDIF
        ENDM

;-------------------------------------------------------------------------------
; SET_POINTER - Establecer puntero de 16 bits
;-------------------------------------------------------------------------------
        MAC SET_POINTER
            LDA #<{2}
            STA {1}
            LDA #>{2}
            STA {1}+1
        ENDM

; EOF
