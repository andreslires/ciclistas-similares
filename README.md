# Comparador de Perfiles de Ciclistas

Aplicación web para encontrar ciclistas con perfiles similares basándose en sus características de rendimiento.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey)
![Scikit-Learn](https://img.shields.io/badge/Library-Scikit--Learn-orange)
![Render](https://img.shields.io/badge/Deploy-Render-brightgreen)

 * **Live Demo**: [https://ciclistas-similares.onrender.com](https://ciclistas-similares.onrender.com)


## Características

- **Búsqueda inteligente** con autocompletado
- **Algoritmo de similitud avanzado** que combina:
  - Similitud de coseno ponderada (60%)
  - Distancia euclidiana normalizada (25%)
  - Características físicas (15%)
- **Visualización con gráfico radar** para comparar perfiles
- **Filtros por edad** y bonificación por mismo tipo de perfil
- **Interfaz limpia y funcional**

## Tipos de Perfil

- **Sprinter**: Especialista en velocidad punta
- **Escalador**: Experto en montaña
- **Clásicas**: Especialista en pavés y terreno irregular
- **Contrarrelojista**: Experto en crono
- **GC**: Líder de clasificación general
- **Todoterreno**: Versátil en múltiples terrenos

## Instalación

1. Clonar el repositorio

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar la aplicación:
```bash
python app.py
```

4. Abrir en el navegador:
```
http://127.0.0.1:5000
```

## Estructura del Proyecto

```
ciclistas-similares/
├── app.py                 
├── data/
│   └── rider_points.csv   
├── static/
│   ├── app.js            
│   └── styles.css        
└── templates/
    └── index.html       
```

## Tecnologías

- **Backend**: Flask, pandas, numpy, scikit-learn
- **Frontend**: HTML, CSS, JavaScript
- **Algoritmo**: Similitud de coseno, distancia euclidiana, normalización

## Datos

El archivo `rider_points.csv` contiene información de ciclistas con las siguientes características:

- **Name**: Nombre del ciclista
- **Team**: Equipo actual
- **Age, Length, Weight**: Datos físicos
- **AVG**: Promedio general
- **FLT, COB, HLL, MTN, SPR, ITT, GC, OR**: Puntuaciones por especialidad (0-100)

El dataset se ha construido a partir de datos de FirstCycling en 2025.