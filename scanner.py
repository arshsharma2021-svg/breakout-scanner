"""
Morgan Trades Breakout Strategy Scanner — Automated, GitHub Actions ready
==========================================================================
Universe : Hardcoded S&P 500 + Russell 1000 extras (~1000 tickers)
Data     : yfinance (free, no API key)
Output   : data/results.json (committed back to repo by the GitHub Action)

Designed to run unattended on a schedule. Per-ticker errors never crash
the whole run -- they're logged and skipped.
"""

import argparse
import json
import sys
import time
import traceback
from datetime import datetime

import pandas as pd
import yfinance as yf

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
CONFIG = {
    "min_price": 1.0,
    "min_adr_pct": 5.0,
    "min_avg_dollar_volume": 3_500_000,
    "runup_lookback_days": 60,
    "runup_min_pct": 30.0,
    "sma_slope_lookback": 5,
    "pullback_lookback_days": 20,
    "volume_dryup_ratio": 0.70,
    "breakout_volume_ratio": 1.50,
    "sma20_proximity_pct": 0.08,
}

# ─────────────────────────────────────────────────────────────────────────────
# UNIVERSE
# ─────────────────────────────────────────────────────────────────────────────
SP500 = [
    "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","ABNB",
    "AKAM","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL","GOOG","MO","AMZN",
    "AMCR","AEE","AAL","AEP","AXP","AIG","AMT","AWK","AMP","AME","AMGN","APH",
    "ADI","ANSS","AON","APA","APO","AAPL","AMAT","APTV","ACGL","ADM","ANET",
    "AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON","BKR","BALL",
    "BAC","BK","BBWI","BAX","BDX","BRK-B","BBY","BIO","TECH","BIIB","BLK",
    "BX","BA","BMY","AVGO","BR","BRO","BF-B","BLDR","BSX","BWA","BG",
    "CHRW","CDNS","CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR","CTLT",
    "CAT","CBOE","CBRE","CDW","CE","COR","CNC","CNX","CF","CRL","SCHW",
    "CHTR","CVX","CMG","CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX",
    "CME","CMS","KO","CTSH","CL","CMCSA","CMA","CAG","COP","ED","STZ","CEG",
    "COO","CPRT","GLW","CTVA","CSGP","COST","CTRA","CCI","CSX","CMI","CVS",
    "DHR","DRI","DVA","DAY","DE","DECK","DAL","DVN","DXCM","FANG","DLR","DFS",
    "DG","DLTR","D","DPZ","DOV","DOW","DHI","DTE","DUK","DD","EMN","ETN",
    "EBAY","ECL","EIX","EW","EA","ELV","EMR","ENPH","ETR","EOG","EPAM","EQT",
    "EFX","EQIX","EQR","ESS","EL","ETSY","EG","EVRG","ES","EXC","EXPE","EXPD",
    "EXPO","EXR","XOM","FFIV","FDS","FICO","FAST","FRT","FDX","FIS","FITB",
    "FSLR","FE","FI","FLT","FMC","F","FTNT","FTV","FOXA","FOX","BEN","FCX",
    "GRMN","IT","GE","GEHC","GEV","GEN","GNRC","GD","GIS","GPC","GILD","GPN",
    "GL","GDDY","GS","HAL","HIG","HAS","HCA","DOC","HSIC","HSY","HES","HPE",
    "HLT","HOLX","HD","HON","HRL","HST","HWM","HPQ","HUBB","HUM","HBAN","HII",
    "IBM","IEX","IDXX","ITW","INCY","IR","PODD","INTC","ICE","IFF","IP","IPG",
    "INTU","ISRG","IVZ","INVH","IQV","IRM","JBHT","JBL","JKHY","J","JNJ",
    "JCI","JPM","JNPR","K","KVUE","KDP","KEY","KEYS","KMB","KIM","KMI","KLAC",
    "KHC","KR","LHX","LH","LRCX","LW","LVS","LDOS","LEN","LLY","LIN","LYV",
    "LKQ","LMT","L","LOW","LULU","LYB","MTB","MRO","MPC","MKTX","MAR","MMC",
    "MLM","MAS","MA","MTCH","MKC","MCD","MCK","MDT","MRK","META","MET","MTD",
    "MGM","MCHP","MU","MSFT","MAA","MRNA","MHK","MOH","TAP","MDLZ","MPWR",
    "MNST","MCO","MS","MOS","MSI","MSCI","NDAQ","NTAP","NFLX","NEM","NWSA",
    "NWS","NEE","NKE","NI","NDSN","NSC","NTRS","NOC","NCLH","NRG","NUE",
    "NVDA","NVR","NXPI","ORLY","OXY","ODFL","OMC","ON","OKE","ORCL","OTIS",
    "PCAR","PKG","PANW","PH","PAYX","PAYC","PYPL","PNR","PEP","PFE","PCG",
    "PM","PSX","PNW","PNC","POOL","PPG","PPL","PFG","PG","PGR","PLD",
    "PRU","PEG","PTC","PSA","PHM","QRVO","PWR","QCOM","DGX","RL",
    "RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY","ROK","ROL","ROP",
    "ROST","RCL","SPGI","CRM","SBAC","SLB","STX","SRE","NOW","SHW","SPG",
    "SWKS","SJM","SNA","SOLV","SO","LUV","SWK","SBUX","STT","STLD","STE",
    "SYK","SYF","SNPS","SYY","TMUS","TROW","TTWO","TPR","TRGP","TGT","TEL",
    "TDY","TFX","TER","TSLA","TXN","TXT","TMO","TJX","TSCO","TT","TDG","TRV",
    "TRMB","TFC","TYL","TSN","USB","UDR","ULTA","UNP","UAL","UPS","URI","UNH",
    "UHS","VLO","VTR","VLTO","VRSN","VRSK","VZ","VRTX","VTRS","VICI","V",
    "VMC","WRB","GWW","WAB","WBA","WMT","DIS","WBD","WM","WAT","WEC","WFC",
    "WELL","WST","WDC","WY","WHR","WMB","WTW","WYNN","XEL","XYL","YUM",
    "ZBRA","ZBH","ZTS",
]

