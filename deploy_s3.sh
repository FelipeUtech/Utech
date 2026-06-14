#!/usr/bin/env bash
#
# Despliegue de la Polla Mundial 2026 a Amazon S3 (sitio estático público).
#
# Uso:
#   1) Edita BUCKET y REGION abajo (el BUCKET debe ser único en todo AWS, sin mayúsculas ni puntos).
#   2) Asegúrate de tener la AWS CLI configurada:  aws configure   (o variables AWS_ACCESS_KEY_ID, etc.)
#   3) Ejecuta:  bash deploy_s3.sh
#
# Para volver a publicar cambios del HTML: vuelve a correr el script (re-sube index.html).
#
set -euo pipefail

# ======================= EDITA ESTO =======================
BUCKET="polla-mundial-2026-utech"     # <-- cámbialo si está tomado (debe ser único globalmente)
REGION="us-east-1"                     # <-- región AWS (ej: us-east-1, sa-east-1, us-east-2)
SRC="polla_mundial_2026.html"          # archivo fuente en este repo
# ==========================================================

KEY="index.html"   # nombre con el que se publica (link limpio)

command -v aws >/dev/null 2>&1 || { echo "ERROR: no se encontró la AWS CLI. Instálala: https://aws.amazon.com/cli/"; exit 1; }
[ -f "$SRC" ] || { echo "ERROR: no existe $SRC en el directorio actual."; exit 1; }

echo "==> Cuenta AWS:"
aws sts get-caller-identity --output text --query Account

# 1) Crear el bucket (us-east-1 no admite LocationConstraint)
if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "==> El bucket '$BUCKET' ya existe, se reutiliza."
else
  echo "==> Creando bucket '$BUCKET' en $REGION ..."
  if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
  else
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION"
  fi
fi

# 2) Permitir acceso público (desactivar Block Public Access en el bucket)
echo "==> Habilitando acceso público ..."
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# 3) Política de bucket: lectura pública de los objetos
echo "==> Aplicando política de lectura pública ..."
aws s3api put-bucket-policy --bucket "$BUCKET" --policy "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{
    \"Sid\": \"PublicReadGetObject\",
    \"Effect\": \"Allow\",
    \"Principal\": \"*\",
    \"Action\": \"s3:GetObject\",
    \"Resource\": \"arn:aws:s3:::$BUCKET/*\"
  }]
}"

# 4) Activar hosting de sitio estático (documento índice)
echo "==> Activando hosting de sitio estático ..."
aws s3 website "s3://$BUCKET/" --index-document "$KEY" --error-document "$KEY"

# 5) Subir el HTML como index.html con el content-type correcto y sin caché agresivo
echo "==> Subiendo $SRC como $KEY ..."
aws s3 cp "$SRC" "s3://$BUCKET/$KEY" \
  --content-type "text/html; charset=utf-8" \
  --cache-control "no-cache, max-age=0"

# 6) Mostrar los links
if [ "$REGION" = "us-east-1" ]; then
  WEB="http://$BUCKET.s3-website-us-east-1.amazonaws.com"
else
  WEB="http://$BUCKET.s3-website.$REGION.amazonaws.com"
fi
HTTPS="https://$BUCKET.s3.$REGION.amazonaws.com/$KEY"

echo ""
echo "============================================================"
echo " ¡Listo! La Polla quedó publicada."
echo ""
echo "  Link para compartir (HTTPS, recomendado):"
echo "    $HTTPS"
echo ""
echo "  Link de sitio estático (HTTP):"
echo "    $WEB"
echo "============================================================"
echo ""
echo "Reparte el LINK, nunca el archivo .html (lleva la master key adentro)."
