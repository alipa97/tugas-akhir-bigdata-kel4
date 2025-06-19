import os
from pymongo import MongoClient

# Koneksi ke MongoDB - pakai environment variable
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://bigdatakecil:bigdata04@xtrahera.m7x7qad.mongodb.net/?retryWrites=true&w=majority&appName=xtrahera')
client = MongoClient(MONGODB_URI)

# Akses database
db = client["tugas_bigdata"]

# Akses koleksi
collection_idx = db["idx_transformed_data"]
collection_yfinance_5tahun = db["yfinance_data_lima_tahun"]
collection_yfinance_3tahun = db["yfinance_data_tiga_tahun"]
collection_yfinance_1tahun = db["yfinance_data_satu_tahun"]
collection_yfinance_tahunan = db["yfinance_data_tahunan"]
collection_yfinance_bulanan = db["yfinance_data_bulanan"]
collection_yfinance_harian = db["yfinance_data_harian"]
collection_yfinance_mingguan = db["yfinance_data_mingguan"]
collection_market_news = db["iqplus_market_news"]
collection_stock_news = db["iqplus_stock_news"]