RUSSELL_EXTRA = [
    "AFRM","AGCO","AGL","AIRC","ALGT","ALK","ALLY","ALNY","ALTR",
    "AMG","AMKR","AMPH","AMRN","AMWL","ANGI","ANF","AR","ARC","ARCO",
    "ARMO","ARRY","ARWR","ARVN","ASH","ATI","AVAV","AVNT","AZEK","AZPN",
    "BANF","BANR","BC","BCPC","BDTX","BEAM","BERY","BJ","BKNG",
    "BLD","BLMN","BMI","BOOT","BORR","BPMC","BRBR","BRKR","BRZE","BUR","CALM",
    "CAMT","CANO","CAPR","CATS","CAVA","CBSH","CCEP","CEIX","CERT","CFR","CHX",
    "CHWY","CIB","CLB","CLFD","CLH","CLOV","CNA","CNMD","CNXC",
    "COHR","COKE","COLL","COLM","CPNG","CPRX","CPSI","CRDO","CROX",
    "CRSP","CRUS","CRVL","CSGS","CUZ","CW","CWEN","CWT","CXM","CXW","DAR",
    "DDS","DDOG","DELL","DEN","DFH","DKS","DNOW","DQ","DRH","DRQ","DRVN",
    "DUOL","DV","DVAX","DXC","DXPE","EAT","EBS","EGP","ELAN","ENOV",
    "ENS","ENV","EPRT","EQH","ESAB","ESNT","ESE","ESGR","EXP","EXTR","EZPW",
    "FAF","FARO","FBP","FCNCA","FCPT","FG","FIVN","FL","FLNC","FLO","FLUT",
    "FMX","FNB","FND","FNF","FOLD","FORM","FOUR","FRME","FRPT","FRSH",
    "FSS","FULT","FUN","G","GATX","GEF","GFF","GHM","GLDD","GLNG",
    "GLOB","GMS","GNW","GO","GOOS","GPK","GRND","GRPN","GRWG","GTLB","GVA",
    "HAFC","HAE","HALO","HASI","HBI","HCC","HCI","HCSG","HGV","HIW","HIMS",
    "HL","HLI","HLNE","HMN","HNI","HOPE","HOMB","HOOD","HTLD","HTLF",
    "HXL","IART","IBP","ICFI","ICL","IDCC","IESC","IIPR","IMVT","INDB","INFA",
    "INFN","INGR","INSP","INST","INTA","IONQ","IONS","IOSP","IOVA",
    "IPGP","IRDM","ITT","JAMF","JOBY","KALU","KAR",
    "KBR","KFRC","KRYS","KSS","KTB","LADR","LANC","LAUR","LCII","LCID","LECO",
    "LEG","LGIH","LGND","LHCG","LII","LITE","LIVN","LMAT","LNTH","LOPE","LPLA",
    "LPSN","LRN","LSI","LSTR","LUMN","LXFR","M","MARA","MATX","MBI",
    "MCBC","MEDP","MEI","MELI","MGNI","MGPI","MIDD","MLAB","MLKN",
    "MMSI","MNDY","MNKD","MODG","MODV","MQ","MRC","MRUS","MSGS","MTSI","MTZ",
    "MXL","NATL","NBTB","NCNO","NDLS","NEO","NEXT","NKLA","NMIH",
    "NMRK","NRDS","NSIT","NTB","NTGR","NTLA","NVAX","NVST","NWE","NWLI",
    "NYCB","OFG","ONB","OPCH","OPRT","ORA","OSCR","OTEX","PACB","PAGP","PAR",
    "PARR","PATK","PAYO","PCRX","PDCO","PFLT","PGNY","PI","PIPR","PLMR",
    "PLXS","PNFP","POST","POWL","PPBI","PRIM","PRGO","PRGS","PRVA","PSTG",
    "PTCT","PVH","QS","QTWO","RBC","RDWR","RGEN","RGNX","RHP","RIOT","RITM",
    "RIVN","RLJ","RNG","RRGB","RRR","RUSHA","RXST","RYAN","SABR","SAFE","SAIA",
    "SANM","SBCF","SBH","SBGI","SBRA","SCCO","SFBS","SFNC","SFM","SG","SITE",
    "SITC","SLAB","SLG","SLGN","SMCI","SMR","SMTC","SNX","SNEX","SNV",
    "SONO","SPOK","SPS","SPSC","SPTN","SPXC","SR","SRDX","STEL",
    "STEP","STRL","STRA","SUM","SUPN","SYNA","TBBK","TCBK",
    "TDC","TDOC","TFIN","TGTX","TKR","TMDX","TMHC","TNDM","TNET","TPIC",
    "TREE","TRIP","TRMK","TRNO","TRS","TRST","TRTX","TRUP","TTEC",
    "TTMI","TWNK","TXRH","UBSI","UCBI","UFPI","UGI","ULCC",
    "UMBF","UMPQ","UNFI","UNF","UPBD","UPST","USFD",
    "USM","UTHR","UWMC","VCEL","VFC","VIRT","VMI","VRTS","VSCO","VSEC",
    "VTLE","VVV","WAFD","WASH","WD","WDFC","WGO","WH","WINA",
    "WMG","WOLF","WOOF","WPC","WRLD","WS","WSBC","WSFS","WTFC","WWD",
    "XHR","XNCR","XPEL","XPER","YELP","YMM","YORW","ZI","ZION",
    "ZM","ZWS",
]

