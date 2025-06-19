import os
from flask import Flask, jsonify, render_template, request
# from pymongo import MongoClient
from dbconfig import collection_yfinance_5tahun, collection_yfinance_3tahun, collection_yfinance_1tahun, collection_yfinance_tahunan, collection_yfinance_bulanan, collection_yfinance_mingguan, collection_yfinance_harian, collection_idx, collection_market_news, collection_stock_news
from bson.json_util import dumps
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

app = Flask(__name__)

@app.route("/")
def index():
    # return render_template("yfinance/5y.html")
    return render_template('idx/top_revenue.html', active_page='idx')

@app.route('/idx')
def idx():
    return render_template('idx/index.html', active_page='idx')

# Route untuk halaman top revenue
@app.route('/idx/top-revenue')
def idx_top_revenue():
    return render_template('idx/top_revenue.html', active_page='idx')

# API untuk ambil data yang akan dipakai di grafik
@app.route("/api/emiten")
def get_emiten():
    data = collection_idx.find({}, {
        "_id": 0,
        "emiten": 1,
        "calculated_ratios.debt_to_equity": 1,
        "calculated_ratios.return_on_assets": 1,
        "calculated_ratios.return_on_equity": 1,
        "calculated_ratios.cash_to_assets_ratio": 1,
        "data_quality.financial_health_score": 1
    })
    return jsonify(list(data))

# API untuk mengambil 5 emiten dengan revenue tertinggi
@app.route("/api/top-revenue")
def get_top_revenue():
    # Ambil parameter tahun dari query string, default ke 2021 jika tidak ada
    year = int(request.args.get('year', 2021))
    
    # Dictionary untuk mapping sektor
    sector_mapping = {
        '1. Agriculture': 'D. Consumer Non-Cyclicals',
        '2. Mining': 'A. Energy',
        # ... (kode mapping sektor lainnya)
    }
    
    # Ambil 5 emiten dengan revenue tertinggi berdasarkan current_year
    pipeline = [
        {"$match": {
            "revenue.current_year": {"$exists": True, "$ne": None},
            "reporting_year": year
        }},
        # Group berdasarkan company_code untuk menghindari duplikasi
        {"$group": {
            "_id": "$company_code",
            "emiten": {"$first": "$emiten"},
            "company_code": {"$first": "$company_code"},
            "sector": {"$first": "$sector"},
            "revenue": {"$first": "$revenue"},
            "reporting_year": {"$first": "$reporting_year"}
        }},
        {"$sort": {"revenue.current_year": -1}},
        {"$limit": 5},
        {"$project": {
            "_id": 0,
            "emiten": 1,
            "company_code": 1,
            "sector": 1,
            "revenue.current_year": 1,
            "revenue.growth_rate_percent": 1,
            "reporting_year": 1
        }}
    ]
    
    top_emiten = list(collection_idx.aggregate(pipeline))
    
    # Terapkan mapping sektor untuk hasil
    for item in top_emiten:
        if item['sector'] in sector_mapping:
            item['original_sector'] = item['sector']
            item['sector'] = sector_mapping[item['sector']]
    
    # Mendapatkan daftar tahun unik untuk dropdown
    distinct_years = sorted(collection_idx.distinct("reporting_year"))
    
    return jsonify({
        "data": top_emiten,
        "years": distinct_years
    })


@app.route('/idx/financial-ratios')
def idx_financial_ratios():
    return render_template('idx/financial_ratios.html', active_page='idx')

# Route untuk halaman Long-Term Borrowing
@app.route('/idx/long-term-borrowing')
def idx_long_term_borrowing():
    return render_template('idx/long_term_borrowing.html', active_page='idx')

# Route untuk halaman Equity Trend
@app.route('/idx/equity-trend')
def idx_equity_trend():
    return render_template('idx/equity_trend.html', active_page='idx')


# API untuk mendapatkan top 5 emiten berdasarkan growth rate
@app.route("/api/top-growth")
def get_top_growth():
    # Ambil parameter tahun dari query string, default ke 2021 jika tidak ada
    year = int(request.args.get('year', 2021))
    
    # Dictionary untuk mapping sektor
    sector_mapping = {
        '1. Agriculture': 'D. Consumer Non-Cyclicals',
        '2. Mining': 'A. Energy',
        '3. Basic Industry And Chemicals': 'B. Basic Materials',
        '4. Miscellaneous Industry': 'C. Industrials',
        '5. Consumer Goods Industry': 'D. Consumer Non-Cyclicals',
        '6. Property, Real Estate And Building Construction': 'H. Properties & Real Estate',
        '7. Infrastructure, Utilities And Transportation': 'J. Infrastructures',
        '8. Finance': 'G. Financials',
        '9. Trade, Services & Investment': 'E. Consumer Cyclicals',
        'B. Basic Materials': 'B. Basic Materials',
        'D. Consumer Non-Cyclicals': 'D. Consumer Non-Cyclicals',
        'E. Consumer Cyclicals': 'E. Consumer Cyclicals',
        'I. Technology': 'I. Technology',
        'J. Infrastructures': 'J. Infrastructures'
    }
    
    # Ambil 5 emiten dengan growth rate tertinggi
    pipeline = [
        {"$match": {
            "revenue.growth_rate_percent": {"$exists": True, "$ne": None},
            "reporting_year": year
        }},
        # Group berdasarkan company_code untuk menghindari duplikasi
        {"$group": {
            "_id": "$company_code",
            "emiten": {"$first": "$emiten"},
            "company_code": {"$first": "$company_code"},
            "sector": {"$first": "$sector"},
            "revenue": {"$first": "$revenue"},
            "reporting_year": {"$first": "$reporting_year"}
        }},
        {"$sort": {"revenue.growth_rate_percent": -1}},
        {"$limit": 5},
        {"$project": {
            "_id": 0,
            "emiten": 1,
            "company_code": 1,
            "sector": 1,
            "revenue.current_year": 1,
            "revenue.prior_year": 1,
            "revenue.growth_rate_percent": 1,
            "reporting_year": 1
        }}
    ]
    
    top_growth = list(collection_idx.aggregate(pipeline))
    
    # Terapkan mapping sektor untuk hasil
    for item in top_growth:
        if item['sector'] in sector_mapping:
            item['original_sector'] = item['sector']
            item['sector'] = sector_mapping[item['sector']]
    
    # Mendapatkan daftar tahun unik untuk dropdown
    distinct_years = sorted(collection_idx.distinct("reporting_year"))
    
    return jsonify({
        "data": top_growth,
        "years": distinct_years
    })

