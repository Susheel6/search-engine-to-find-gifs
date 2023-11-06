# -*- coding: utf-8 -*-
"""IR_Final_Project_Code.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Wp4s8RYrGTBi6m2yPN-Z_w043i2iZyWz
"""

pip install -U pandas pinecone-client sentence-transformers tqdm

import IPython.display as display
from IPython.core.interactiveshell import InteractiveShell

InteractiveShell.ast_node_interactivity = "all"

#To obtain the dataset
!wget https://github.com/raingo/TGIF-Release/archive/master.zip

!unzip master.zip

import pandas as pd

#reading the file from the database
file_path = "./TGIF-Release-master/data/tgif-v1.0.tsv"
column_names = ['url', 'description']
df = pd.read_csv(file_path, delimiter='\t', names=column_names)

# display the first five rows of the DataFrame
print(df.head())

pip install pinecone-client

import pinecone

# Connecting to Pinecone Database
pinecone.init(api_key="c96881aa-8613-4a9c-b7c4-16608bf002cf", environment="us-east1-gcp")
Index_name1 = 'gif-search'
# Create index if it does not already exist
if Index_name1 not in pinecone.list_indexes():
    pinecone.create_index(Index_name1, dimension=384, metric="cosine")
# Connect to index
index = pinecone.Index(Index_name1)

from sentence_transformers import SentenceTransformer
import torch

device_type = 'cuda' if torch.cuda.is_available() else 'cpu'
model1 = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
model1.to(device_type)
retriever1 = model1
retriever1.to(device_type)

from tqdm.auto import tqdm

# Uses batches of 64
batch_size = 64
batch_groups = df.groupby(df.index // batch_size)

for batch_idx, (_, batch) in tqdm(enumerate(batch_groups), total=len(df) // batch_size + 1):
    emb1 = retriever1.encode(batch['description'].tolist()).tolist()
    metadata = batch.to_dict(orient='records')
    # Create IDs
    id1 = [str(batch_idx * batch_size + idx) for idx in range(len(batch))]
    records_to_upsert = list(zip(id1, emb1, metadata))
    _ = index.upsert(vectors=records_to_upsert)

# To Check if we have all vectors in the index
index_stats = index.describe_index_stats()

from sklearn.cluster import KMeans
import numpy as np

kmeans = KMeans(n_clusters=10, random_state=42).fit(emb1)
labels = kmeans.labels_

# Compute cluster centroids
centroids = kmeans.cluster_centers_


# Function to search for GIFs in a particular cluster
def search_cluster(query, cluster):
    query_embedding = model1.encode([query])[0]
    similarities = np.dot(centroids, query_embedding) / (np.linalg.norm(centroids, axis=1) * np.linalg.norm(query_embedding))
    closest_cluster_idx = np.argsort(similarities)[-1]
    cluster_embeddings = emb1[labels == closest_cluster_idx]
    distances = np.dot(cluster_embeddings, query_embedding) / (np.linalg.norm(cluster_embeddings, axis=1) * np.linalg.norm(query_embedding))
    indices = np.argsort(distances)[-10:]
    return df.loc[labels == closest_cluster_idx].iloc[indices]['url'].tolist()

def Enter_query_here(query):
    # Generate embeddings for the query
    xq = retriever1.encode(query).tolist()
    # Compute cosine similarity between query and embeddings vectors and return top 10 URls
    xc = index.query(xq, top_k=10,
                    include_metadata=True)
    results = []
    for context in xc['matches']:
        url = context['metadata']['url']
        results.append(url)
    return results

from IPython.display import HTML

def Displayed_query(urls):
    figures = []
    for url in urls:
        figures.append(f'''
            <figure style="display: inline-block; margin: 10px;">
                <img src="{url}" alt="GIF" style="width: 200px; height: 200px;">
            </figure>
        ''')
    return HTML(data=f'''
        <div style="display: flex; flex-flow: row wrap; text-align: center;">
        {''.join(figures)}
        </div>
    ''')

gifs = Enter_query_here("mahesh babu")
Displayed_query(gifs)

from google.colab import drive
drive.mount('/content/drive')

from zipfile import ZipFile
import os

file_paths = []

for root,dictionaries,files in os.walk("/content/drive/MyDrive/Colab Notebooks/IR Final Project Code.ipynb"):
  for filename in files:
    filepath = os.path.join(root, filename)
    file_paths.append(filepath)

with ZipFile("/content/drive/MyDrive/ FinalProjectcode1.zip", 'w') as zip:
    for file in file_paths:
      zip.write(file)