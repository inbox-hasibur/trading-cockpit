"""DSE Market Map & Sector Analytics Module.

Provides comprehensive sector treemap data and Top Sectors By Gainer metrics
mirroring live Dhaka Stock Exchange (DSE) market breadth.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

# Complete realistic DSE sector dataset matching live market map screenshots
DSE_SECTOR_DATA: dict[str, list[dict[str, Any]]] = {
    "Textile": [
        {"symbol": "MATINSPINN", "change": 1.23, "turnover_cr": 32.56, "price": 65.8},
        {"symbol": "ENVOYTEX", "change": 4.23, "turnover_cr": 19.94, "price": 44.5},
        {"symbol": "SAIHAMTEX", "change": 7.49, "turnover_cr": 17.99, "price": 28.7},
        {"symbol": "SONARGAON", "change": 8.20, "turnover_cr": 10.85, "price": 31.7},
        {"symbol": "PTL", "change": -0.26, "turnover_cr": 9.48, "price": 76.2},
        {"symbol": "SAIHAMCOT", "change": 2.79, "turnover_cr": 8.05, "price": 22.1},
        {"symbol": "SIMTEX", "change": 2.05, "turnover_cr": 6.27, "price": 19.9},
        {"symbol": "MALEKSPIN", "change": 4.96, "turnover_cr": 4.72, "price": 29.6},
        {"symbol": "HWAWELLTEX", "change": 0.60, "turnover_cr": 4.52, "price": 50.3},
        {"symbol": "ETL", "change": 2.11, "turnover_cr": 4.45, "price": 14.5},
        {"symbol": "APEXSPINN", "change": 0.02, "turnover_cr": 4.26, "price": 132.0},
        {"symbol": "FEKDIL", "change": 2.46, "turnover_cr": 4.25, "price": 16.6},
        {"symbol": "SQUARETEXT", "change": 4.23, "turnover_cr": 3.83, "price": 68.9},
        {"symbol": "MLDYEING", "change": 0.00, "turnover_cr": 3.58, "price": 15.0},
        {"symbol": "ARGONDENIM", "change": -0.49, "turnover_cr": 2.62, "price": 20.2},
        {"symbol": "SHARPIND", "change": 3.64, "turnover_cr": 2.19, "price": 17.1},
        {"symbol": "DSSL", "change": 1.02, "turnover_cr": 2.16, "price": 19.8},
        {"symbol": "SHEPHERD", "change": 1.90, "turnover_cr": 1.14, "price": 16.1},
        {"symbol": "MHSML", "change": 1.18, "turnover_cr": 1.12, "price": 25.7},
        {"symbol": "DACCADYE", "change": 4.79, "turnover_cr": 0.80, "price": 13.1},
        {"symbol": "MONNOFABR", "change": 1.23, "turnover_cr": 0.74, "price": 24.6},
        {"symbol": "SHASHADNIM", "change": -0.79, "turnover_cr": 0.70, "price": 25.1},
        {"symbol": "PDL", "change": 8.16, "turnover_cr": 0.53, "price": 10.6},
        {"symbol": "VFSTDL", "change": 2.61, "turnover_cr": 0.52, "price": 15.7},
        {"symbol": "TOSRIFA", "change": -1.08, "turnover_cr": 0.50, "price": 18.3},
        {"symbol": "QUEENSOUTH", "change": 0.00, "turnover_cr": 1.58, "price": 14.2},
    ],
    "Insurance": [
        {"symbol": "PROVATIINS", "change": 2.59, "turnover_cr": 8.76, "price": 59.4},
        {"symbol": "DGIC", "change": 1.54, "turnover_cr": 5.91, "price": 32.9},
        {"symbol": "CITYGENINS", "change": 0.00, "turnover_cr": 5.36, "price": 42.1},
        {"symbol": "PIONEERINS", "change": 1.75, "turnover_cr": 4.74, "price": 69.8},
        {"symbol": "PURABIGEN", "change": 8.65, "turnover_cr": 4.37, "price": 33.9},
        {"symbol": "NITOLINS", "change": 1.94, "turnover_cr": 2.91, "price": 41.9},
        {"symbol": "AGRANINS", "change": 1.56, "turnover_cr": 2.55, "price": 32.5},
        {"symbol": "ISLAMIINS", "change": 1.56, "turnover_cr": 2.49, "price": 39.0},
        {"symbol": "RELIANCINS", "change": 3.03, "turnover_cr": 2.18, "price": 64.6},
        {"symbol": "ICICL", "change": 3.51, "turnover_cr": 1.42, "price": 29.5},
        {"symbol": "MERCINS", "change": 3.66, "turnover_cr": 1.40, "price": 31.2},
        {"symbol": "SIPLC", "change": 2.71, "turnover_cr": 1.30, "price": 41.6},
        {"symbol": "EASTERNINS", "change": -0.80, "turnover_cr": 1.20, "price": 55.4},
        {"symbol": "CENTRALINS", "change": 1.41, "turnover_cr": 1.10, "price": 36.0},
        {"symbol": "PEOPLESINS", "change": 2.07, "turnover_cr": 0.95, "price": 29.5},
        {"symbol": "BGIC", "change": 0.00, "turnover_cr": 0.88, "price": 44.0},
    ],
    "Engineering": [
        {"symbol": "BSRMSTEEL", "change": 4.13, "turnover_cr": 6.40, "price": 63.1},
        {"symbol": "NAHEEACP", "change": -2.45, "turnover_cr": 5.26, "price": 39.9},
        {"symbol": "DOMINAGE", "change": 0.16, "turnover_cr": 4.64, "price": 12.3},
        {"symbol": "ANWARGALV", "change": -1.27, "turnover_cr": 4.29, "price": 186.5},
        {"symbol": "BBSCABLES", "change": 5.62, "turnover_cr": 3.25, "price": 35.7},
        {"symbol": "RUNNERAUTO", "change": 4.02, "turnover_cr": 3.13, "price": 33.6},
        {"symbol": "WALTONHIL", "change": 0.40, "turnover_cr": 2.80, "price": 680.0},
        {"symbol": "BDLAMPS", "change": 0.35, "turnover_cr": 1.85, "price": 172.0},
        {"symbol": "GPHISPAT", "change": 1.20, "turnover_cr": 1.50, "price": 33.5},
        {"symbol": "BSRMLTD", "change": 0.28, "turnover_cr": 1.40, "price": 89.0},
        {"symbol": "NAVANAENG", "change": -0.90, "turnover_cr": 1.10, "price": 21.8},
        {"symbol": "OIMEX", "change": 1.33, "turnover_cr": 0.95, "price": 15.2},
    ],
    "Fuel & Power": [
        {"symbol": "SPCL", "change": 3.48, "turnover_cr": 18.74, "price": 62.4},
        {"symbol": "DOREENPWR", "change": 4.73, "turnover_cr": 4.78, "price": 33.2},
        {"symbol": "INTRACO", "change": 7.34, "turnover_cr": 3.49, "price": 30.7},
        {"symbol": "BPPL", "change": 2.63, "turnover_cr": 3.39, "price": 27.3},
        {"symbol": "EASTRNLUB", "change": -0.26, "turnover_cr": 3.11, "price": 1150.0},
        {"symbol": "MPETROLEUM", "change": -0.58, "turnover_cr": 1.50, "price": 204.0},
        {"symbol": "POWERGRID", "change": -0.90, "turnover_cr": 1.20, "price": 43.8},
        {"symbol": "CVOPRL", "change": 2.18, "turnover_cr": 0.94, "price": 140.0},
        {"symbol": "UPGDCL", "change": 0.00, "turnover_cr": 0.85, "price": 178.5},
        {"symbol": "TITASGAS", "change": 0.00, "turnover_cr": 0.70, "price": 30.9},
    ],
    "Bank": [
        {"symbol": "BRACBANK", "change": 0.46, "turnover_cr": 9.12, "price": 65.5},
        {"symbol": "CITYBANK", "change": 1.07, "turnover_cr": 6.05, "price": 28.3},
        {"symbol": "PRIMEBANK", "change": 0.00, "turnover_cr": 3.77, "price": 21.5},
        {"symbol": "PUBALIBANK", "change": 2.48, "turnover_cr": 2.44, "price": 28.9},
        {"symbol": "JAMUNABANK", "change": 1.30, "turnover_cr": 1.80, "price": 23.3},
        {"symbol": "MTB", "change": 1.03, "turnover_cr": 1.56, "price": 19.6},
        {"symbol": "NBL", "change": 1.37, "turnover_cr": 1.20, "price": 7.4},
        {"symbol": "TRUSTBANK", "change": 1.68, "turnover_cr": 1.15, "price": 30.2},
        {"symbol": "EBL", "change": 1.30, "turnover_cr": 1.12, "price": 31.1},
        {"symbol": "IFIC", "change": 0.00, "turnover_cr": 1.11, "price": 8.5},
        {"symbol": "BANKASIA", "change": 0.50, "turnover_cr": 1.05, "price": 20.4},
        {"symbol": "DHAKABANK", "change": 0.00, "turnover_cr": 0.90, "price": 13.0},
        {"symbol": "UTTARABANK", "change": 0.45, "turnover_cr": 0.85, "price": 22.3},
    ],
    "Food & Allied": [
        {"symbol": "FINEFOODS", "change": 0.48, "turnover_cr": 13.05, "price": 125.6},
        {"symbol": "LOVELLO", "change": 2.78, "turnover_cr": 2.39, "price": 77.5},
        {"symbol": "BATBC", "change": 1.27, "turnover_cr": 2.17, "price": 382.0},
        {"symbol": "RDFOOD", "change": 4.74, "turnover_cr": 1.64, "price": 39.8},
        {"symbol": "APEXFOODS", "change": 1.01, "turnover_cr": 1.10, "price": 268.0},
        {"symbol": "GHAIL", "change": 0.80, "turnover_cr": 0.90, "price": 14.5},
        {"symbol": "OLYMPIC", "change": 0.00, "turnover_cr": 0.85, "price": 150.0},
    ],
    "Pharmaceuticals & Chemicals": [
        {"symbol": "FARCHEM", "change": 2.41, "turnover_cr": 12.30, "price": 8.5},
        {"symbol": "SQURPHARMA", "change": 0.46, "turnover_cr": 7.02, "price": 216.0},
        {"symbol": "ASIATICLAB", "change": 2.46, "turnover_cr": 5.51, "price": 41.7},
        {"symbol": "BXPHARMA", "change": 0.64, "turnover_cr": 4.37, "price": 90.0},
        {"symbol": "ORIONINFU", "change": 6.92, "turnover_cr": 4.33, "price": 455.0},
        {"symbol": "ORIONPHARM", "change": -4.18, "turnover_cr": 3.16, "price": 68.7},
        {"symbol": "IBP", "change": 1.44, "turnover_cr": 1.67, "price": 14.1},
        {"symbol": "ACMEPL", "change": 0.43, "turnover_cr": 1.06, "price": 70.0},
        {"symbol": "SILVAPHL", "change": 2.07, "turnover_cr": 0.95, "price": 14.8},
        {"symbol": "PHARMAID", "change": -3.80, "turnover_cr": 1.10, "price": 540.0},
        {"symbol": "BEACONPHAR", "change": 0.00, "turnover_cr": 0.80, "price": 180.0},
        {"symbol": "RENATA", "change": 0.00, "turnover_cr": 0.75, "price": 620.0},
    ],
    "Mutual Funds": [
        {"symbol": "1STPRIMFMF", "change": -0.73, "turnover_cr": 8.46, "price": 13.5},
        {"symbol": "CAPMIBBLMF", "change": -2.99, "turnover_cr": 3.66, "price": 16.2},
        {"symbol": "PF1STMF", "change": 0.85, "turnover_cr": 3.55, "price": 11.9},
        {"symbol": "RELIANCE1", "change": 0.88, "turnover_cr": 1.77, "price": 11.5},
        {"symbol": "MBL1STMF", "change": 1.15, "turnover_cr": 1.04, "price": 8.8},
        {"symbol": "EXIM1STMF", "change": 0.00, "turnover_cr": 0.90, "price": 5.4},
        {"symbol": "ICBSONALI1", "change": 1.25, "turnover_cr": 0.85, "price": 8.1},
    ],
    "Financial Institutions": [
        {"symbol": "IPDC", "change": 1.75, "turnover_cr": 7.30, "price": 17.4},
        {"symbol": "IDLC", "change": 0.85, "turnover_cr": 2.10, "price": 35.6},
        {"symbol": "LANKABAFIN", "change": 1.40, "turnover_cr": 1.85, "price": 14.5},
        {"symbol": "MIDASFIN", "change": -1.20, "turnover_cr": 0.75, "price": 8.2},
        {"symbol": "BAYLEASING", "change": 0.00, "turnover_cr": 0.60, "price": 6.5},
        {"symbol": "ICB", "change": 0.00, "turnover_cr": 1.50, "price": 62.0},
    ],
    "Miscellaneous": [
        {"symbol": "BEXIMCO", "change": 2.58, "turnover_cr": 6.55, "price": 115.6},
        {"symbol": "BSC", "change": 2.04, "turnover_cr": 2.89, "price": 45.0},
        {"symbol": "AMANFEED", "change": 0.00, "turnover_cr": 1.10, "price": 28.5},
        {"symbol": "BERGERPBL", "change": 0.00, "turnover_cr": 0.95, "price": 1750.0},
        {"symbol": "SINOBANGLA", "change": 0.00, "turnover_cr": 0.85, "price": 52.0},
        {"symbol": "KBPPWBBL", "change": -0.90, "turnover_cr": 0.80, "price": 11.0},
    ],
    "IT Sector": [
        {"symbol": "AGNISYSL", "change": 1.35, "turnover_cr": 1.87, "price": 22.5},
        {"symbol": "AAMRATECH", "change": 2.54, "turnover_cr": 1.60, "price": 32.3},
        {"symbol": "GENEXIL", "change": 0.00, "turnover_cr": 1.45, "price": 31.0},
        {"symbol": "BDCOM", "change": 2.50, "turnover_cr": 1.20, "price": 24.6},
        {"symbol": "EGEN", "change": 1.80, "turnover_cr": 0.95, "price": 28.2},
        {"symbol": "DAFODILCOM", "change": -1.10, "turnover_cr": 0.70, "price": 58.0},
    ],
    "Life Insurance": [
        {"symbol": "SONALILIFE", "change": 1.20, "turnover_cr": 1.70, "price": 68.0},
        {"symbol": "SUNLIFEINS", "change": -2.10, "turnover_cr": 1.10, "price": 37.5},
        {"symbol": "RUPALILIFE", "change": -0.80, "turnover_cr": 0.95, "price": 85.0},
        {"symbol": "MEGHNALIFE", "change": 0.50, "turnover_cr": 0.80, "price": 62.0},
        {"symbol": "DELTALIFE", "change": 0.00, "turnover_cr": 0.75, "price": 130.0},
    ],
    "Tannery Industries": [
        {"symbol": "MKFOOTWEAR", "change": 4.01, "turnover_cr": 9.61, "price": 18.2},
        {"symbol": "APEXFOOT", "change": 0.80, "turnover_cr": 1.15, "price": 240.0},
        {"symbol": "BATASHOE", "change": 0.00, "turnover_cr": 0.90, "price": 920.0},
        {"symbol": "SAMORITA", "change": 2.05, "turnover_cr": 3.40, "price": 64.8},
        {"symbol": "FORTUNE", "change": 1.10, "turnover_cr": 1.50, "price": 18.5},
    ],
    "Paper & Printing": [
        {"symbol": "HAKKANIPUL", "change": 1.80, "turnover_cr": 1.20, "price": 45.0},
        {"symbol": "BPML", "change": -1.50, "turnover_cr": 0.90, "price": 38.0},
        {"symbol": "MAGNUPAPER", "change": 0.00, "turnover_cr": 0.60, "price": 24.0},
    ],
    "Cement": [
        {"symbol": "LHBL", "change": 0.00, "turnover_cr": 1.38, "price": 62.5},
        {"symbol": "PREMIERCEM", "change": -1.10, "turnover_cr": 0.85, "price": 44.0},
        {"symbol": "HEIDELBCEM", "change": 0.40, "turnover_cr": 0.75, "price": 195.0},
        {"symbol": "CONFIDCEM", "change": 0.00, "turnover_cr": 0.60, "price": 72.0},
    ],
    "Ceramics Sector": [
        {"symbol": "SPCERA", "change": 0.00, "turnover_cr": 2.61, "price": 28.0},
        {"symbol": "SHINEPUKUR", "change": 1.50, "turnover_cr": 1.20, "price": 27.5},
        {"symbol": "RAKCERAMIC", "change": 0.00, "turnover_cr": 0.80, "price": 30.0},
        {"symbol": "MONNOCERA", "change": -0.80, "turnover_cr": 0.70, "price": 88.0},
    ],
    "Services & Real Estate": [
        {"symbol": "EHL", "change": 0.50, "turnover_cr": 1.40, "price": 68.0},
        {"symbol": "SAIFPOWER", "change": 1.20, "turnover_cr": 1.10, "price": 16.5},
    ],
    "Travel & Leisure": [
        {"symbol": "SEAPEARL", "change": 1.80, "turnover_cr": 1.50, "price": 78.0},
        {"symbol": "UNIQUEHRL", "change": 0.00, "turnover_cr": 0.80, "price": 48.0},
    ],
    "Jute": [
        {"symbol": "SONALIANSH", "change": 1.75, "turnover_cr": 3.78, "price": 315.0},
        {"symbol": "NORTHERN", "change": 0.00, "turnover_cr": 0.50, "price": 180.0},
    ],
    "Telecommunication": [
        {"symbol": "GP", "change": 0.52, "turnover_cr": 1.65, "price": 265.0},
        {"symbol": "ROBI", "change": 1.02, "turnover_cr": 1.15, "price": 24.8},
        {"symbol": "BSCCL", "change": 0.00, "turnover_cr": 0.90, "price": 142.0},
    ],
}


def build_market_map_payload(scenario_bias: Decimal = Decimal("0")) -> dict[str, Any]:
    """Builds hierarchical treemap data and sector gainer stats for the visualizer."""
    sectors_out: list[dict[str, Any]] = []
    bar_chart_data: list[dict[str, Any]] = []

    bias_float = float(scenario_bias)

    for sector_name, companies in DSE_SECTOR_DATA.items():
        comp_out = []
        sector_turnover = 0.0
        up_count = 0
        down_count = 0
        eql_count = 0

        for c in companies:
            adj_change = round(c["change"] + bias_float, 2)
            turnover = c["turnover_cr"]
            sector_turnover += turnover

            if adj_change > 0:
                up_count += 1
            elif adj_change < 0:
                down_count += 1
            else:
                eql_count += 1

            comp_out.append({
                "symbol": c["symbol"],
                "sector": sector_name,
                "change": adj_change,
                "turnover_cr": turnover,
                "price": c["price"],
            })

        # Sort companies within sector by turnover desc
        comp_out.sort(key=lambda item: item["turnover_cr"], reverse=True)

        sector_entry = {
            "name": sector_name,
            "turnover_cr": round(sector_turnover, 2),
            "up_count": up_count,
            "down_count": down_count,
            "eql_count": eql_count,
            "total_count": len(comp_out),
            "companies": comp_out,
        }
        sectors_out.append(sector_entry)

        bar_chart_data.append({
            "sector": sector_name,
            "up": up_count,
            "down": down_count,
            "eql": eql_count,
            "total": len(comp_out),
            "turnover_cr": round(sector_turnover, 2),
        })

    # Sort treemap sectors by total turnover descending
    sectors_out.sort(key=lambda s: s["turnover_cr"], reverse=True)

    # Sort bar chart sectors by UP count descending (matching Image 3 "Top Sectors By Gainer")
    bar_chart_data.sort(key=lambda b: (b["up"], b["turnover_cr"]), reverse=True)

    return {
        "treemap": sectors_out,
        "top_sectors_by_gainer": bar_chart_data,
        "total_turnover_cr": round(sum(s["turnover_cr"] for s in sectors_out), 2),
        "total_companies": sum(s["total_count"] for s in sectors_out),
        "total_up": sum(s["up_count"] for s in sectors_out),
        "total_down": sum(s["down_count"] for s in sectors_out),
        "total_eql": sum(s["eql_count"] for s in sectors_out),
    }

