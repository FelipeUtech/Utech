# 🚀 INICIO RÁPIDO - Tetris en 10 Minutos

¿Quieres ver algo funcionando **YA**? ¡Sigue estos pasos!

## ⏱️ 10 Minutos para tu Primer Tetris

### Minuto 1-2: Preparación
1. Ve a https://scratch.mit.edu
2. Clic en "Crear"
3. Borra el gato (clic derecho > borrar)

### Minuto 3-4: Dibuja tu primera pieza
1. Haz clic en el botón del gato con ➕ (abajo a la derecha)
2. Selecciona "Pintar"
3. Elige la herramienta **Rectángulo** (cuadrado)
4. Dibuja un cuadrado de 4 bloques (como un ➕)
5. Píntalo de **ROJO**

### Minuto 5-7: Programa el movimiento

Arrastra estos bloques desde el panel izquierdo:

```
🎬 Cuando se presione la bandera verde
   └─ por siempre
      ├─ si <tecla (flecha izquierda) presionada?> entonces
      │  └─ cambiar x por (-10)
      │
      ├─ si <tecla (flecha derecha) presionada?> entonces
      │  └─ cambiar x por (10)
      │
      ├─ esperar (0.3) segundos
      └─ cambiar y por (-10)
```

**Cómo encontrar cada bloque:**
- 🎬 "Cuando se presione..." → **Eventos** (amarillo)
- "por siempre" → **Control** (naranja)
- "si ... entonces" → **Control** (naranja)
- "tecla ... presionada?" → **Sensores** (azul claro)
- "cambiar x/y por" → **Movimiento** (azul)
- "esperar" → **Control** (naranja)

### Minuto 8: Haz que vuelva arriba
1. Busca el bloque "ir a x: (0) y: (0)"
2. Cambia y: a **170**
3. Ponlo justo después de "cuando se presione la bandera verde"

### Minuto 9: Añade rotación
Dentro del "por siempre", añade:
```
si <tecla (espacio) presionada?> entonces
   └─ girar (90) grados
   └─ esperar (0.2) segundos
```

### Minuto 10: ¡JUEGA!
1. Haz clic en la **bandera verde** (arriba a la derecha)
2. Usa las flechas ⬅️➡️ para moverte
3. Presiona **ESPACIO** para rotar
4. ¡Observa cómo cae!

---

## 🎯 Código Completo para Copiar

```
Cuando se presione la bandera verde
├─ ir a x: (0) y: (170)
└─ por siempre
   ├─ si <tecla (flecha izquierda) presionada?> entonces
   │  └─ cambiar x por (-10)
   │
   ├─ si <tecla (flecha derecha) presionada?> entonces
   │  └─ cambiar x por (10)
   │
   ├─ si <tecla (espacio) presionada?> entonces
   │  ├─ girar (90) grados
   │  └─ esperar (0.2) segundos
   │
   ├─ si <(posición y) < [-160]> entonces
   │  └─ ir a x: (0) y: (170)
   │
   ├─ esperar (0.3) segundos
   └─ cambiar y por (-10)
```

---

## ✅ Checklist Visual

Usa esto para verificar que tienes todo:

- [ ] Scratch abierto
- [ ] Gato borrado
- [ ] Una pieza dibujada (roja)
- [ ] Bloque "Cuando se presione bandera verde"
- [ ] Bloque "por siempre"
- [ ] Movimiento izquierda/derecha
- [ ] Caída automática (cambiar y por -10)
- [ ] Rotación con espacio
- [ ] Vuelve arriba cuando llega abajo
- [ ] ¡Funciona!

---

## 🎨 Mejora en 5 Minutos Más

### Agrega un Sonido
1. Ve a la pestaña **Sonidos** (arriba)
2. Haz clic en el icono de altavoz
3. Elige "Pop"
4. Vuelve a **Código**
5. Después de "cambiar x por (-10)" agrega:
   ```
   tocar sonido (Pop)
   ```

### Agrega Color de Fondo
1. Haz clic en **Escenario** (abajo a la derecha, junto a los sprites)
2. Ve a **Fondos**
3. Elige **Negro**

### Agrega Puntuación
1. Panel izquierdo → **Variables** (naranja)
2. "Crear una variable"
3. Llámala "Puntos"
4. En tu código, después de "ir a x: 0 y: 170" agrega:
   ```
   cambiar (Puntos) por (10)
   ```

---

## 🆘 Problemas Comunes

### "¡No veo nada!"
→ Haz clic en la pestaña "Disfraces" y verifica que tu pieza tenga color

### "Se mueve muy rápido"
→ En "esperar (0.3) segundos" cambia 0.3 a **1**

### "No rota bien"
→ En la pestaña "Disfraces", haz clic en "Fijar centro del disfraz" y ponlo en el medio

### "Se sale de la pantalla"
→ Agrega después del movimiento:
```
si <(posición x) < [-200]> entonces
   └─ fijar x a (-200)

si <(posición x) > [200]> entonces
   └─ fijar x a (200)
```

---

## 📱 ¿Qué Hacer Después?

Una vez que tienes esto funcionando:

1. **Agrega más piezas** → Crea más sprites con diferentes formas
2. **Cambia colores** → Haz cada pieza de un color diferente
3. **Agrega música** → Busca "Dance" en los sonidos
4. **Haz un fondo bonito** → Pinta un escenario colorido
5. **Invita a alguien a jugar** → Comparte tu juego

---

## 🎓 Siguiente Nivel

Cuando domines esto, ve al archivo **README.md** para:
- Detectar cuando toca el fondo
- Hacer que las piezas se queden
- Borrar líneas completas
- Game Over

---

## 💪 Consejos de Motivación

- **No te rindas**: Todos los programadores cometen errores
- **Experimenta**: Cambia números y ve qué pasa
- **Pide ayuda**: No hay preguntas tontas
- **Celebra**: Cada pequeño logro cuenta
- **Diviértete**: ¡Esto debe ser entretenido!

---

## 📸 Guarda tu Trabajo

**IMPORTANTE**: Guarda frecuentemente

1. Clic en "Archivo" (arriba izquierda)
2. "Guardar ahora"
3. Dale un nombre: "Mi Primer Tetris"

Si tienes cuenta en Scratch:
1. Clic en "Compartir"
2. Ya está guardado en la nube
3. Puedes acceder desde cualquier computadora

---

## 🎮 Controles Finales

| Tecla | Acción |
|-------|--------|
| ⬅️ | Mover izquierda |
| ➡️ | Mover derecha |
| ⬇️ | Bajar rápido (opcional) |
| ESPACIO | Rotar |

---

¡Felicidades! 🎉 Has creado tu primer juego de Tetris.

**Siguiente paso**: Abre `README.md` para hacer el juego completo.

**Recuerda**: Lo importante no es hacerlo perfecto, es hacerlo FUNCIONAR. ✨

¿Listo para el siguiente desafío? ¡Sigue programando! 🚀
