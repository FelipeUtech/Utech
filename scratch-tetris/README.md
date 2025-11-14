# 🎮 TETRIS en Scratch

¡Un Tetris divertido y colorido para crear en Scratch! Perfecto para niños de 8 años.

## 🌟 ¿Qué es Scratch?

Scratch es un lenguaje de programación visual creado por MIT. ¡Es perfecto para aprender a programar jugando!

- 🎨 **Visual**: Arrastras bloques como si fueran LEGO
- 🎮 **Divertido**: Creas juegos y animaciones
- 🌈 **Colorido**: Todo es muy visual y atractivo
- 🆓 **Gratis**: Completamente gratuito

## 🚀 Comenzar

### Opción 1: Online (Recomendado)
1. Ve a https://scratch.mit.edu
2. Haz clic en "Crear" (botón azul arriba)
3. ¡Listo! Ya puedes empezar a programar

### Opción 2: Offline
1. Descarga Scratch desde: https://scratch.mit.edu/download
2. Instala en tu computadora
3. Abre la aplicación

## 🎯 Crear el Tetris - Guía Paso a Paso

### Paso 1: Preparar el Escenario 🎨

1. **Elimina el gato**: Haz clic derecho en el gato y selecciona "borrar"
2. **Pinta el fondo**:
   - Haz clic en "Escenario" (abajo a la derecha)
   - Ve a la pestaña "Fondos"
   - Haz clic en "Pintar"
   - Dibuja un rectángulo negro en el centro (este será el tablero)
   - Dibuja líneas para hacer una cuadrícula

### Paso 2: Crear las Piezas (Sprites) 🧩

Vamos a crear las piezas del Tetris. Cada pieza será un "objeto" (sprite).

#### Pieza 1: El Cuadrado (O)
1. Haz clic en el gato con el **+** para crear nuevo sprite
2. Selecciona "Pintar"
3. Dibuja un cuadrado de 2x2 bloques
4. Coloréalo de **amarillo**
5. Nómbralo "PiezaO"

#### Pieza 2: La Línea (I)
1. Crea otro sprite
2. Dibuja una línea de 4 bloques
3. Coloréala de **cyan/azul claro**
4. Nómbrala "PiezaI"

#### Pieza 3: La T
1. Crea otro sprite
2. Dibuja una T
3. Coloréala de **morado**
4. Nómbrala "PiezaT"

#### Pieza 4: La L
1. Crea otro sprite
2. Dibuja una L
3. Coloréala de **naranja**
4. Nómbrala "PiezaL"

#### Pieza 5: La Z
1. Crea otro sprite
2. Dibuja una Z
3. Coloréala de **rojo**
4. Nómbrala "PiezaZ"

### Paso 3: Programar el Movimiento 🎮

Para **CADA PIEZA**, agrega estos bloques:

```scratch
Cuando se presione la bandera verde
└─ ir a x: (0) y: (180)
└─ por siempre
   ├─ si <tecla (flecha izquierda) presionada?> entonces
   │  └─ cambiar x por (-10)
   │
   ├─ si <tecla (flecha derecha) presionada?> entonces
   │  └─ cambiar x por (10)
   │
   ├─ si <tecla (flecha abajo) presionada?> entonces
   │  └─ cambiar y por (-10)
   │
   ├─ si <tecla (espacio) presionada?> entonces
   │  └─ girar (90) grados
   │
   └─ esperar (0.5) segundos
   └─ cambiar y por (-10)
```

**¿Qué hace este código?**
- La pieza empieza arriba
- Se mueve con las flechas
- Baja automáticamente cada 0.5 segundos
- Gira con la barra espaciadora

### Paso 4: Mejorar el Juego 🎯

#### A. Hacer que solo una pieza caiga a la vez

En el **Escenario**, agrega:

```scratch
Cuando se presione la bandera verde
└─ fijar [PiezaActual] a [ninguna]
└─ por siempre
   └─ fijar [PiezaActual] a (número al azar entre (1) y (5))
   └─ esperar (5) segundos
```

#### B. Detectar el fondo

En cada pieza:

```scratch
por siempre
└─ si <posición y < (-140)> entonces
   └─ ir a x: (0) y: (180)
   └─ crear clon de [mí mismo]
```

#### C. Añadir puntuación

En el **Escenario**:

1. Crea una variable llamada "Puntos"
2. Agrega:

```scratch
Cuando se presione la bandera verde
└─ fijar [Puntos] a [0]

cuando reciba [línea completada]
└─ cambiar [Puntos] por (100)
```

### Paso 5: Efectos Especiales ✨

#### Sonidos
1. Ve a la pestaña "Sonidos"
2. Haz clic en el icono de altavoz
3. Selecciona sonidos divertidos:
   - "Pop" para cuando la pieza toca el fondo
   - "Boing" para cuando giras
   - "Cheer" para líneas completadas

