# Torah Translations

Sistema de flashcards para aprendizaje de vocabulario hebreo-español con transliteraciones. Este proyecto utiliza GitHub Pages para servir estáticamente archivos JSON generados desde CSV.

## 📁 Estructura del Proyecto

```
torah_translations/
├── texts/                  # Archivos CSV fuente con traducciones
│   ├── genesis/
│   │   ├── bereshit.csv
│   │   └── noah.csv
│   └── exodus/
│       └── shemot.csv
├── public/                 # Archivos estáticos (HTML, CSS, JS)
│   └── index.html
├── scripts/                # Scripts de generación
│   └── generate-flashcards.js
├── dist/                   # Archivos generados (ignorados en git)
│   ├── index.json         # Índice con metadata
│   └── [estructura igual a texts pero con .json]
└── .github/workflows/      # GitHub Actions
    └── deploy.yml
```

## 🚀 Uso

### Agregar Nuevas Traducciones

1. Crea o edita archivos CSV en la carpeta `texts/`
2. Formato del CSV:
   ```csv
   hebrew,transliteration,spanish
   בְּרֵאשִׁית,Bereshit,En el principio
   בָּרָא,bara,creó
   ```

3. Los archivos se organizan por libro/sección en subcarpetas

### Generación Local

```bash
# Instalar dependencias
npm install

# Generar archivos JSON
npm run build
```

Los archivos generados se crearán en la carpeta `dist/`:
- `index.json` - Metadatos de todos los archivos
- Archivos `.json` - Flashcards individuales por tema

### Despliegue Automático

El proyecto usa GitHub Actions para:
1. Detectar cambios en el branch `main`
2. Ejecutar el script de generación
3. Desplegar automáticamente a GitHub Pages

## 📚 Formato de Datos

### Archivo CSV de Entrada
```csv
hebrew,transliteration,spanish
בְּרֵאשִׁית,Bereshit,En el principio
בָּרָא,bara,creó
```

### Archivo JSON de Salida
```json
[
  {
    "hebrew": "בְּרֵאשִׁית",
    "transliteration": "Bereshit",
    "spanish": "En el principio"
  },
  {
    "hebrew": "בָּרָא",
    "transliteration": "bara",
    "spanish": "creó"
  }
]
```

### Índice (index.json)
```json
{
  "generatedAt": "2025-11-23T04:32:00.000Z",
  "files": [
    {
      "source": "genesis/bereshit.csv",
      "output": "genesis/bereshit.json",
      "cardCount": 7,
      "book": "genesis"
    }
  ]
}
```

## 🌐 GitHub Pages

Una vez desplegado, el sitio estará disponible en:
`https://[usuario].github.io/torah_translations/`

La página principal muestra:
- Lista de todos los libros y archivos
- Cantidad de flashcards por archivo
- Enlaces directos a los archivos JSON

## 🛠️ Desarrollo

### Requisitos
- Node.js 20 o superior
- npm

### Scripts Disponibles
- `npm run build` - Genera archivos JSON desde CSV

## 📝 Licencia

ISC