# API untuk mendapatkan data heatmap pertumbuhan laba bersih per sektor
@app.route("/api/profit-growth-heatmap")
def get_profit_growth_heatmap():
    # Dictionary untuk mapping sektor
    sector_mapping = {
        '1. Agriculture': 'D. Consumer Non-Cyclicals',
        '2. Mining': 'A. Energy',
        '3. Basic Industry And Chemicals': 'B. Basic Materials',
        '4. Miscellaneous Industry': 'C. Industrials',
        '5. Consumer Goods Industry': 'D. Consumer Non-Cyclicals',
        '6. Property, Real Estate And Building Construction': 'H. Properties & Real Estate',
        '7. Infrastructure, Utilities And Transportation': 'J. Infrastructures',
        '8. Finance': 'G. Financials',
        '9. Trade, Services & Investment': 'E. Consumer Cyclicals',
        'B. Basic Materials': 'B. Basic Materials',
        'D. Consumer Non-Cyclicals': 'D. Consumer Non-Cyclicals',
        'E. Consumer Cyclicals': 'E. Consumer Cyclicals',
        'I. Technology': 'I. Technology',
        'J. Infrastructures': 'J. Infrastructures'
    }
    
    # Pipeline aggregation untuk menghitung rata-rata pertumbuhan net profit per sektor dan tahun
    pipeline = [
        {"$match": {
            "net_profit.growth_rate_percent": {"$exists": True, "$ne": None}
        }},
        {"$group": {
            "_id": {
                "sector": "$sector",
                "year": "$reporting_year"
            },
            "avg_growth": {"$avg": "$net_profit.growth_rate_percent"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.year": 1, "_id.sector": 1}}
    ]
    
    results = list(collection_idx.aggregate(pipeline))
    
    # Mendapatkan daftar unik sektor dan tahun
    sectors = set()
    years = set()
    
    for result in results:
        sector = result["_id"]["sector"]
        # Map sektor menggunakan dictionary mapping jika ada
        if sector in sector_mapping:
            mapped_sector = sector_mapping[sector]
            sectors.add(mapped_sector)
        else:
            sectors.add(sector)
        
        years.add(result["_id"]["year"])
    
    # Konversi ke list dan urutkan
    sectors_list = sorted(list(sectors))
    years_list = sorted(list(years))
    
    # Membuat data untuk heatmap
    heatmap_data = []
    
    for sector in sectors_list:
        row_data = {"sector": sector}
        
        for year in years_list:
            # Cari data pertumbuhan untuk sektor dan tahun ini
            found = False
            for result in results:
                result_sector = result["_id"]["sector"]
                result_year = result["_id"]["year"]
                
                # Cek apakah perlu dipetakan
                if result_sector in sector_mapping:
                    result_sector = sector_mapping[result_sector]
                
                if result_sector == sector and result_year == year:
                    row_data[str(year)] = round(result["avg_growth"], 2)
                    found = True
                    break
            
            # Jika tidak ada data, isi dengan null
            if not found:
                row_data[str(year)] = None
        
        heatmap_data.append(row_data)
    
    return jsonify({
        "sectors": sectors_list,
        "years": years_list,
        "data": heatmap_data
    })

# API untuk mendapatkan top 5 emiten berdasarkan net profit
@app.route("/api/top-profit")
def get_top_profit():
    # Ambil parameter tahun dari query string, default ke 2021 jika tidak ada
    year = int(request.args.get('year', 2021))
    
    # Dictionary untuk mapping sektor
    sector_mapping = {
        '1. Agriculture': 'D. Consumer Non-Cyclicals',
        '2. Mining': 'A. Energy',
        '3. Basic Industry And Chemicals': 'B. Basic Materials',
        '4. Miscellaneous Industry': 'C. Industrials',
        '5. Consumer Goods Industry': 'D. Consumer Non-Cyclicals',
        '6. Property, Real Estate And Building Construction': 'H. Properties & Real Estate',
        '7. Infrastructure, Utilities And Transportation': 'J. Infrastructures',
        '8. Finance': 'G. Financials',
        '9. Trade, Services & Investment': 'E. Consumer Cyclicals',
        'B. Basic Materials': 'B. Basic Materials',
        'D. Consumer Non-Cyclicals': 'D. Consumer Non-Cyclicals',
        'E. Consumer Cyclicals': 'E. Consumer Cyclicals',
        'I. Technology': 'I. Technology',
        'J. Infrastructures': 'J. Infrastructures'
    }
    
    # Ambil 5 emiten dengan net profit tertinggi berdasarkan current_year
    pipeline = [
        {"$match": {
            "net_profit.current_year": {"$exists": True, "$ne": None},
            "reporting_year": year
        }},
        # Group berdasarkan company_code untuk menghindari duplikasi
        {"$group": {
            "_id": "$company_code",
            "emiten": {"$first": "$emiten"},
            "company_code": {"$first": "$company_code"},
            "sector": {"$first": "$sector"},
            "net_profit": {"$first": "$net_profit"},
            "reporting_year": {"$first": "$reporting_year"}
        }},
        {"$sort": {"net_profit.current_year": -1}},
        {"$limit": 5},
        {"$project": {
            "_id": 0,
            "emiten": 1,
            "company_code": 1,
            "sector": 1,
            "net_profit.current_year": 1,
            "net_profit.growth_rate_percent": 1,
            "reporting_year": 1
        }}
    ]
    
    top_profit = list(collection_idx.aggregate(pipeline))
    
    # Terapkan mapping sektor untuk hasil
    for item in top_profit:
        if item['sector'] in sector_mapping:
            item['original_sector'] = item['sector']
            item['sector'] = sector_mapping[item['sector']]
    
    # Mendapatkan daftar tahun unik untuk dropdown
    distinct_years = sorted(collection_idx.distinct("reporting_year"))
    
    return jsonify({
        "data": top_profit,
        "years": distinct_years
    })

# Route untuk halaman komposisi aset dan ekuitas
@app.route('/idx/asset-equity')
def idx_asset_equity():
    return render_template('idx/asset_equity_composition.html', active_page='idx')

# API untuk mendapatkan data komposisi aset dan ekuitas per sektor
@app.route("/api/asset-equity-composition")
def get_asset_equity_composition():
    # Ambil parameter tahun dari query string
    year = int(request.args.get('year', 2021))
    
    # Dictionary untuk mapping sektor
    sector_mapping = {
        '1. Agriculture': 'D. Consumer Non-Cyclicals',
        '2. Mining': 'A. Energy',
        '3. Basic Industry And Chemicals': 'B. Basic Materials',
        '4. Miscellaneous Industry': 'C. Industrials',
        '5. Consumer Goods Industry': 'D. Consumer Non-Cyclicals',
        '6. Property, Real Estate And Building Construction': 'H. Properties & Real Estate',
        '7. Infrastructure, Utilities And Transportation': 'J. Infrastructures',
        '8. Finance': 'G. Financials',
        '9. Trade, Services & Investment': 'E. Consumer Cyclicals',
        'B. Basic Materials': 'B. Basic Materials',
        'D. Consumer Non-Cyclicals': 'D. Consumer Non-Cyclicals',
        'E. Consumer Cyclicals': 'E. Consumer Cyclicals',
        'I. Technology': 'I. Technology',
        'J. Infrastructures': 'J. Infrastructures'
    }
    
    # Aggregate pipeline untuk menghitung total aset dan ekuitas per sektor
    pipeline = [
        {"$match": {
            "assets.current_year": {"$exists": True, "$ne": None},
            "equity.current_year": {"$exists": True, "$ne": None},
            "reporting_year": year
        }},
        # Group berdasarkan sektor untuk menghitung total
        {"$group": {
            "_id": "$sector",
            "total_assets": {"$sum": "$assets.current_year"},
            "total_equity": {"$sum": "$equity.current_year"},
            "count": {"$sum": 1}
        }},
        # Urutkan berdasarkan total aset
        {"$sort": {"total_assets": -1}},
        # Restruktur output
        {"$project": {
            "_id": 0,
            "sector": "$_id",
            "total_assets": 1,
            "total_equity": 1,
            "count": 1
        }}
    ]
    
    sector_data = list(collection_idx.aggregate(pipeline))
    
    # Mendapatkan daftar tahun unik untuk dropdown
    distinct_years = sorted(collection_idx.distinct("reporting_year"))
    
    # Menerapkan mapping sektor dan menggabungkan data dengan sektor yang sama
    mapped_sector_data = {}
    
    for sector_info in sector_data:
        sector = sector_info['sector']
        # Map sektor jika ada dalam mapping
        if sector in sector_mapping:
            mapped_sector = sector_mapping[sector]
        else:
            mapped_sector = sector
        
        # Jika sektor yang dimapping sudah ada, tambahkan datanya
        if mapped_sector in mapped_sector_data:
            mapped_sector_data[mapped_sector]['total_assets'] += sector_info['total_assets']
            mapped_sector_data[mapped_sector]['total_equity'] += sector_info['total_equity']
            mapped_sector_data[mapped_sector]['count'] += sector_info['count']
        else:
            # Jika belum ada, inisialisasi dengan data sektor ini
            mapped_sector_data[mapped_sector] = {
                'sector': mapped_sector,
                'total_assets': sector_info['total_assets'],
                'total_equity': sector_info['total_equity'],
                'count': sector_info['count']
            }
    
    # Mengkonversi kembali ke list untuk diurutkan
    result_data = list(mapped_sector_data.values())
    # Urutkan hasil berdasarkan total aset
    result_data.sort(key=lambda x: x['total_assets'], reverse=True)
    
    # Hitung rasio equity to assets untuk setiap sektor
    for sector in result_data:
        if sector['total_assets'] > 0:
            sector['equity_to_assets_ratio'] = round(sector['total_equity'] / sector['total_assets'] * 100, 2)
            sector['debt_to_assets_ratio'] = round(100 - sector['equity_to_assets_ratio'], 2)
        else:
            sector['equity_to_assets_ratio'] = 0
            sector['debt_to_assets_ratio'] = 0
    
    return jsonify({
        "data": result_data,
        "years": distinct_years
    })


# API untuk mendapatkan daftar tahun yang tersedia
@app.route("/api/available-years")
def get_available_years():
    distinct_years = sorted(collection_idx.distinct("reporting_year"))
    return jsonify(distinct_years)

# API untuk mendapatkan daftar sektor
@app.route("/api/sectors")
def get_sectors():
    try:
        # Get distinct sectors from database
        sectors = sorted(collection_idx.distinct("sector"))
        return jsonify(sectors)
    except Exception as e:
        # Fallback to hardcoded sectors if database fails
        sectors = [
            'Agriculture',
            'Energy',
            'Basic Materials',
            'Industrials',
            'Consumer Non-Cyclicals',
            'Consumer Cyclicals',
            'Healthcare',
            'Financials',
            'Properties & Real Estate',
            'Technology',
            'Infrastructures',
            'Transportation & Logistic'
        ]
        return jsonify(sectors)

# API untuk mendapatkan daftar tahun
@app.route("/api/years")
def get_years():
    try:
        # Get distinct years from database
        years = sorted(collection_idx.distinct("reporting_year"), reverse=True)
        return jsonify(years)
    except Exception as e:
        # Fallback to hardcoded years if database fails
        years = [2023, 2022, 2021, 2020]
        return jsonify(years)

# API untuk mendapatkan data pertumbuhan sektor
@app.route("/api/sector-growth")
def get_sector_growth():
    # Ambil parameter sektor dari query string
    sector = request.args.get('sector')
    
    # Pipeline agregasi untuk menghitung rata-rata pertumbuhan revenue berdasarkan tahun untuk sektor tertentu
    pipeline = [
        {
            "$match": {
                "sector": {"$regex": sector, "$options": "i"},  # Case insensitive search
                "revenue.growth_rate_percent": {"$ne": None}
            }
        },
        {
            "$group": {
                "_id": "$reporting_year",
                "avg_growth": {"$avg": "$revenue.growth_rate_percent"},
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}  # Urutkan berdasarkan tahun
        }
    ]
    
    sector_data = list(collection_idx.aggregate(pipeline))
    
    # Format data untuk Chart.js
    result = {
        "labels": [str(item["_id"]) for item in sector_data],
        "data": [round(item["avg_growth"], 2) for item in sector_data],
        "counts": [item["count"] for item in sector_data]
    }
    
    return jsonify(result)

# Route untuk halaman tren pertumbuhan sektor
@app.route('/idx/sector-growth')
def idx_sector_growth():
    return render_template('idx/sector_growth.html', active_page='idx')

# Route untuk halaman top growth
@app.route('/idx/top-growth')
def idx_top_growth():
    return render_template('idx/top_growth.html', active_page='idx')

# Route untuk halaman top profit
@app.route('/idx/top-profit')
def idx_top_profit():
    return render_template('idx/top_profit.html', active_page='idx')

# Route untuk halaman revenue gabungan
@app.route('/idx/revenue')
def idx_revenue():
    return render_template('idx/revenue.html', active_page='idx')

# API untuk mendapatkan top 5 emiten dengan DER terendah per sektor
@app.route("/api/top-der")
def get_top_der():
    # Ambil parameter sektor dari query string
    sector = request.args.get('sector')
    year = int(request.args.get('year', 2021))
    
    if not sector:
        return jsonify({"error": "Sector parameter is required"}), 400
    
    # Pipeline aggregation untuk menghitung DER dan mengambil top 5 terendah
    pipeline = [
        {"$match": {
            "sector": {"$regex": sector, "$options": "i"},  # Case insensitive search
            "short_term_borrowing.current_year": {"$exists": True, "$ne": None},
            "long_term_borrowing.current_year": {"$exists": True, "$ne": None},
            "equity.current_year": {"$exists": True, "$ne": None, "$gt": 0}  # Pastikan equity positif untuk menghindari DER negatif
        }},
        # Group berdasarkan company_code untuk menghindari duplikasi
        {"$group": {
            "_id": "$company_code",
            "emiten": {"$first": "$emiten"},
            "company_code": {"$first": "$company_code"},
            "sector": {"$first": "$sector"},
            "short_term_borrowing": {"$first": "$short_term_borrowing.current_year"},
            "long_term_borrowing": {"$first": "$long_term_borrowing.current_year"},
            "equity": {"$first": "$equity.current_year"},
            "reporting_year": {"$first": "$reporting_year"}
        }},
        # Tambahkan field DER dengan perhitungan
        {"$addFields": {
            "der": {
                "$divide": [
                    {"$add": ["$short_term_borrowing", "$long_term_borrowing"]},
                    "$equity"
                ]
            },
            "total_debt": {"$add": ["$short_term_borrowing", "$long_term_borrowing"]}
        }},
        {"$sort": {"der": 1}},  # Urutkan dari terendah (terbaik)
        {"$limit": 5},
        {"$project": {
            "_id": 0,
            "emiten": 1,
            "company_code": 1,
            "sector": 1,
            "calculated_ratios": {
                "debt_to_equity": "$der"  # Agar kompatibel dengan template
            },
            "total_debt": 1, 
            "equity": {"current_year": "$equity"}  # Restruktur untuk kompatibilitas template
        }}
    ]
    
    top_der = list(collection_idx.aggregate(pipeline))
    
    return jsonify(top_der)

# API untuk mendapatkan DER emiten dan rata-rata sektor
@app.route("/api/emiten-der")
def get_emiten_der():
    # Ambil parameter emiten dari query string
    emiten_code = request.args.get('emiten')
    year = int(request.args.get('year', 2021))
    
    if not emiten_code:
        return jsonify({"error": "Emiten parameter is required"}), 400
    
    # Dapatkan data emiten termasuk sektor
    emiten_data = collection_idx.find_one({"company_code": emiten_code, "reporting_year": year})
    
    if not emiten_data:
        return jsonify({"error": "Emiten not found"}), 404
    
    sector = emiten_data.get("sector")
    
    # Hitung DER untuk emiten yang dipilih
    short_term = emiten_data.get("short_term_borrowing", {}).get("current_year", 0) or 0
    long_term = emiten_data.get("long_term_borrowing", {}).get("current_year", 0) or 0
    equity = emiten_data.get("equity", {}).get("current_year", 0) or 0
    
    emiten_der = None
    if equity > 0:
        emiten_der = (short_term + long_term) / equity
    
    # Pipeline aggregation untuk menghitung rata-rata DER sektor
    pipeline = [
        {"$match": {
            "sector": sector,
            "short_term_borrowing.current_year": {"$ne": None},
            "long_term_borrowing.current_year": {"$ne": None},
            "equity.current_year": {"$ne": None, "$gt": 0},  # Pastikan equity positif
            "reporting_year": year
        }},
        # Group berdasarkan company_code untuk menghindari duplikasi
        {"$group": {
            "_id": "$company_code",
            "short_term_borrowing": {"$first": "$short_term_borrowing.current_year"},
            "long_term_borrowing": {"$first": "$long_term_borrowing.current_year"},
            "equity": {"$first": "$equity.current_year"}
        }},
        # Tambahkan field DER dengan perhitungan
        {"$addFields": {
            "der": {
                "$divide": [
                    {"$add": ["$short_term_borrowing", "$long_term_borrowing"]},
                    "$equity"
                ]
            }
        }},
        # Hitung rata-rata DER
        {"$group": {
            "_id": None,
            "avg_der": {"$avg": "$der"},
            "count": {"$sum": 1}
        }}
    ]
    
    sector_result = list(collection_idx.aggregate(pipeline))
    sector_avg_der = sector_result[0]["avg_der"] if sector_result else None
    count_emiten = sector_result[0]["count"] if sector_result else 0
    
    # Mendapatkan daftar tahun unik untuk dropdown
    distinct_years = sorted(collection_idx.distinct("reporting_year"))
    
    # Mendapatkan daftar semua emiten untuk dropdown
    all_emitens = list(collection_idx.find(
        {"company_code": {"$exists": True, "$ne": ""}},
        {"_id": 0, "company_code": 1, "emiten": 1}
    ).distinct("company_code"))
    
    return jsonify({
        "emiten": emiten_code,
        "emiten_name": emiten_data.get("emiten"),
        "sector": sector,
        "emiten_der": emiten_der,
        "sector_avg_der": sector_avg_der,
        "count_emiten_in_sector": count_emiten,
        "years": distinct_years,
        "emitens": all_emitens
    })

# Route untuk halaman DER (Debt to Equity Ratio)
@app.route('/idx/der')
def idx_der():
    return render_template('idx/der.html', active_page='idx')

# API endpoint untuk mengambil semua sektor yang tersedia
@app.route('/api/all-sectors')
def get_all_sectors():
    sectors = collection_idx.distinct("sector")
    # Filter out None values and sort
    sectors = sorted([sector for sector in sectors if sector])
    return jsonify(sectors)

# API endpoint untuk mengambil daftar emiten (untuk dropdown)
@app.route('/api/emiten-list')
def get_emiten_list():
    pipeline = [
        {"$match": {"company_code": {"$exists": True, "$ne": None}}},
        # Group berdasarkan company_code untuk menghindari duplikasi
        {"$group": {
            "_id": "$company_code",
            "emiten": {"$first": "$emiten"},
            "company_code": {"$first": "$company_code"},
            "sector": {"$first": "$sector"}
        }},
        {"$sort": {"company_code": 1}},
        {"$project": {
            "_id": 0,
            "emiten": 1,
            "company_code": 1,
            "sector": 1
        }}
    ]
    
    emiten_list = list(collection_idx.aggregate(pipeline))
    return jsonify(emiten_list)

# API endpoint untuk membandingkan DER emiten dengan rata-rata sektornya
@app.route('/api/compare-der')
def compare_der():
    emiten_code = request.args.get('emiten')
    year = int(request.args.get('year', 2021))
    
    if not emiten_code:
        return jsonify({})
    
    # Ambil data emiten yang dipilih
    emiten_data = collection_idx.find_one({
        "company_code": emiten_code,
        "reporting_year": year,
        "short_term_borrowing.current_year": {"$exists": True},
        "long_term_borrowing.current_year": {"$exists": True},
        "equity.current_year": {"$exists": True, "$gt": 0}
    })
    
    if not emiten_data:
        return jsonify({})
    
    # Ambil sektor dari emiten yang dipilih
    sector = emiten_data.get("sector")
    
    # Hitung DER untuk emiten yang dipilih
    short_term = emiten_data.get("short_term_borrowing", {}).get("current_year", 0) or 0
    long_term = emiten_data.get("long_term_borrowing", {}).get("current_year", 0) or 0
    equity = emiten_data.get("equity", {}).get("current_year", 0) or 0
    
    emiten_der = None
    if equity > 0:
        emiten_der = (short_term + long_term) / equity
    
    # Pipeline aggregation untuk menghitung rata-rata DER sektor
    pipeline = [
        {"$match": {
            "sector": sector,
            "short_term_borrowing.current_year": {"$ne": None},
            "long_term_borrowing.current_year": {"$ne": None},
            "equity.current_year": {"$ne": None, "$gt": 0},  # Pastikan equity positif
            "reporting_year": year
        }},
        # Group berdasarkan company_code untuk menghindari duplikasi
        {"$group": {
            "_id": "$company_code",
            "short_term_borrowing": {"$first": "$short_term_borrowing.current_year"},
            "long_term_borrowing": {"$first": "$long_term_borrowing.current_year"},
            "equity": {"$first": "$equity.current_year"}
        }},
        # Tambahkan field DER dengan perhitungan
        {"$addFields": {
            "der": {
                "$divide": [
                    {"$add": ["$short_term_borrowing", "$long_term_borrowing"]},
                    "$equity"
                ]
            }
        }},
        # Hitung rata-rata DER
        {"$group": {
            "_id": None,
            "avg_der": {"$avg": "$der"},
            "count": {"$sum": 1}
        }}
    ]
    
    sector_der_data = list(collection_idx.aggregate(pipeline))
    
    if not sector_der_data:
        return jsonify({})
    
    sector_avg_der = sector_der_data[0].get("avg_der", 0)
    total_emiten = sector_der_data[0].get("count", 0)
    
    result = {
        "company_code": emiten_code,
        "emiten_name": emiten_data.get("emiten"),
        "sector": sector,
        "emiten_der": emiten_der,
        "sector_avg_der": sector_avg_der,
        "total_emiten": total_emiten
    }
    
    return jsonify(result)

# API untuk mendapatkan top 5 emiten dengan aset terbesar per sektor
@app.route("/api/top-assets")
def get_top_assets():
    # Ambil parameter sektor dari query string
    sector = request.args.get('sector')
    year = int(request.args.get('year', 2021))
    
    if not sector:
        return jsonify({"error": "Sector parameter is required"}), 400
    
    # Pipeline aggregation untuk mendapatkan top 5 dengan aset terbesar berdasarkan sektor
    pipeline = [
        {"$match": {
            "sector": {"$regex": sector, "$options": "i"},  # Case insensitive search
            "assets.current_year": {"$exists": True, "$ne": None},
            "reporting_year": year
        }},
        # Group berdasarkan company_code untuk menghindari duplikasi
        {"$group": {
            "_id": "$company_code",
            "emiten": {"$first": "$emiten"},
            "company_code": {"$first": "$company_code"},
            "sector": {"$first": "$sector"},
            "assets": {"$first": "$assets"},
            "reporting_year": {"$first": "$reporting_year"}
        }},
        {"$sort": {"assets.current_year": -1}},  # Urutkan dari terbesar
        {"$limit": 5},
        {"$project": {
            "_id": 0,
            "emiten": 1,
            "company_code": 1,
            "sector": 1,
            "assets": 1,
            "reporting_year": 1
        }}
    ]
    
    top_assets = list(collection_idx.aggregate(pipeline))
    
    # Mendapatkan daftar tahun unik untuk dropdown
    distinct_years = sorted(collection_idx.distinct("reporting_year"))
    
    return jsonify({
        "data": top_assets,
        "years": distinct_years
    })

# Route untuk halaman top assets
@app.route('/idx/top-assets')
def idx_top_assets():    return render_template('idx/top_assets.html', active_page='idx')

# API untuk Financial Ratios Analysis (ROE, ROA, NPM)
@app.route("/api/financial-ratios-data")
def get_financial_ratios_data():
    sector = request.args.get('sector')
    year = int(request.args.get('year', 2021))
    
    # Pipeline untuk menghitung financial ratios
    pipeline = [
        {"$match": {
            "net_profit.current_year": {"$exists": True, "$ne": None},
            "equity.current_year": {"$exists": True, "$ne": None, "$gt": 0},
            "assets.current_year": {"$exists": True, "$ne": None, "$gt": 0},
            "revenue.current_year": {"$exists": True, "$ne": None, "$gt": 0},
            "reporting_year": year
        }}
    ]
    
    # Add sector filter if provided
    if sector:
        pipeline[0]["$match"]["sector"] = {"$regex": sector, "$options": "i"}
    
    # Add aggregation stages
    pipeline.extend([
        {"$group": {
            "_id": "$company_code",
            "emiten": {"$first": "$emiten"},
            "company_code": {"$first": "$company_code"},
            "sector": {"$first": "$sector"},
            "net_profit": {"$first": "$net_profit.current_year"},
            "equity": {"$first": "$equity.current_year"},
            "assets": {"$first": "$assets.current_year"},
            "revenue": {"$first": "$revenue.current_year"},
            "reporting_year": {"$first": "$reporting_year"}
        }},
        {"$addFields": {
            "roe": {
                "$cond": {
                    "if": {"$and": [
                        {"$ne": ["$equity", 0]},
                        {"$ne": ["$equity", None]},
                        {"$ne": ["$net_profit", None]}
                    ]},
                    "then": {"$multiply": [{"$divide": ["$net_profit", "$equity"]}, 100]},
                    "else": None
                }
            },
            "roa": {
                "$cond": {
                    "if": {"$and": [
                        {"$ne": ["$assets", 0]},
                        {"$ne": ["$assets", None]},
                        {"$ne": ["$net_profit", None]}
                    ]},
                    "then": {"$multiply": [{"$divide": ["$net_profit", "$assets"]}, 100]},
                    "else": None
                }
            },
            "npm": {
                "$cond": {
                    "if": {"$and": [
                        {"$ne": ["$revenue", 0]},
                        {"$ne": ["$revenue", None]},
                        {"$ne": ["$net_profit", None]}
                    ]},
                    "then": {"$multiply": [{"$divide": ["$net_profit", "$revenue"]}, 100]},
                    "else": None
                }
            }
        }},
        {"$match": {
            "$or": [
                {"roe": {"$ne": None}},
                {"roa": {"$ne": None}},
                {"npm": {"$ne": None}}
            ]
        }},
        {"$sort": {"roe": -1}},
        {"$project": {
            "_id": 0,
            "emiten": 1,
            "company_code": 1,
            "sector": 1,
            "roe": 1,
            "roa": 1,
            "npm": 1,
            "net_profit": 1,
            "equity": 1,
            "assets": 1,
            "revenue": 1,
            "reporting_year": 1
        }}
    ])
    
    ratios_data = list(collection_idx.aggregate(pipeline))
    return jsonify(ratios_data)

# API untuk perbandingan financial ratios antar sektor
@app.route('/api/compare-financial-ratios')
def compare_financial_ratios():
    year = int(request.args.get('year', 2021))
    
    pipeline = [
        {"$match": {
            "net_profit.current_year": {"$exists": True, "$ne": None},
            "equity.current_year": {"$exists": True, "$ne": None, "$gt": 0},
            "assets.current_year": {"$exists": True, "$ne": None, "$gt": 0},
            "revenue.current_year": {"$exists": True, "$ne": None, "$gt": 0},
            "reporting_year": year
        }},
        {"$group": {
            "_id": "$company_code",
            "sector": {"$first": "$sector"},
            "net_profit": {"$first": "$net_profit.current_year"},
            "equity": {"$first": "$equity.current_year"},
            "assets": {"$first": "$assets.current_year"},
            "revenue": {"$first": "$revenue.current_year"}
        }},
        {"$addFields": {
            "roe": {
                "$cond": {
                    "if": {"$and": [
                        {"$ne": ["$equity", 0]},
                        {"$ne": ["$equity", None]},
                        {"$ne": ["$net_profit", None]}
                    ]},
                    "then": {"$multiply": [{"$divide": ["$net_profit", "$equity"]}, 100]},
                    "else": None
                }
            },
            "roa": {
                "$cond": {
                    "if": {"$and": [
                        {"$ne": ["$assets", 0]},
                        {"$ne": ["$assets", None]},
                        {"$ne": ["$net_profit", None]}
                    ]},
                    "then": {"$multiply": [{"$divide": ["$net_profit", "$assets"]}, 100]},
                    "else": None
                }
            },
            "npm": {
                "$cond": {
                    "if": {"$and": [
                        {"$ne": ["$revenue", 0]},
                        {"$ne": ["$revenue", None]},
                        {"$ne": ["$net_profit", None]}
                    ]},
                    "then": {"$multiply": [{"$divide": ["$net_profit", "$revenue"]}, 100]},
                    "else": None
                }
            }
        }},
        {"$group": {
            "_id": "$sector",
            "sector": {"$first": "$sector"},
            "avg_roe": {"$avg": "$roe"},
            "avg_roa": {"$avg": "$roa"},
            "avg_npm": {"$avg": "$npm"},
            "company_count": {"$sum": 1}
        }},
        {"$match": {
            "company_count": {"$gte": 2}  # Minimal 2 perusahaan per sektor
        }},
        {"$sort": {"avg_roe": -1}},        {"$project": {
            "_id": 0,
            "sector": 1,
            "avg_roe": {"$round": ["$avg_roe", 2]},
            "avg_roa": {"$round": ["$avg_roa", 2]},
            "avg_npm": {"$round": ["$avg_npm", 2]},
            "company_count": 1
        }}
    ]
    
    comparison_data = list(collection_idx.aggregate(pipeline))
    return jsonify(comparison_data)

# API untuk Long-Term Borrowing Analysis
@app.route("/api/long-term-borrowing-data")
def get_long_term_borrowing_data():
    sector = request.args.get('sector')
    year = int(request.args.get('year', 2022))
    
    # Pipeline untuk menghitung long-term borrowing trends
    pipeline = [
        {"$match": {
            "long_term_borrowing.current_year": {"$exists": True, "$ne": None},
            "reporting_year": year
        }}
    ]
    
    # Add sector filter if provided
    if sector:
        pipeline[0]["$match"]["sector"] = {"$regex": sector, "$options": "i"}
    
    # Add aggregation stages
    pipeline.extend([
        {"$group": {
            "_id": "$company_code",
            "emiten": {"$first": "$emiten"},
            "company_code": {"$first": "$company_code"},
            "sector": {"$first": "$sector"},
            "long_term_borrowing_current": {"$first": "$long_term_borrowing.current_year"},
            "long_term_borrowing_prior": {"$first": "$long_term_borrowing.prior_year"},
            "growth_rate_existing": {"$first": "$long_term_borrowing.growth_rate_percent"},
            "reporting_year": {"$first": "$reporting_year"}
        }},
        {"$addFields": {
            "growth_rate": {
                "$cond": {
                    "if": {"$ne": ["$growth_rate_existing", None]},
                    "then": "$growth_rate_existing",
                    "else": {
                        "$cond": {
                            "if": {"$and": [
                                {"$ne": ["$long_term_borrowing_prior", 0]},
                                {"$ne": ["$long_term_borrowing_prior", None]},
                                {"$ne": ["$long_term_borrowing_current", None]}
                            ]},
                            "then": {
                                "$multiply": [
                                    {"$divide": [
                                        {"$subtract": ["$long_term_borrowing_current", "$long_term_borrowing_prior"]},
                                        "$long_term_borrowing_prior"
                                    ]}, 100
                                ]
                            },
                            "else": None
                        }
                    }
                }
            }
        }},
        {"$sort": {"long_term_borrowing_current": -1}},
        {"$project": {
            "_id": 0,
            "emiten": 1,
            "company_code": 1,
            "sector": 1,
            "long_term_borrowing_current": 1,
            "long_term_borrowing_prior": 1,
            "growth_rate": 1,
            "reporting_year": 1
        }}
    ])
    
    borrowing_data = list(collection_idx.aggregate(pipeline))
    return jsonify(borrowing_data)

# API untuk Equity Trend Analysis
@app.route("/api/equity-trend-data")
def get_equity_trend_data():
    sector = request.args.get('sector')
    year = int(request.args.get('year', 2022))
    
    # Pipeline untuk menghitung equity trends
    pipeline = [
        {"$match": {
            "equity.current_year": {"$exists": True, "$ne": None},
            "reporting_year": year
        }}
    ]
    
    # Add sector filter if provided
    if sector:
        pipeline[0]["$match"]["sector"] = {"$regex": sector, "$options": "i"}
    
    # Add aggregation stages
    pipeline.extend([
        {"$group": {
            "_id": "$company_code",
            "emiten": {"$first": "$emiten"},
            "company_code": {"$first": "$company_code"},
            "sector": {"$first": "$sector"},
            "equity_current": {"$first": "$equity.current_year"},
            "equity_prior": {"$first": "$equity.prior_year"},
            "growth_rate_existing": {"$first": "$equity.growth_rate_percent"},
            "reporting_year": {"$first": "$reporting_year"}
        }},
        {"$addFields": {
            "growth_rate": {
                "$cond": {
                    "if": {"$ne": ["$growth_rate_existing", None]},
                    "then": "$growth_rate_existing",
                    "else": {
                        "$cond": {
                            "if": {"$and": [
                                {"$ne": ["$equity_prior", 0]},
                                {"$ne": ["$equity_prior", None]},
                                {"$ne": ["$equity_current", None]}
                            ]},
                            "then": {
                                "$multiply": [
                                    {"$divide": [
                                        {"$subtract": ["$equity_current", "$equity_prior"]},
                                        "$equity_prior"
                                    ]}, 100
                                ]
                            },
                            "else": None
                        }
                    }
                }
            }
        }},
        {"$sort": {"equity_current": -1}},
        {"$project": {
            "_id": 0,
            "emiten": 1,
            "company_code": 1,
            "sector": 1,
            "equity_current": 1,
            "equity_prior": 1,
            "growth_rate": 1,
            "reporting_year": 1
        }}
    ])
    
    equity_data = list(collection_idx.aggregate(pipeline))
    return jsonify(equity_data)

# API untuk perbandingan long-term borrowing antar sektor
@app.route('/api/compare-long-term-borrowing')
def compare_long_term_borrowing():
    year = int(request.args.get('year', 2022))
    
    pipeline = [
        {"$match": {
            "long_term_borrowing.current_year": {"$exists": True, "$ne": None},
            "reporting_year": year
        }},
        {"$group": {
            "_id": "$sector",
            "sector": {"$first": "$sector"},
            "total_companies": {"$sum": 1},
            "avg_debt": {"$avg": "$long_term_borrowing.current_year"},
            "total_debt": {"$sum": "$long_term_borrowing.current_year"},
            "max_debt": {"$max": "$long_term_borrowing.current_year"},
            "min_debt": {"$min": "$long_term_borrowing.current_year"}
        }},
        {"$sort": {"total_debt": -1}},
        {"$project": {
            "_id": 0,
            "sector": 1,
            "total_companies": 1,
            "avg_debt": 1,
            "total_debt": 1,
            "max_debt": 1,
            "min_debt": 1
        }}
    ]
    
    comparison_data = list(collection_idx.aggregate(pipeline))
    return jsonify(comparison_data)

# API untuk perbandingan equity antar sektor
@app.route('/api/compare-equity-trend')
def compare_equity_trend():
    year = int(request.args.get('year', 2022))
    
    pipeline = [
        {"$match": {
            "equity.current_year": {"$exists": True, "$ne": None},
            "reporting_year": year
        }},
        {"$group": {
            "_id": "$sector",
            "sector": {"$first": "$sector"},
            "total_companies": {"$sum": 1},
            "avg_equity": {"$avg": "$equity.current_year"},
            "total_equity": {"$sum": "$equity.current_year"},
            "max_equity": {"$max": "$equity.current_year"},
            "min_equity": {"$min": "$equity.current_year"},
            "avg_growth": {"$avg": {
                "$cond": {
                    "if": {"$and": [
                        {"$ne": ["$equity.prior_year", 0]},
                        {"$ne": ["$equity.prior_year", None]},
                        {"$ne": ["$equity.current_year", None]}
                    ]},
                    "then": {
                        "$multiply": [
                            {"$divide": [
                                {"$subtract": ["$equity.current_year", "$equity.prior_year"]},
                                "$equity.prior_year"
                            ]}, 100
                        ]
                    },
                    "else": None
                }
            }}
        }},
        {"$sort": {"total_equity": -1}},
        {"$project": {
            "_id": 0,
            "sector": 1,
            "total_companies": 1,
            "avg_equity": 1,
            "total_equity": 1,
            "max_equity": 1,
            "min_equity": 1,
            "avg_growth": 1
        }}
    ]
    
    comparison_data = list(collection_idx.aggregate(pipeline))
    return jsonify(comparison_data)

# Route untuk halaman yfinance 5 tahun
@app.route('/yfinance/5tahun')
def yfinance_lima_tahun():
    return render_template('yfinance/5y.html', active_page='yfinance')

# API untuk mendapatkan daftar ticker yang tersedia untuk 5 tahun
@app.route("/api/tickers/5tahun")
def get_tickers_lima_tahun():
    tickers = collection_yfinance_5tahun.distinct("ticker")
    return jsonify(tickers)

# API untuk mendapatkan data saham 5 tahun berdasarkan ticker
@app.route("/api/stock/5tahun/<ticker>")
def get_stock_data_lima_tahun(ticker):
    data = collection_yfinance_5tahun.find(
        {"ticker": ticker},
        {
            "_id": 0,
            "StartDate": 1,
            "Open": 1,
            "Close": 1,
            "Low": 1,
            "High": 1,
            "AvgVolume": 1,
            "MaxVolume": 1
        }
    ).sort("StartDate", 1)

    result = []
    for d in data:
        start_date = d.get("StartDate", "")
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
        elif isinstance(start_date, str) and "T" in start_date:
            start_date = start_date.split("T")[0]

        result.append({
            "StartDate": start_date,
            "open": d.get("Open", 0),
            "close": d.get("Close", 0),
            "high": d.get("High", 0),
            "low": d.get("Low", 0),
            "avgVolume": d.get("AvgVolume", 0),
            "maxVolume": d.get("MaxVolume", 0)
        })

    return jsonify(result)

# Route untuk halaman yfinance 3 tahun
@app.route('/yfinance/3tahun')
def yfinance_tiga_tahun():
    return render_template('yfinance/3y.html', active_page='yfinance')

# API untuk mendapatkan daftar ticker yang tersedia untuk 3 tahun
@app.route("/api/tickers/3tahun")
def get_tickers_tiga_tahun():
    tickers = collection_yfinance_3tahun.distinct("ticker")
    return jsonify(tickers)

# API untuk mendapatkan data saham 3 tahun berdasarkan ticker
@app.route("/api/stock/3tahun/<ticker>")
def get_stock_data_tiga_tahun(ticker):
    # Ambil semua data dulu
    data = collection_yfinance_3tahun.find(
        {"ticker": ticker},
        {
            "_id": 0,
            "StartDate": 1,
            "Open": 1,
            "Close": 1,
            "Low": 1,
            "High": 1,
            "AvgVolume": 1,
            "MaxVolume": 1
        }
    ).sort("StartDate", 1)

    tiga_tahun_lalu = datetime.now() - relativedelta(years=3)

    result = []
    for d in data:
        start_date_str = d.get("StartDate", "")
        try:
            # Ubah string ke datetime
            start_date = datetime.strptime(start_date_str.split("T")[0], "%Y-%m-%d")
        except Exception:
            continue  # skip kalau format salah

        # Filter hanya data 3 tahun terakhir
        if start_date >= tiga_tahun_lalu:
            result.append({
                "StartDate": start_date.strftime("%Y-%m-%d"),
                "open": d.get("Open", 0),
                "close": d.get("Close", 0),
                "high": d.get("High", 0),
                "low": d.get("Low", 0),
                "avgVolume": d.get("AvgVolume", 0),
                "maxVolume": d.get("MaxVolume", 0)
            })

    return jsonify(result)

# Route untuk halaman yfinance 1 tahun
@app.route('/yfinance/1tahun')
def yfinance_satu_tahun():
    return render_template('yfinance/1y.html', active_page='yfinance')

# API untuk mendapatkan daftar ticker yang tersedia untuk 1 tahun
@app.route("/api/tickers/1tahun")
def get_tickers_satu_tahun():
    tickers = collection_yfinance_1tahun.distinct("ticker")
    return jsonify(tickers)

# API untuk mendapatkan data saham 1 tahun berdasarkan ticker
@app.route("/api/stock/1tahun/<ticker>")
def get_stock_data_satu_tahun(ticker):
    # Ambil semua data dulu
    data = collection_yfinance_1tahun.find(
        {"ticker": ticker},
        {
            "_id": 0,
            "StartDate": 1,
            "Open": 1,
            "Close": 1,
            "Low": 1,
            "High": 1,
            "AvgVolume": 1,
            "MaxVolume": 1
        }
    ).sort("StartDate", 1)

    tiga_tahun_lalu = datetime.now() - relativedelta(years=1)

    result = []
    for d in data:
        start_date_str = d.get("StartDate", "")
        try:
            # Ubah string ke datetime
            start_date = datetime.strptime(start_date_str.split("T")[0], "%Y-%m-%d")
        except Exception:
            continue  # skip kalau format salah

        # Filter hanya data 1 tahun terakhir
        if start_date >= tiga_tahun_lalu:
            result.append({
                "StartDate": start_date.strftime("%Y-%m-%d"),
                "open": d.get("Open", 0),
                "close": d.get("Close", 0),
                "high": d.get("High", 0),
                "low": d.get("Low", 0),
                "avgVolume": d.get("AvgVolume", 0),
                "maxVolume": d.get("MaxVolume", 0)
            })

    return jsonify(result)

# Route untuk halaman yfinance tahunan
@app.route('/yfinance/tahunan')
def yfinance_tahunan():
    return render_template('yfinance/tahunan.html', active_page='yfinance')

# API untuk mendapatkan daftar ticker yang tersedia untuk data tahunan
@app.route("/api/tickers/tahunan")
def get_tickers_tahunan():
    tickers = collection_yfinance_tahunan.distinct("ticker")
    return jsonify(tickers)

# API untuk mendapatkan data saham tahunan berdasarkan ticker
@app.route("/api/stock/tahunan/<ticker>")
def get_stock_data_tahunan(ticker):
    data = collection_yfinance_tahunan.find(
        {"ticker": ticker},
        {
            "_id": 0,
            "Bulan": 1,
            "Open": 1,
            "Close": 1,
            "Low": 1,
            "High": 1,
            "AvgVolume": 1,
            "MaxVolume": 1
        }
    ).sort("Bulan", 1)

    result = []
    for d in data:
        result.append({
            "Bulan": d.get("Bulan", ""),
            "open": d.get("Open", 0),
            "close": d.get("Close", 0),
            "high": d.get("High", 0),
            "low": d.get("Low", 0),
            "avgVolume": d.get("AvgVolume", 0),
            "maxVolume": d.get("MaxVolume", 0)
        })

    return jsonify(result)

# Route halaman grafik bulanan
@app.route('/yfinance/bulanan')
def yfinance_bulanan():
    return render_template('yfinance/bulanan.html', active_page='yfinance')

# API: Ambil daftar ticker unik untuk data bulanan
@app.route("/api/tickers/bulanan")
def get_tickers_bulanan():
    tickers = collection_yfinance_bulanan.distinct("ticker")
    return jsonify(tickers)

# API: Ambil data saham berdasarkan ticker (grafik bulanan)
@app.route("/api/stock/bulanan/<ticker>")
def get_stock_data_bulanan(ticker):
    data = collection_yfinance_bulanan.find(
        {"ticker": ticker},
        {
            "_id": 0,
            "Bulan": 1,
            "Open": 1,
            "Close": 1,
            "Low": 1,
            "High": 1,
            "AvgVolume": 1,
            "MaxVolume": 1
        }
    ).sort("Bulan", 1)

    result = []
    for d in data:
        result.append({
            "Bulan": d.get("Bulan", ""),
            "open": d.get("Open", 0),
            "close": d.get("Close", 0),
            "high": d.get("High", 0),
            "low": d.get("Low", 0),
            "avgVolume": d.get("AvgVolume", 0),
            "maxVolume": d.get("MaxVolume", 0)
        })

    return jsonify(result)

# Route halaman mingguan
@app.route('/yfinance/mingguan')
def yfinance_mingguan():
    return render_template('yfinance/mingguan.html', active_page='yfinance')

# API ambil ticker unik dari data mingguan
@app.route("/api/tickers/mingguan")
def get_tickers_mingguan():
    tickers = collection_yfinance_mingguan.distinct("ticker")
    return jsonify(tickers)

# API ambil data saham mingguan berdasarkan ticker
@app.route("/api/stock/mingguan/<ticker>")
def get_stock_data_mingguan(ticker):
    data = collection_yfinance_mingguan.find(
        {"ticker": ticker},
        {
            "_id": 0,
            "Bulan": 1,
            "Open": 1,
            "Close": 1,
            "Low": 1,
            "High": 1,
            "AvgVolume": 1,
            "MaxVolume": 1
        }
    ).sort("Bulan", 1)

    result = []
    for d in data:
        result.append({
            "Bulan": d.get("Bulan", ""),  # format "2020-W25"
            "open": d.get("Open", 0),
            "close": d.get("Close", 0),
            "high": d.get("High", 0),
            "low": d.get("Low", 0),
            "avgVolume": d.get("AvgVolume", 0),
            "maxVolume": d.get("MaxVolume", 0)
        })

    return jsonify(result)

# Route halaman grafik harian
@app.route('/yfinance/harian')
def yfinance_harian():
    return render_template('yfinance/harian.html', active_page='yfinance')

# API: Ambil semua ticker unik dari data harian
@app.route("/api/tickers/harian")
def get_tickers_harian():
    tickers = collection_yfinance_harian.distinct("ticker")
    return jsonify(tickers)

# API: Ambil data harian berdasarkan ticker
@app.route("/api/stock/harian/<ticker>")
def get_stock_data_harian(ticker):
    data = collection_yfinance_harian.find(
        {"ticker": ticker},
        {
            "_id": 0,
            "Bulan": 1,  # format "2020-06-18"
            "Open": 1,
            "Close": 1,
            "Low": 1,
            "High": 1,
            "AvgVolume": 1,
            "MaxVolume": 1
        }
    ).sort("Bulan", 1)

    result = []
    for d in data:
        result.append({
            "Bulan": d.get("Bulan", ""),
            "open": d.get("Open", 0),
            "close": d.get("Close", 0),
            "high": d.get("High", 0),
            "low": d.get("Low", 0),
            "avgVolume": d.get("AvgVolume", 0),
            "maxVolume": d.get("MaxVolume", 0)
        })

    return jsonify(result)

@app.route('/market_news')
def market_news():
    return render_template('iqplus/market.html', active_page='market_news')

@app.route("/api/market_news")
def get_market_news():
    query = request.args.get("q", "")
    
    # Filter hanya data yang punya ringkasan
    match_stage = {
        "ringkasan": {"$exists": True, "$ne": None}
    }

    # Jika ada query pencarian, tambahkan filter pencarian
    if query:
        regex = {"$regex": query, "$options": "i"}
        match_stage["$or"] = [
            {"judul": regex},
            {"konten": regex},
            {"ringkasan": regex}
        ]

    # Pipeline aggregasi untuk hapus duplikat berdasarkan link
    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$link",  # unik berdasarkan link
                "judul": {"$first": "$judul"},
                "tanggal_artikel": {"$first": "$tanggal_artikel"},
                "ringkasan": {"$first": "$ringkasan"},
                "waktu": {"$first": "$waktu"},
                "link": {"$first": "$link"}
            }
        },
        {"$sort": {"tanggal_artikel": -1}}
    ]

    berita = list(collection_market_news.aggregate(pipeline))
    return jsonify(berita)