UNIVERSE = sorted(set(SP500 + RUSSELL_EXTRA))


# ─────────────────────────────────────────────────────────────────────────────
# MARKET CONDITIONS
# ─────────────────────────────────────────────────────────────────────────────
def check_market(ticker="QQQ"):
    try:
        df = yf.Ticker(ticker).history(period="6mo", interval="1d")
        if df is None or df.empty or len(df) < 25:
            return {"favorable": None, "note": "Could not fetch QQQ data"}
        df = df.reset_index()
        df["sma10"] = df["Close"].rolling(10).mean()
        df["sma20"] = df["Close"].rolling(20).mean()
        s10 = df["sma10"].iloc[-1]
        s20 = df["sma20"].iloc[-1]
        if pd.isna(s10) or pd.isna(s20):
            return {"favorable": None, "note": "Not enough QQQ history yet"}
        ok = bool(s10 > s20)
        return {
            "favorable": ok,
            "qqq_sma10": round(float(s10), 2),
            "qqq_sma20": round(float(s20), 2),
            "note": (
                "FAVORABLE - QQQ 10 SMA above 20 SMA. Breakout setups favored."
                if ok else
                "UNFAVORABLE - QQQ 10 SMA below 20 SMA. Expect lower win rate."
            ),
        }
    except Exception as e:
        return {"favorable": None, "note": "Error checking market: %s" % e}


# ─────────────────────────────────────────────────────────────────────────────
# INDICATORS
# ─────────────────────────────────────────────────────────────────────────────
def add_indicators(df):
    c = df["Close"]
    df["sma10"] = c.rolling(10).mean()
    df["sma20"] = c.rolling(20).mean()
    df["sma50"] = c.rolling(50).mean()
    df["sma200"] = c.rolling(200).mean()
    df["adr_pct"] = (df["High"] / df["Low"] - 1).rolling(20).mean() * 100
    df["dollar_vol"] = c * df["Volume"]
    df["avg_dollar_vol_20"] = df["dollar_vol"].rolling(20).mean()
    df["avg_vol_20"] = df["Volume"].rolling(20).mean()
    return df


