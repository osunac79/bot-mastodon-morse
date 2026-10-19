# 🎬🔤 Bot de Morse para Mastodon

Bot que enseña código morse usando títulos de cine (ciencia ficción, terror
y películas frikis) como contenido. Funciona en GitHub Actions, sin
necesidad de servidor ni Raspberry Pi — igual que tu bot del tiempo.

## Cómo funciona

- **09:00** → publica la **lección** del día (letras nuevas + rankings de ayer)
- **18:00** → publica el **quiz** (audio en morse) y abre la ventana de respuestas
- Cada **20 min** → revisa menciones y anota puntos a quien acierte

Todo el estado (títulos usados, ranking, quiz activo) se guarda en la
carpeta `data/` dentro del propio repositorio.

## Puesta en marcha (paso a paso)

### 1. Crear el repositorio en GitHub
Sube esta carpeta a un repo nuevo (puede ser privado).

### 2. Conseguir las claves necesarias

**Mastodon** (token de acceso de tu app):
1. En tu instancia de Mastodon → Ajustes → Desarrollo → Nueva aplicación.
2. Dale permisos de lectura y escritura.
3. Copia el "Access Token" que te genera.

**TMDb** (clave gratuita para buscar películas):
1. Crea una cuenta en https://www.themoviedb.org
2. Ve a Ajustes → API → solicita una clave (API Key v3).

### 3. Configurar los "Secrets" en GitHub
En tu repo: Settings → Secrets and variables → Actions → New repository secret.
Añade estos tres:

| Nombre | Valor |
|---|---|
| `MASTODON_ACCESS_TOKEN` | el token que copiaste de Mastodon |
| `TMDB_API_KEY` | tu clave de TMDb |

Y edita `config.yaml` para poner tu `base_url` (la URL de tu instancia,
ej. `https://mastodon.social`).

### 4. Dar permisos de escritura al workflow
El bot hace `git push` para guardar su propio estado (rankings, títulos
usados). Para que pueda hacerlo:
- Settings → Actions → General → "Workflow permissions" → marca
  **"Read and write permissions"**.

### 5. Probarlo manualmente
En la pestaña **Actions** de tu repo verás los tres workflows
(`Lección de morse`, `Quiz de morse`, `Revisar menciones`). Puedes
lanzarlos a mano con el botón **"Run workflow"** antes de esperar al cron,
para comprobar que todo funciona.

## Editar el bot a tu gusto

Todo lo que normalmente querrás cambiar está en **`config.yaml`**, sin
tocar código:

- `contenido.generos` — añade o quita géneros (usa los nombres en inglés
  tal como los usa TMDb: "Science Fiction", "Horror", "Comedy"...)
- `contenido.palabras_clave` — para afinar el filtro "friki/culto"
- `audio.wpm` — velocidad del pitido morse
- `audio.formato` — `mp3` u `ogg`
- `niveles` — qué letras se desbloquean en cada nivel y en qué orden
- `mastodon.max_caracteres` — límite de caracteres de tu instancia (por
  defecto 500). Si tu instancia permite más, súbelo aquí y el toot de la
  lección aprovechará el espacio extra automáticamente; si el límite es
  muy bajo, el bot recorta primero el ranking total, luego el de ayer,
  antes de arriesgarse a que la publicación falle.

Para editarlo desde el móvil vía SSH: `nano config.yaml`, guardas con
`Ctrl+O`, `Enter`, `Ctrl+X`, y haces `git add . && git commit -m "ajuste" && git push`.

## Estructura del proyecto

```
morse-bot/
├── config.yaml              ← toda la configuración editable
├── requirements.txt
├── src/
│   ├── morse.py              ← traducción texto <-> morse
│   ├── niveles.py             ← progresión de letras/niveles
│   ├── estado.py               ← lectura/escritura de data/*.json
│   ├── contenido.py             ← búsqueda de títulos en TMDb
│   ├── audio.py                  ← generación del audio morse (mp3/ogg)
│   └── mastodon_client.py         ← publicar toots / leer menciones
├── scripts/
│   ├── leccion.py             ← workflow de la mañana
│   ├── quiz.py                 ← workflow de la tarde
│   └── revisar_menciones.py     ← workflow cada 20 min
├── data/                      ← estado persistente (se auto-genera)
└── .github/workflows/          ← los tres crons de GitHub Actions
```

## Notas / próximos pasos posibles

- De momento el contenido es solo títulos de película. La estructura
  está preparada para añadir actores o frases icónicas más adelante
  sin rediseñar nada.
- Los signos de puntuación en morse (¿ ! " etc.) no están soportados
  todavía — quedan como posible "nivel avanzado" futuro.
- El filtrado por década (`contenido.decadas`) está preparado en la
  configuración pero aún no implementado en la consulta a TMDb.