# Detail satu berita
@app.route("/market_news/<judul>")
def market_news_detail(judul):
    data = collection_market_news.find_one({"judul": judul})
    if not data:
        return "Berita tidak ditemukan", 404
    return render_template("iqplus/market_detail.html", berita=data)


@app.route('/stock_news')
def stock_news():
    return render_template('iqplus/stock.html', active_page='stock_news')

@app.route("/api/stock_news")
def get_stock_news():
    query = request.args.get("q", "")
    
    # Filter hanya data yang punya ringkasan
    match_stage = {
        "ringkasan": {"$exists": True, "$ne": None}
    }

    # Jika ada query pencarian, tambahkan filter pencarian
    if query:
        regex = {"$regex": query, "$options": "i"}
        match_stage["$or"] = [
            {"judul": regex},
            {"konten": regex},
            {"ringkasan": regex}
        ]

    # Pipeline aggregasi untuk hapus duplikat berdasarkan link
    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$link",  # unik berdasarkan link
                "judul": {"$first": "$judul"},
                "tanggal_artikel": {"$first": "$tanggal_artikel"},
                "ringkasan": {"$first": "$ringkasan"},
                "waktu": {"$first": "$waktu"},
                "link": {"$first": "$link"}
            }
        },
        {"$sort": {"tanggal_artikel": -1}}
    ]

    berita = list(collection_stock_news.aggregate(pipeline))
    return jsonify(berita)

# Detail satu berita
@app.route("/stock_news/<judul>")
def stock_news_detail(judul):
    data = collection_stock_news.find_one({"judul": judul})
    if not data:
        return "Berita tidak ditemukan", 404
    return render_template("iqplus/stock_detail.html", berita=data)

# @app.route("/api/test")
# def test_data():
#     data = list(collection_market_news.find())
#     print(data)  # buat debug di terminal
#     return jsonify(data)

# Jalankan Flask
if __name__ == "__main__":
    # app.run(debug=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)