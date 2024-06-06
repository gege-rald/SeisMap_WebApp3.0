import logging
import sqlite3
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score
import itertools
from datetime import datetime

def prfrm_clustering(magnitude_range, depth_range, date_range, sqlite_file, table_name):
    try:
        logging.info("Connecting to SQLite database...")
        conn = sqlite3.connect(sqlite_file)
        query = f"SELECT * FROM {table_name}"
        data = pd.read_sql(query, conn)
        conn.close()
        logging.info("Data loaded successfully.")

        data['Mag'] = pd.to_numeric(data['Mag'], errors='coerce')
        data['Depth'] = pd.to_numeric(data['Depth'], errors='coerce')
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')

        data = data.dropna(subset=['Mag', 'Depth', 'Date'])

        filtered_data = data[
            (data['Mag'] >= magnitude_range['min']) & (data['Mag'] <= magnitude_range['max']) &
            (data['Depth'] >= depth_range['min']) & (data['Depth'] <= depth_range['max']) &
            (data['Date'] >= pd.Timestamp(date_range['start'])) & (data['Date'] <= pd.Timestamp(date_range['end']))
        ]
        logging.info("Data filtered successfully.")

        if filtered_data.empty:
            raise ValueError("No data points found after applying the filtering criteria.")

        lat_long = filtered_data[['Latitude', 'Longitude']].to_numpy()

        min_samples = np.arange(2, 20, step=3)
        epsilons = np.linspace(0.01, 1, num=15)
        combinations = list(itertools.product(epsilons, min_samples))

        def get_scores_and_labels(combinations, X, N):
            scores = []
            all_labels_list = []

            for i, (eps, num_samples) in enumerate(combinations):
                try:
                    dbscan_cluster_model = DBSCAN(eps=eps, min_samples=num_samples).fit(X)
                    labels = dbscan_cluster_model.labels_
                    labels_set = set(labels)
                    num_clusters = len(labels_set)
                    if -1 in labels_set:
                        num_clusters -= 1

                    if (num_clusters < 2) or (num_clusters > 50):
                        scores.append(-10)
                        all_labels_list.append('bad')
                    else:
                        scores.append(silhouette_score(X, labels))
                        all_labels_list.append(labels)
                except:
                    scores.append(-10)
                    all_labels_list.append('error')

            best_index = np.argmax(scores)
            best_parameters = combinations[best_index]
            best_labels = all_labels_list[best_index]
            best_score = scores[best_index]

            return {
                'best_epsilon': best_parameters[0],
                'best_min_samples': best_parameters[1],
                'best_labels': best_labels,
                'best_score': best_score
            }

        best_dict = get_scores_and_labels(combinations, lat_long, len(combinations))

        best_model = DBSCAN(eps=best_dict['best_epsilon'], min_samples=best_dict['best_min_samples']).fit(lat_long)
        filtered_data['y'] = best_dict['best_labels']

        if len(set(best_dict['best_labels'])) <= 1:
            raise ValueError("DBSCAN resulted in a single cluster or no clusters. Adjust parameters and try again.")

        silhouette_scores = []
        dbi_scores = []

        for _ in range(10):
            labels = best_model.labels_
            silhouette_scores.append(silhouette_score(lat_long, labels))
            dbi_scores.append(davies_bouldin_score(lat_long, labels))

        avg_silhouette_score = np.mean(silhouette_scores)
        avg_dbi_score = np.mean(dbi_scores)

        return {
            'best_epsilon': best_dict['best_epsilon'],
            'best_min_samples': best_dict['best_min_samples'],
            'best_labels': best_dict['best_labels'],
            'best_score': best_dict['best_score'],
            'data': filtered_data,
            'avg_silhouette_score': avg_silhouette_score,
            'avg_dbi_score': avg_dbi_score
        }

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise e

# Example usage:
magnitude_range = {'max': 6.0, 'min': 4.0}
depth_range = {'max': 70, 'min': 10}
date_range = {'end': '2021-01-01', 'start': '2020-01-01'}
sqlite_file = 'Python/static/final_earthquake_catalogue.db'
table_name = 'earthquake_database'  # Update with your table name

results = prfrm_clustering(magnitude_range, depth_range, date_range, sqlite_file, table_name)
#print("Clustering Results:", results)