Agrega en tu código:
```scratch
cuando toque el suelo
└─ tocar sonido [Pop]
```

#### Efectos visuales
```scratch
cuando se presione la bandera verde
└─ fijar efecto [color] a (0)

cuando reciba [línea completada]
└─ cambiar efecto [color] por (25)
└─ esperar (0.5) segundos
└─ fijar efecto [color] a (0)
```

## 🎨 Versión Simplificada (Más Fácil)

Si el Tetris completo es muy complicado, empieza con esta versión simple:

### Tetris Ultra-Simple

1. **Un solo tipo de pieza**
2. **Solo mueve izquierda/derecha**
3. **Cae automáticamente**

```scratch
Cuando se presione la bandera verde
└─ ir a x: (0) y: (180)
└─ por siempre
   ├─ si <tecla (flecha izquierda) presionada?> entonces
   │  └─ cambiar x por (-10)
   │
   ├─ si <tecla (flecha derecha) presionada?> entonces
   │  └─ cambiar x por (10)
   │
   └─ esperar (0.3) segundos
   └─ cambiar y por (-10)
   └─ si <posición y < (-140)> entonces
      └─ ir a x: (0) y: (180)
```

¡Con solo esto ya tienes un juego básico funcionando!

## 🏆 Ideas para Mejorar

Una vez que tengas lo básico funcionando:

1. ✨ **Más piezas**: Agrega todas las 7 piezas del Tetris original
2. 🎵 **Música de fondo**: Agrega la música clásica de Tetris
3. 📊 **High Score**: Guarda la puntuación más alta
4. 💨 **Niveles**: Aumenta la velocidad cada 10 líneas
5. 👻 **Próxima pieza**: Muestra cuál será la siguiente pieza
6. 🌈 **Efectos de arcoíris**: Cuando completes una línea
7. 💥 **Partículas**: Efectos cuando las piezas caen
8. 🎮 **Botón de pausa**: Para poder descansar

## 📚 Aprender Más sobre Scratch

### Tutoriales recomendados:
- **Scratch.mit.edu/ideas**: Tutoriales oficiales
- **Code.org**: Curso de Scratch gratis
- **YouTube**: Busca "Scratch tutorial español"

### Proyectos para inspirarte:
1. Ve a https://scratch.mit.edu/explore/projects/games/
2. Busca "Tetris"
3. Haz clic en "Ver dentro" para ver cómo otros lo hicieron
4. ¡Aprende de otros programadores!

## 🆘 Ayuda y Problemas Comunes

### "Las piezas se mueven muy rápido"
- Aumenta el tiempo en el bloque "esperar" (prueba con 0.5 o 1 segundo)

### "Las piezas atraviesan el suelo"
- Verifica que la condición `posición y < (-140)` esté bien escrita
- Ajusta el número -140 según dónde esté tu suelo

### "No puedo girar las piezas"
- Asegúrate de que el centro de la pieza esté en el medio
- En el editor de disfraces, usa la herramienta "Fijar centro del disfraz"

### "Las piezas desaparecen"
- Revisa que no estén ocultas con el bloque "mostrar"
- Verifica que estén en la capa correcta

## 🎓 Lo que tu hijo aprenderá

Programando este Tetris aprenderá:

- 🧠 **Lógica**: if/entonces, bucles
- 📐 **Coordenadas**: X, Y, movimiento en el plano
- 🎨 **Creatividad**: Diseño de personajes y fondos
- 🐛 **Debugging**: Encontrar y corregir errores
- 🎯 **Resolución de problemas**: Pensar paso a paso
- 🔄 **Algoritmos**: Secuencias de instrucciones

## 👨‍👩‍👦 Tips para Padres

1. **Deja que experimente**: No importa si se equivoca
2. **Celebra pequeños logros**: Cada bloque que funciona es un éxito
3. **Programa juntos**: Es una actividad familiar divertida
4. **No lo compares**: Cada niño aprende a su ritmo
5. **Fomenta la creatividad**: ¡Que cambie colores, sonidos, lo que quiera!

## 🎉 Compartir el Proyecto

Cuando terminen:

1. Haz clic en "Compartir" (arriba a la derecha)
2. Dale un nombre divertido
3. Añade instrucciones para otros jugadores
4. ¡Compártelo con amigos y familia!

## 📝 Archivo de Referencia

Incluyo un archivo `tetris-bloques.txt` con todos los bloques de código escritos paso a paso.

¡Diviértanse programando! 🎮✨

---

**¿Necesitas ayuda?**
- Scratch tiene una comunidad muy amable
- Puedes hacer preguntas en los foros de Scratch
- ¡O pregúntame a mí! Estoy aquí para ayudar
