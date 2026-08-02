# Procedimiento: digitalización desde escáner/impresora (sin brew)

**Proyecto:** mementobloom / Administracion_UPN  
**Alcance:** rutina confiable para digitalizar documentos físicos usando herramientas sin `brew` y sin modificar el sistema con SANE/HPLIP.  
**Nota:** este procedimiento prioriza una solución CLI de usuario; solo si no existe, usa fallback manual.

---

## 1. Inventario rápido del escáner

```bash
# Impresoras/escáner registrados en el sistema
lpstat -p -d

# Dispositivos USB detectados
system_profiler SPUSBDataType | grep -i -A20 "HP\|Ink Tank\|scanner"

# Drivers/preferencias de escaneo HP instalados
ls ~/Library/Preferences | grep -i "hp.*scan"
```

Si ves `HP Ink Tank ... series` y preferencias `com.hp.scanModule3`, el escáner está disponible por USB.

---

## 2. Ruta preferida sin brew: `scanlib`

`scanlib` usa `ImageCaptureCore` y escanea sin drivers de terceros ni brew.

Instalación recomendada:

```bash
python3 -m pip install scanlib
```

Uso:

```bash
# Listar escáneres
python3 -m scanlib list

# Escanear a JPEG color 300 DPI
python3 -m scanlib scan \
  -s 0 \
  -o "/ruta/destino/upn_documento_AAAA-MM-DD.jpg" \
  --dpi 300 \
  --color-mode color \
  --format jpeg \
  --jpeg-quality 95
```

**Notas:**
- `-s 0` funciona cuando solo hay un escáner USB listado.
- `scanlib` no soporta PDF en la versión documentada aquí; para PDF usa el fallback.

---

## 3. Ruta alternativa: `node-hp-scan-to` por red

Si el equipo tiene IP local y el escáner está en la misma red, esta herramienta escanea por eSCL.

```bash
npx node-hp-scan-to -a 192.168.18.xxx \
  single-scan \
  -d "/ruta/destino" \
  -p "upn_doc_AAAA-MM-DD" \
  --pdf
```

Limitación conocida: en este equipo, `DiscoveryTree.xml` rompe el parseo con `xml2js`, así que úsala solo si ya validaste ese endpoint en tu modelo.

---

## 4. Fallback manual (sin CLI)

Si ninguna CLI funciona, usa:

```bash
# Abrir app de escaneo HP
open -a "HP Easy Scan"

# O abrir Image Capture
open -a "/System/Applications/Image Capture.app"
```

Guarda el archivo en la carpeta designada y registra la ruta final.

---

## 5. Destino y nomenclatura para Administracion_UPN

Carpeta de digitalizados:

```
/Volumes/Macintosh HD - Datos/otros_proyectos/Administracion_UPN/Documentos_Escaneados/
```

Convención de nombre:

```
upn_documento_AAAA-MM-DD.ext
```

Donde `AAAA-MM-DD` es la fecha del documento o la fecha de digitalización.

---

## 6. Post-escaneo

1. Verifica el archivo generado y tamaño.
2. Si es JPG grande y necesitas PDF, convierte con Preview/Save as PDF.
3. Registra el archivo en el handoff del proyecto UPN.
4. Si el documento requiere OCR posterior, indícalo explícitamente.

---

## 7. Troubleshooting corto

- `python3 -m scanlib list` no muestra nada: confirmar que el escáner está encendido y conectado por USB.
- `Permission denied` / acceso denegado: cerrar `HP Easy Scan` y reintentar; solo una app puede tomar el dispositivo a la vez.
- Escaneo muy lento o trabado: cerrar procesos HP residuales (`HP Scan Request Handler`, `HP Device Monitor`) y reintentar.
- Si aparece XML corrupto en `node-hp-scan-to`: preferir `scanlib` en USB o fallback manual.

---

## Checklist rápida

- [ ] Escáner encendido y conectado
- [ ] App HP/Image Capture cerradas antes de usar CLI
- [ ] `python3 -m scanlib list` responde con 1 dispositivo
- [ ] Archivo guardado en `Documentos_Escaneados/`
- [ ] Nombre respeta `upn_documento_AAAA-MM-DD.ext`
- [ ] Handoff actualizado con ruta y observaciones
