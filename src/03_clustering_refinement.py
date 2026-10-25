"""
Módulo 03 Refinado: Validación y Refinamiento de Clusters (4 a 6 perfiles)
Reto 1: Perfiles Ciudadanos de Participación (INE / ENCÍVICA 2024)
Equipo: Byte me
"""

import os
import json
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("03_clustering_refinement")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DATASETS = os.path.join(PROJECT_ROOT, "output", "datasets")

def refine_and_validate_clusters():
    logger.info("=== AUDITORÍA Y VALIDACIÓN DE CLUSTERS PARA ENTREGABLES ===")
    fichas_path = os.path.join(OUTPUT_DATASETS, "arquetipos_fichas.json")
    dataset_path = os.path.join(OUTPUT_DATASETS, "dataset_clusters_final.parquet")
    
    assert os.path.exists(fichas_path), f"No se encontró {fichas_path}"
    assert os.path.exists(dataset_path), f"No se encontró {dataset_path}"
    
    with open(fichas_path, "r", encoding="utf-8") as f:
        fichas = json.load(f)
        
    df = pd.read_parquet(dataset_path)
    n_clusters = len(fichas)
    logger.info(f"Número de clusters identificados: {n_clusters}")
    assert 4 <= n_clusters <= 6, f"El número de clusters debe estar entre 4 y 6, se encontraron {n_clusters}"
    
    total_padron = df["ln_2024"].sum()
    logger.info(f"Padrón total analizado (2024): {total_padron:,} electores en {len(df):,} secciones.")
    
    # Enriquecer fichas con metadatos de equipo y lemas cívicos oficiales
    team_metadata = {
        "equipo": "Byte me",
        "convocatoria": "Hackea la Participación: Datos que construyen democracia (CCPC 2009–2024 / ENCÍVICA)",
        "reto": "Reto 1: Perfiles ciudadanos de participación",
        "representante": "Johanan Olivares Gutierrez",
        "integrantes": [
            "Johanan Olivares Gutierrez",
            "Oscar Ariel Cuevas Martinez",
            "Saul Alexis Arias Gonzales"
        ]
    }
    
    lemas_y_factores = {
        0: {
            "lema_civico": "Mujeres al frente: la fuerza organizada que transforma comunidades.",
            "factor_abstencion": "Sobrecarga de trabajo de cuidados y barreras de movilidad vespertina.",
            "icono": "♀"
        },
        1: {
            "lema_civico": "Tu voz en cada periodo: el Congreso y tu municipio deciden tu día a día.",
            "factor_abstencion": "Percepción errónea de irrelevancia de las elecciones intermedias.",
            "icono": "⚖"
        },
        2: {
            "lema_civico": "Tu ciudad es tu decisión: el costo del silencio se paga en servicios.",
            "factor_abstencion": "Desafección cívica, fatiga urbana, jornadas laborales y lejanía de casillas.",
            "icono": "🏙"
        },
        3: {
            "lema_civico": "Tradición que une: el valor de la palabra y el compromiso comunitario.",
            "factor_abstencion": "Distancias físicas en zonas dispersas y barreras de accesibilidad.",
            "icono": "🌱"
        },
        4: {
            "lema_civico": "El futuro no espera: votar es exigir empleo digno, medio ambiente y derechos.",
            "factor_abstencion": "Falta de representación en candidaturas y desconfianza en partidos políticos.",
            "icono": "🚀"
        }
    }
    
    for k, v in fichas.items():
        c_id = int(k)
        v["equipo"] = team_metadata["equipo"]
        if c_id in lemas_y_factores:
            v["lema_civico"] = lemas_y_factores[c_id]["lema_civico"]
            v["factor_abstencion"] = lemas_y_factores[c_id]["factor_abstencion"]
            v["icono"] = lemas_y_factores[c_id]["icono"]
            
    # Guardar versión enriquecida
    with open(fichas_path, "w", encoding="utf-8") as f:
        json.dump(fichas, f, indent=4, ensure_ascii=False)
        
    logger.info("✓ Fichas enriquecidas con lemas cívicos, factores de abstención y metadatos de equipo.")
    return fichas, team_metadata

if __name__ == "__main__":
    refine_and_validate_clusters()
