#!/usr/bin/env bash
#
# Publica la Polla Mundial 2026 en un bucket S3 QUE YA EXISTE (el mismo del HTML de aportes).
# NO crea el bucket ni cambia su configuración pública: solo sube el archivo como otra ruta,
# para no pisar el index.html / archivo de aportes.
#
# Uso:
#   1) Edita BUCKET, REGION y (si aplica) PROFILE abajo con los datos del bucket de aportes.
#   2) Ejecuta:  bash deploy_s3_bucket_existente.sh
#
# Para republicar cambios del HTML: vuelve a correr el script.
#
set -euo pipefail

# ======================= EDITA ESTO =======================
BUCKET=""                              # <-- nombre EXACTO del bucket existente (el del aportes)
REGION="us-east-1"                     # <-- región de ese bucket
PROFILE=""                             # opcional: perfil AWS (la misma cuenta del aportes). Vacío = por defecto.
SRC="polla_mundial_2026.html"          # archivo fuente en este repo
KEY="polla.html"                       # ruta de publicación (NO uses index.html para no pisar el aportes)
# ==========================================================

[ -n "$PROFILE" ] && export AWS_PROFILE="$PROFILE"

command -v aws >/dev/null 2>&1 || { echo "ERROR: no se encontró la AWS CLI. Instálala: https://aws.amazon.com/cli/"; exit 1; }
[ -n "$BUCKET" ] || { echo "ERROR: define BUCKET con el nombre del bucket existente."; exit 1; }
[ -f "$SRC" ] || { echo "ERROR: no existe $SRC en el directorio actual."; exit 1; }

echo "==> Cuenta AWS:"
aws sts get-caller-identity --output text --query Account

echo "==> Verificando que el bucket '$BUCKET' exista y sea accesible ..."
aws s3api head-bucket --bucket "$BUCKET"

echo "==> Subiendo $SRC como $KEY (sin tocar el resto del bucket) ..."
aws s3 cp "$SRC" "s3://$BUCKET/$KEY" \
  --content-type "text/html; charset=utf-8" \
  --cache-control "no-cache, max-age=0"

HTTPS="https://$BUCKET.s3.$REGION.amazonaws.com/$KEY"
if [ "$REGION" = "us-east-1" ]; then
  WEB="http://$BUCKET.s3-website-us-east-1.amazonaws.com/$KEY"
else
  WEB="http://$BUCKET.s3-website.$REGION.amazonaws.com/$KEY"
fi

echo ""
echo "============================================================"
echo " ¡Listo! La Polla quedó publicada en tu bucket existente."
echo ""
echo "  Link para compartir (HTTPS, recomendado):"
echo "    $HTTPS"
echo ""
echo "  Link de sitio estático (HTTP):"
echo "    $WEB"
echo "============================================================"
echo ""
echo "Tu archivo de aportes NO se tocó. Reparte el LINK, no el .html (lleva la master key adentro)."
