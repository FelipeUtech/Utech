# Desplegar la Polla Mundial 2026 en Amazon S3

La app es un solo archivo (`polla_mundial_2026.html`). Se publica en un bucket S3
configurado como sitio estático público. Repartes el **link**, no el archivo.

## Opción A — Script automático (recomendado)

Requisitos: tener la [AWS CLI](https://aws.amazon.com/cli/) instalada y configurada
(`aws configure`, con una cuenta que pueda crear buckets).

1. Abre `deploy_s3.sh` y edita arriba `BUCKET` (nombre único en todo AWS, sin
   mayúsculas ni puntos) y `REGION`.
2. Ejecuta:

   ```bash
   bash deploy_s3.sh
   ```

El script crea el bucket, le da acceso público, activa el hosting estático, sube el
HTML como `index.html` y te imprime el link para compartir.

Para **publicar cambios** del HTML más adelante: vuelve a correr el script.

## Opción B — Consola web de AWS (sin CLI)

1. **Crea el bucket**: S3 → *Create bucket*. Nombre único, elige región.
   En *Block Public Access* **desmarca** "Block all public access" y confirma.
2. **Sube el archivo**: entra al bucket → *Upload* → sube `polla_mundial_2026.html`
   y renómbralo a `index.html` (o súbelo ya renombrado).
3. **Hosting estático**: bucket → pestaña *Properties* → *Static website hosting* →
   *Enable* → *Index document* = `index.html` → *Save*.
4. **Política pública**: bucket → *Permissions* → *Bucket policy* → pega (cambia
   `NOMBRE-BUCKET`):

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Sid": "PublicReadGetObject",
       "Effect": "Allow",
       "Principal": "*",
       "Action": "s3:GetObject",
       "Resource": "arn:aws:s3:::NOMBRE-BUCKET/*"
     }]
   }
   ```
5. El **link** sale en *Properties → Static website hosting* (endpoint), o como
   `https://NOMBRE-BUCKET.s3.REGION.amazonaws.com/index.html`.

## Prueba antes de repartir

1. Abre el link, entra con un nombre de prueba.
2. Cambia un marcador → debe decir "✓ Guardado".
3. Tabla → *Actualizar* → aparece tu nombre.
4. Admin (PIN `utech26`) → carga un resultado → el partido se cierra y suma puntos.
5. Verifica que la app de **aportes** sigue intacta (no se tocó `payments`).

## Notas

- La master key de JSONBin va **embebida** en el HTML; al ser un bucket público,
  cualquiera con el link puede descargar el archivo y verla. Es el mismo modelo ya
  aceptado del HTML de aportes. Reparte el link a tu grupo, no lo publiques abierto.
- El link del sitio estático de S3 es **HTTP**; el de objeto
  (`https://...s3.REGION.amazonaws.com/index.html`) es **HTTPS** y suele ser mejor
  para compartir. Si quieres HTTPS sobre el endpoint de sitio o un dominio propio,
  haría falta CloudFront (opcional, no necesario para arrancar).
