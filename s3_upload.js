#!/usr/bin/env node
/*
 * Sube un archivo a S3 firmando la petición con SigV4 — sin dependencias externas
 * ni AWS CLI (solo Node). Útil cuando hay red a AWS pero no está instalada la CLI.
 *
 * Lee de variables de entorno:
 *   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY   (obligatorias)
 *   AWS_SESSION_TOKEN                           (opcional, para credenciales temporales)
 *   AWS_REGION  (o REGION)                      (def: us-east-1)
 *   BUCKET                                      (obligatoria: bucket existente)
 *   KEY                                         (def: polla.html)
 *   FILE                                        (def: polla_mundial_2026.html)
 *
 * Ejemplo:
 *   BUCKET=mi-bucket REGION=us-east-1 node s3_upload.js
 */
const fs = require("fs");
const https = require("https");
const crypto = require("crypto");

const ak = process.env.AWS_ACCESS_KEY_ID;
const sk = process.env.AWS_SECRET_ACCESS_KEY;
const st = process.env.AWS_SESSION_TOKEN;
const region = process.env.AWS_REGION || process.env.REGION || "us-east-1";
const bucket = process.env.BUCKET;
const key = process.env.KEY || "polla.html";
const file = process.env.FILE || "polla_mundial_2026.html";

function die(m){ console.error("ERROR: " + m); process.exit(1); }
if(!ak || !sk) die("faltan AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY en el entorno.");
if(!bucket) die("falta BUCKET (nombre del bucket existente).");
if(!fs.existsSync(file)) die("no existe el archivo: " + file);

const sha256hex = d => crypto.createHash("sha256").update(d).digest("hex");
const hmac = (k,d) => crypto.createHmac("sha256",k).update(d).digest();

const method = "PUT";
const service = "s3";
const host = `${bucket}.s3.${region}.amazonaws.com`;
const body = fs.readFileSync(file);
const payloadHash = sha256hex(body);
const contentType = "text/html; charset=utf-8";
const cacheControl = "no-cache, max-age=0";

const amzdate = new Date().toISOString().replace(/[:-]|\.\d{3}/g, ""); // YYYYMMDDTHHMMSSZ
const datestamp = amzdate.slice(0, 8);
const canonicalUri = "/" + key.split("/").map(encodeURIComponent).join("/");

const headers = {
  "cache-control": cacheControl,
  "content-type": contentType,
  "host": host,
  "x-amz-content-sha256": payloadHash,
  "x-amz-date": amzdate,
};
if(st) headers["x-amz-security-token"] = st;

const signedKeys = Object.keys(headers).sort();
const canonicalHeaders = signedKeys.map(k => k + ":" + String(headers[k]).trim() + "\n").join("");
const signedHeaders = signedKeys.join(";");
const canonicalRequest = [method, canonicalUri, "", canonicalHeaders, signedHeaders, payloadHash].join("\n");

const algorithm = "AWS4-HMAC-SHA256";
const credScope = `${datestamp}/${region}/${service}/aws4_request`;
const stringToSign = [algorithm, amzdate, credScope, sha256hex(canonicalRequest)].join("\n");

const kDate = hmac("AWS4" + sk, datestamp);
const kRegion = hmac(kDate, region);
const kService = hmac(kRegion, service);
const kSigning = hmac(kService, "aws4_request");
const signature = crypto.createHmac("sha256", kSigning).update(stringToSign).digest("hex");

const authorization = `${algorithm} Credential=${ak}/${credScope}, SignedHeaders=${signedHeaders}, Signature=${signature}`;

const reqHeaders = {
  "Authorization": authorization,
  "Content-Type": contentType,
  "Cache-Control": cacheControl,
  "x-amz-content-sha256": payloadHash,
  "x-amz-date": amzdate,
  "Content-Length": body.length,
};
if(st) reqHeaders["x-amz-security-token"] = st;

const req = https.request({ host, method, path: canonicalUri, headers: reqHeaders }, res => {
  let data = "";
  res.on("data", c => data += c);
  res.on("end", () => {
    if(res.statusCode >= 200 && res.statusCode < 300){
      const link = `https://${host}${canonicalUri}`;
      console.log("OK · publicado.");
      console.log("LINK: " + link);
    } else {
      console.error("FALLÓ (HTTP " + res.statusCode + "):\n" + data);
      process.exit(1);
    }
  });
});
req.on("error", e => die(e.message));
req.write(body);
req.end();