def hard_filter(df):
    last = df.iloc[-1]
    price = float(last["Close"])
    adr = last["adr_pct"]
    dvol = last["avg_dollar_vol_20"]

    adr_val = float(adr) if not pd.isna(adr) else 0.0
    dvol_val = float(dvol) if not pd.isna(dvol) else 0.0

    checks = {
        "price > $1": price > CONFIG["min_price"],
        "ADR% > 5": adr_val > CONFIG["min_adr_pct"],
        "$vol > $3.5M (20d)": dvol_val > CONFIG["min_avg_dollar_volume"],
    }
    return all(checks.values()), checks


def score_pattern(df):
    cfg = CONFIG
    n = len(df)
    res = {
        "step1_runup_30pct": False,
        "step2_sma_inclining": False,
        "step3_pullback_tighten": False,
        "step4_vol_dryup": False,
        "step5_breakout_vol": False,
        "sma_all_stacked": False,
        "runup_pct": None,
        "pct_from_sma20": None,
        "vol_dryup_ratio": None,
        "breakout_vol_ratio": None,
        "steps_passed": 0,
        "score": 0,
    }

    lb = cfg["runup_lookback_days"]
    sl = cfg["sma_slope_lookback"]

    # Step 1
    if n > lb + 5:
        window = df.iloc[-lb:]
        lo_idx = window["Low"].idxmin()
        hi_after = df.loc[lo_idx:]["High"].max()
        lo_val = df.at[lo_idx, "Low"]
        if lo_val and lo_val > 0:
            pct = (hi_after / lo_val - 1) * 100
            res["runup_pct"] = round(float(pct), 1)
            res["step1_runup_30pct"] = pct >= cfg["runup_min_pct"]

    # Step 2
    if n > sl + 25:
        s10n, s10t = df["sma10"].iloc[-1], df["sma10"].iloc[-1 - sl]
        s20n, s20t = df["sma20"].iloc[-1], df["sma20"].iloc[-1 - sl]
        s50n, s50t = df["sma50"].iloc[-1], df["sma50"].iloc[-1 - sl]
        s200n, s200t = df["sma200"].iloc[-1], df["sma200"].iloc[-1 - sl]
        if not any(pd.isna(x) for x in [s10n, s10t, s20n, s20t]):
            res["step2_sma_inclining"] = bool(s10n > s10t and s20n > s20t)
        if not any(pd.isna(x) for x in [s10n, s20n, s50n, s200n, s10t, s20t, s50t, s200t]):
            res["sma_all_stacked"] = bool(
                s10n > s20n > s50n > s200n
                and s10n > s10t and s20n > s20t
                and s50n > s50t and s200n > s200t
            )

    # Step 3
    pb = cfg["pullback_lookback_days"]
    if n > pb + 5:
        recent = df.iloc[-pb:]
        mid = pb // 2
        r1 = recent.iloc[:mid]["High"].max() - recent.iloc[:mid]["Low"].min()
        r2 = recent.iloc[mid:]["High"].max() - recent.iloc[mid:]["Low"].min()
        sma20_last = df["sma20"].iloc[-1]
        close_last = float(df["Close"].iloc[-1])
        if not pd.isna(sma20_last) and sma20_last > 0:
            pct_from = (close_last / float(sma20_last) - 1)
            res["pct_from_sma20"] = round(pct_from * 100, 2)
            res["step3_pullback_tighten"] = bool(
                r2 < r1 and abs(pct_from) < cfg["sma20_proximity_pct"]
            )

    # Step 4
    if n > pb + 25:
        vol_pb = df["Volume"].iloc[-pb:].mean()
        vol_prev = df["Volume"].iloc[-(pb + 20):-pb].mean()
        if vol_prev and vol_prev > 0:
            ratio = vol_pb / vol_prev
            res["vol_dryup_ratio"] = round(float(ratio), 2)
            res["step4_vol_dryup"] = ratio < cfg["volume_dryup_ratio"]

    # Step 5
    if n > 22:
        last_vol = float(df["Volume"].iloc[-1])
        avg_vol = df["avg_vol_20"].iloc[-2]
        if not pd.isna(avg_vol) and avg_vol > 0:
            bvr = last_vol / float(avg_vol)
            res["breakout_vol_ratio"] = round(bvr, 2)
            res["step5_breakout_vol"] = bvr > cfg["breakout_volume_ratio"]

    steps = sum([
        res["step1_runup_30pct"], res["step2_sma_inclining"],
        res["step3_pullback_tighten"], res["step4_vol_dryup"],
        res["step5_breakout_vol"],
    ])
    res["steps_passed"] = steps
    res["score"] = round(steps / 5 * 100)
    return res


