from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.preprocessing import MinMaxScaler, StandardScaler

app = Flask(__name__)


# ---------------------------------
# Configuración y Preprocesamiento
# ---------------------------------

# Definición de características
FEATURES = ['AVG', 'FLT', 'COB', 'HLL', 'MTN', 'SPR', 'ITT', 'GC', 'OR']
SPECIALTY_FEATURES = ['FLT', 'COB', 'HLL', 'MTN', 'SPR', 'ITT', 'GC', 'OR']
PHYSICAL_FEATURES = ['Length', 'Weight', 'Age']

# Carga y Preprocesamiento
df_raw = pd.read_csv('data/rider_points.csv')
df_display = df_raw.copy() # Para mostrar valores reales

# Reemplazar 0s con NaN en características físicas (valores desconocidos)
df_raw['Length'] = df_raw['Length'].replace(0, np.nan) # Altura desconocida
df_raw['Weight'] = df_raw['Weight'].replace(0, np.nan) # Peso desconocido

# Normalización para especialidades
scaler_specialty = MinMaxScaler()
df_scaled = df_raw.copy()
df_scaled[SPECIALTY_FEATURES] = scaler_specialty.fit_transform(df_raw[SPECIALTY_FEATURES])

# Normalización para características físicas (ignorando NaN)
scaler_physical = StandardScaler()
# Calcular media y desv. estándar ignorando NaN
physical_mean = df_raw[PHYSICAL_FEATURES].mean()
physical_std = df_raw[PHYSICAL_FEATURES].std()
# Normalizar manualmente para preservar NaN
for feature in PHYSICAL_FEATURES:
    df_scaled[feature] = (df_raw[feature] - physical_mean[feature]) / physical_std[feature]


# ------------------------------------
# Funciones auxiliares para similitud
# ------------------------------------

# Función para identificar el perfil dominante del ciclista
def identify_rider_profile(rider_data):
    """Identifica el perfil dominante del ciclista"""
    specialty_scores = {
        'Sprinter': rider_data['SPR'],
        'Escalador': (rider_data['MTN'] + rider_data['HLL']) / 2,
        'Clásicas': (rider_data['COB'] + rider_data['FLT'] + rider_data['OR'] + rider_data['HLL']) / 4,
        'Contrarrelojista': rider_data['ITT'],
        'GC': rider_data['GC'],
        'Todoterreno': rider_data['OR']
    }
    return max(specialty_scores, key=specialty_scores.get), max(specialty_scores.values())

# Función para calcular similitud
def calculate_weighted_similarity(rider_vector, all_vectors, rider_strengths):
    """Calcula similitud con pesos dinámicos basados en las fortalezas del ciclista"""
    # Crear pesos: dar más importancia a las especialidades fuertes del ciclista
    # Evitamos que el modelo se enfoque en las debilidades
    weights = np.ones(len(SPECIALTY_FEATURES))
    for i, feature in enumerate(SPECIALTY_FEATURES):
        if rider_strengths[i] > 70:  # Especialidad fuerte
            weights[i] = 2.0
        elif rider_strengths[i] > 50:  # Especialidad media
            weights[i] = 1.5
        else:  # Especialidad débil
            weights[i] = 0.8
    
    # Aplicar pesos
    weighted_rider = rider_vector * weights
    weighted_all = all_vectors * weights
    
    return cosine_similarity(weighted_all, weighted_rider.reshape(1, -1)).flatten()

# Función principal para calcular similitud con múltiples métricas y filtros inteligentes
def calculate_similarity(rider_name, max_results=10):
    """
    Calcula similitud con múltiples métricas y filtros inteligentes
    """
    # Obtener el corredor seleccionado
    rider_row = df_scaled[df_scaled['Name'] == rider_name]
    if rider_row.empty: 
        return None
    
    # Nombre, edad y perfil del ciclista seleccionado
    rider_display = df_display[df_display['Name'] == rider_name].iloc[0]
    rider_age = rider_display['Age']
    rider_profile, profile_score = identify_rider_profile(rider_display)
    
    # Vectores para similitud (corredor seleccionado vs todos los demás)
    rider_vector = rider_row[SPECIALTY_FEATURES].values[0]
    all_vectors = df_scaled[SPECIALTY_FEATURES].values
    
    # 1. Similitud de Coseno Ponderada (60% del score)
    cosine_scores = calculate_weighted_similarity(rider_vector, all_vectors, rider_display[SPECIALTY_FEATURES].values)
    
    # 2. Distancia Euclidiana Inversa Normalizada (25% del score)
    euclidean_dist = euclidean_distances(all_vectors, rider_vector.reshape(1, -1)).flatten()
    max_dist = np.max(euclidean_dist)
    if max_dist > 0:
        euclidean_scores = 1 - (euclidean_dist / max_dist)
    else:
        euclidean_scores = np.ones_like(euclidean_dist)
    
    # 3. Similitud en características físicas (15% del score)
    # Solo considerar si ambos tienen datos disponibles
    physical_rider = rider_row[PHYSICAL_FEATURES].values[0]
    physical_all = df_scaled[PHYSICAL_FEATURES].values
    
    # Inicializar scores de físico con 0.5
    physical_scores = np.full(len(physical_all), 0.5)
    
    # Encontrar características válidas (no NaN) en el ciclista seleccionado
    valid_features = ~np.isnan(physical_rider)
    
    if valid_features.sum() > 0:  # Si hay al menos una característica física disponible
        # Filtrar solo características válidas
        valid_rider_features = physical_rider[valid_features]
        valid_all_features = physical_all[:, valid_features]
        
        # Filtrar registros donde todas las características válidas tienen datos
        has_valid_data = ~np.isnan(valid_all_features).any(axis=1)
        
        if has_valid_data.sum() > 0:  # Si hay registros con datos válidos
            valid_indices = np.where(has_valid_data)[0]
            valid_all_features_clean = valid_all_features[has_valid_data]
            
            # Calcular distancia euclidiana solo con características válidas
            physical_dist = euclidean_distances(
                valid_all_features_clean, 
                valid_rider_features.reshape(1, -1)
            ).flatten()
            # Normalizar distancia física
            max_physical = np.max(physical_dist)
            if max_physical > 0:
                physical_dist_norm = 1 - (physical_dist / max_physical)
            else:
                physical_dist_norm = np.zeros_like(physical_dist)
            physical_scores[valid_indices] = physical_dist_norm
    
    # Calcular score de similitud final combinando las métricas
    combined_scores = (0.60 * cosine_scores + 0.25 * euclidean_scores + 0.15 * physical_scores)
    
    # Crear DataFrame de resultados
    results = df_display.copy()
    results['SimilarityScore'] = combined_scores
    results['CosineScore'] = cosine_scores
    results['PhysicalScore'] = physical_scores
    
    # Filtros inteligentes
    # 1. Excluir al mismo corredor
    results = results[results['Name'] != rider_name]
    
    # 2. Preferir ciclistas con edad similar (±7 años)
    age_diff = np.abs(results['Age'] - rider_age)
    results['AgePenalty'] = np.where(age_diff <= 7, 0, age_diff * 0.01)
    results['SimilarityScore'] = results['SimilarityScore'] - results['AgePenalty']
    
    # 3. Bonificar ligeramente ciclistas del mismo perfil
    results['RiderProfile'] = results.apply(lambda row: identify_rider_profile(row)[0], axis=1)
    results['ProfileBonus'] = np.where(results['RiderProfile'] == rider_profile, 0.03, 0.0)
    results['SimilarityScore'] = results['SimilarityScore'] + results['ProfileBonus']
    
    # 4. Asegurar que el score esté entre 0 y 1
    results['SimilarityScore'] = np.clip(results['SimilarityScore'], 0, 1)
    
    # Ordenar y obtener top resultados
    top_similar = results.sort_values(by='SimilarityScore', ascending=False).head(max_results)
    
    # Calcular razones de similitud
    result_list = []
    for _, row in top_similar.iterrows():
        reasons = []
        
        # Analizar similitudes específicas
        for feat in SPECIALTY_FEATURES:
            diff = abs(rider_display[feat] - row[feat])
            if diff < 10 and rider_display[feat] > 60:
                reasons.append(f"{feat}")
        
        result_list.append({
            **row.to_dict(),
            'MatchReasons': ', '.join(reasons[:3]) if reasons else 'Perfil general',
            'ProfileType': row['RiderProfile']
        })
    
    return result_list, rider_profile


# ----------------------------
# Rutas de la aplicación Flask
# ----------------------------

# Ruta principal para renderizar la página
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para obtener ciclistas
@app.route('/get_riders')
def get_riders():
    riders = sorted(df_raw['Name'].tolist())
    return jsonify({'riders': riders})

# Ruta para búsqueda de ciclistas (con filtro por query)
@app.route('/search_riders')
def search_riders():
    query = request.args.get('query', '')
    
    # Filtrar por query
    filtered_df = df_raw[df_raw['Name'].str.contains(query, case=False, na=False)]
    
    riders = sorted(filtered_df['Name'].tolist())
    return jsonify({'riders': riders})

# Ruta para obtener datos de un ciclista específico y sus similares
@app.route('/get_rider_data')
def get_rider_data():
    name = request.args.get('name')
    selected_rider = df_display[df_display['Name'] == name].iloc[0].to_dict()
    similar_riders, rider_profile = calculate_similarity(name, max_results=10)
    
    # Añadir perfil al ciclista seleccionado
    selected_rider['ProfileType'] = rider_profile
    
    return jsonify({
        'selected': selected_rider,
        'similar': similar_riders,
        'profile': rider_profile
    })

if __name__ == '__main__':
    app.run(debug=True)