def fetch_one(ticker, retries=2):
    """Fetch + validate a single ticker's history. Returns df or None."""
    for attempt in range(retries):
        try:
            df = yf.Ticker(ticker).history(period="1y", interval="1d", auto_adjust=True)
            if df is None or df.empty or len(df) < 60:
                return None
            df = df.reset_index()
            required = {"Date", "Open", "High", "Low", "Close", "Volume"}
            if not required.issubset(df.columns):
                return None
            return df
        except Exception:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            return None
    return None


def main():
    ap = argparse.ArgumentParser(description="Morgan Trades Breakout Scanner")
    ap.add_argument("--out", default="data/results.json")
    ap.add_argument("--min-score", type=int, default=0)
    ap.add_argument("--no-market-check", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Limit universe size (for testing)")
    args = ap.parse_args()

    universe = UNIVERSE[:args.limit] if args.limit > 0 else UNIVERSE

    print("=" * 60)
    print("  BREAKOUT SCANNER - Morgan Trades Strategy")
    print("  Universe : %d tickers" % len(universe))
    print("  Started  : %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    market = {"favorable": None, "note": "skipped"}
    if not args.no_market_check:
        print("\nChecking market conditions (QQQ)...")
        market = check_market()
        print("  -> %s" % market["note"])

    results = []
    passed = failed = errors = 0
    total = len(universe)

    print("\nScanning %d tickers individually (safe mode, handles bad tickers gracefully)...\n" % total)

    for i, ticker in enumerate(universe, 1):
        try:
            df = fetch_one(ticker)
            if df is None:
                errors += 1
                if i % 50 == 0:
                    print("  [%4d/%d] ... (%d errors so far)" % (i, total, errors))
                continue

            df = add_indicators(df)
            ok, filter_checks = hard_filter(df)
            last = df.iloc[-1]

            adr_pct = last["adr_pct"]
            dvol = last["avg_dollar_vol_20"]

            row = {
                "ticker": ticker,
                "date": str(df["Date"].iloc[-1].date()),
                "close": round(float(last["Close"]), 2),
                "adr_pct": round(float(adr_pct), 2) if not pd.isna(adr_pct) else None,
                "avg_dollar_vol_20": round(float(dvol), 0) if not pd.isna(dvol) else None,
                "passes_filters": ok,
                "filter_checks": filter_checks,
                "pattern": None,
            }

            if ok:
                passed += 1
                pat = score_pattern(df)
                row["pattern"] = pat
                steps = pat["steps_passed"]
                bar = "#" * steps + "." * (5 - steps)
                print("  [%4d/%d] %-6s PASS  %s  %d/5  run=%s%%" % (
                    i, total, ticker, bar, steps, pat["runup_pct"]))
            else:
                failed += 1

            results.append(row)

        except Exception as e:
            errors += 1
            print("  [%4d/%d] %-6s ERROR  %s" % (i, total, ticker, e))
            continue

    results.sort(
        key=lambda r: (
            r["passes_filters"],
            r["pattern"]["score"] if r["pattern"] else -1,
        ),
        reverse=True,
    )

    if args.min_score > 0:
        results = [
            r for r in results
            if r["passes_filters"] and r["pattern"]
            and r["pattern"]["steps_passed"] >= args.min_score
        ]

    output = {
        "generated_at": datetime.now().isoformat(),
        "universe_size": total,
        "passed_filters": passed,
        "failed_filters": failed,
        "errors": errors,
        "config": CONFIG,
        "market_conditions": market,
        "results": results,
    }

    import os
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w") as f:
        json.dump(output, f, indent=2)

    candidates = [r for r in results if r["pattern"] and r["pattern"]["steps_passed"] >= 3]
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("  Passed hard filters : %d" % passed)
    print("  3+/5 step candidates: %d" % len(candidates))
    print("  Errors / no data    : %d" % errors)
    print("  Output saved to     : %s" % args.out)
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nFATAL ERROR:")
        traceback.print_exc()
        sys.exit(1)
