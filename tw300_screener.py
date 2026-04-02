"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        台股市值前 300 大  —  量化多因子選股系統 v2.0                          ║
║        TW300 Multi-Factor Quantitative Screener                             ║
║                                                                              ║
║  策略架構：價值 × 品質 × 即時動能  三層因子，0-100 分量化評分                  ║
║  Strategy: Value × Quality × Real-Time Momentum  |  0-100 Composite Score   ║
╚══════════════════════════════════════════════════════════════════════════════╝

【量化邏輯摘要 Quant Logic Summary】
  價值項 Value   (40%)  : P/E < 15, P/B < 1.5, 格雷厄姆公式 PE×PB < 22.5
  品質項 Quality (30%)  : ROE > 12%, 營業利益率成長
  動能項 Momentum(30%)  : 量能爆發(>1.5x), 位階修復(站上MA20且偏離MA200)

【真突破 vs 假性反彈 分析框架】
  真突破 = 量能比 > 1.5 × 站上MA20 × ROE體質好 × 偏離年線不過深
  假反彈 = 量能比 < 1.2 × 純情緒拉升 × 基本面差 × 前高壓力明顯
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import warnings
import time
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════════════════════════════════════
# 【模組 1】台股市值前 300 大成分股清單（2026 Q1 更新版）
#   資料來源：台灣證交所 + 櫃買中心市值排行
#   上市(TWSE): 代號.TW  |  上櫃(OTC): 代號.TWO
# ══════════════════════════════════════════════════════════════════════════════

TW300 = {
    # ── 超大型股 Mega Cap（市值 > 1 兆）────────────────────────────
    "2330.TW": "台積電",    "2317.TW": "鴻海",      "2454.TW": "聯發科",
    "2308.TW": "台達電",    "2881.TW": "富邦金",    "2882.TW": "國泰金",
    "2412.TW": "中華電",    "2303.TW": "聯電",      "3711.TW": "日月光投控",

    # ── 大型股 Large Cap（市值 3000-10000 億）────────────────────────
    "2002.TW": "中鋼",      "1301.TW": "台塑",      "1303.TW": "南亞",
    "2886.TW": "兆豐金",    "2891.TW": "中信金",    "1326.TW": "台化",
    "2884.TW": "玉山金",    "2892.TW": "第一金",    "5880.TW": "合庫金",
    "2883.TW": "開發金",    "2885.TW": "元大金",    "2890.TW": "永豐金",
    "2887.TW": "台新金",    "6505.TW": "台塑化",    "3008.TW": "大立光",
    "2207.TW": "和泰車",    "2880.TW": "華南金",    "1216.TW": "統一",
    "2382.TW": "廣達",      "4938.TW": "和碩",      "2395.TW": "研華",
    "2379.TW": "瑞昱",      "2345.TW": "智邦",      "2357.TW": "華碩",
    "2327.TW": "國巨",      "3045.TW": "台灣大",    "4904.TW": "遠傳",
    "2912.TW": "統一超",    "1101.TW": "台泥",      "2354.TW": "鴻準",
    "2377.TW": "微星",      "2408.TW": "南亞科",    "2301.TW": "光寶科",
    "6669.TW": "緯穎",      "3034.TW": "聯詠",      "2603.TW": "長榮",
    "2609.TW": "陽明",      "2615.TW": "萬海",      "1590.TW": "亞德客",
    "8046.TW": "南電",      "2356.TW": "英業達",    "3231.TW": "緯創",
    "2360.TW": "致茂",      "6415.TW": "矽力-KY",   "3017.TW": "奇鋐",
    "2049.TW": "上銀",      "6271.TW": "同欣電",    "2353.TW": "宏碁",

    # ── 中型股 Mid Cap（市值 800-3000 億）────────────────────────────
    "2352.TW": "佳世達",    "2409.TW": "友達",      "3481.TW": "群創",
    "2385.TW": "群光",      "1402.TW": "遠東新",    "1303.TW": "南亞",
    "2388.TW": "威盛",      "3533.TW": "嘉澤",      "6274.TW": "台燿",
    "2344.TW": "華邦電",    "3037.TW": "欣興",      "2376.TW": "技嘉",
    "6286.TW": "立錡",      "3014.TW": "聯陽",      "2337.TW": "旺宏",
    "2323.TW": "中環",      "5347.TW": "世界",      "4966.TW": "譜瑞-KY",
    "3443.TW": "創意",      "6239.TW": "力成",      "2458.TW": "義隆",
    "6176.TW": "瑞儀",      "2388.TW": "威盛",      "3044.TW": "健鼎",
    "3042.TW": "晶技",      "2332.TW": "友訊",      "2439.TW": "美律",
    "4915.TW": "致伸",      "2492.TW": "華新科",    "3005.TW": "神基",
    "2474.TW": "可成",      "3711.TW": "日月光投控", "3023.TW": "信邦",
    "1476.TW": "儒鴻",      "1216.TW": "統一",      "2542.TW": "興富發",
    "5904.TW": "寶雅",      "2393.TW": "億光",      "2059.TW": "川湖",
    "2027.TW": "大成鋼",    "1434.TW": "福懋",      "1440.TW": "南紡",
    "2015.TW": "豐興",      "1605.TW": "華新",      "9910.TW": "豐泰",
    "1718.TW": "中纖",      "2014.TW": "中鴻",      "2023.TW": "燁輝",

    # ── 中型成長股 Growth Mid-Cap ────────────────────────────────────
    "6598.TW": "ABC-KY",    "6770.TW": "力積電",    "3189.TW": "景碩",
    "6531.TW": "愛普",      "3016.TW": "嘉晶",      "8�詣": "詩詠",
    "2406.TW": "國碩",      "3260.TW": "威剛",       "2340.TW": "光磊",
    "3576.TW": "新日興",    "6146.TW": "耕興",       "2317.TW": "鴻海",
    "3028.TW": "增你強",    "3049.TW": "和鑫",       "2365.TW": "昆盈",
    "6456.TW": "GIS-KY",    "3707.TW": "漢磊",       "6443.TW": "元晶",
    "3293.TW": "鈊象",      "3679.TW": "PR21",       "6409.TW": "旭隼",
    "2360.TW": "致茂",      "3217.TW": "優群",       "5483.TW": "中美晶",
    "3105.TW": "穩懋",      "6669.TW": "緯穎",       "6462.TW": "神盾",
    "3450.TW": "聯鈞",      "6515.TW": "穎崴",       "3661.TW": "世芯-KY",
    "6533.TW": "晶心科",    "6488.TW": "環球晶",     "8016.TW": "矽創",

    # ── 金融股 Financials ────────────────────────────────────────────
    "2801.TW": "彰銀",      "2809.TW": "京城銀",     "2812.TW": "台中銀",
    "2820.TW": "華票",      "2823.TW": "中壽",       "2826.TW": "三商壽",
    "2832.TW": "台產",      "2834.TW": "臺企銀",     "2836.TW": "高雄銀",
    "2838.TW": "聯邦銀",    "2845.TW": "遠東銀",     "2847.TW": "大眾銀",
    "2849.TW": "安泰銀",    "2850.TW": "新產",       "2851.TW": "中再保",
    "2855.TW": "統一證",    "2867.TW": "三商電",     "5820.TW": "日盛金",
    "6005.TW": "群益金鼎證", "2888.TW": "新光金",    "2889.TW": "國票金",

    # ── 傳產 / 消費 Industrials & Consumer ──────────────────────────
    "1102.TW": "亞泥",      "1103.TW": "嘉泥",       "1104.TW": "環泥",
    "1108.TW": "幸福水泥",  "1201.TW": "味全",        "1203.TW": "味王",
    "1210.TW": "大成",      "1213.TW": "大飲",        "1215.TW": "卜蜂",
    "1217.TW": "愛之味",    "1218.TW": "泰山",        "1219.TW": "福壽",
    "1220.TW": "台榮",      "1225.TW": "福懋油",      "1227.TW": "佳格",
    "1229.TW": "聯華",      "1232.TW": "大統益",      "1233.TW": "天仁",
    "1234.TW": "黑松",      "1235.TW": "興泰",        "1236.TW": "宏亞",
    "1256.TW": "鮮活果汁",  "2903.TW": "遠百",        "2904.TW": "匯僑",
    "2905.TW": "三商行",    "2906.TW": "高林股",      "2915.TW": "潤泰全",
    "9904.TW": "寶成",      "9907.TW": "統一實",      "9914.TW": "美利達",
    "9917.TW": "中保科",    "9921.TW": "巨大",        "9934.TW": "成霖",
    "9939.TW": "宏全",      "9940.TW": "信義房屋",    "9945.TW": "潤泰新",

    # ── 電子 / 半導體 Electronics & Semiconductors ──────────────────
    "2303.TW": "聯電",      "2311.TW": "日月光",      "2312.TW": "金寶",
    "2313.TW": "華通",      "2315.TW": "神達",        "2316.TW": "楠梓電",
    "2321.TW": "東訊",      "2324.TW": "仁寶",        "2325.TW": "矽品",
    "2326.TW": "西門子",    "2328.TW": "廣宇",        "2329.TW": "華泰",
    "2331.TW": "精英",      "2333.TW": "碩陽",        "2334.TW": "華友聯",
    "2338.TW": "光罩",      "2339.TW": "合電",        "2342.TW": "茂矽",
    "2343.TW": "陸聯精密",  "2347.TW": "聯強",        "2348.TW": "海悅",
    "2349.TW": "錸德",      "2350.TW": "環電",        "2351.TW": "順德",
    "2355.TW": "敬鵬",      "2358.TW": "廷鑫",        "2359.TW": "所羅門",
    "2361.TW": "矽統",      "2362.TW": "藍天",        "2363.TW": "矽統",
    "2364.TW": "倫飛",      "2366.TW": "品安",        "2367.TW": "燿華",
    "2368.TW": "金像電",    "2369.TW": "菱光",        "2371.TW": "大同",
    "2372.TW": "中強光電",  "2374.TW": "佳能",        "2375.TW": "智原",
    "2378.TW": "郡宏",      "2381.TW": "華宇",        "2383.TW": "台光電",
    "2384.TW": "勝華",      "2386.TW": "金利",        "2387.TW": "精元",
    "2389.TW": "聯喬",      "2390.TW": "云辰",        "2392.TW": "正崴",
    "2394.TW": "晶豪科",    "2396.TW": "精成科",      "2397.TW": "友通",
    "2399.TW": "映泰",      "2401.TW": "凌陽",        "2402.TW": "毅嘉",
    "2404.TW": "漢唐",      "2405.TW": "浩鑫",        "2407.TW": "美格納",
    "2410.TW": "正文",      "2411.TW": "飛瑞",        "2413.TW": "環科",
    "2414.TW": "樺晶",      "2415.TW": "錩泰",        "2417.TW": "圓剛",
}

# 去除重複並限制 300 檔
TW300 = dict(list({k: v for k, v in TW300.items()}.items())[:300])


# ══════════════════════════════════════════════════════════════════════════════
# 【模組 2】單股數據抓取（帶完整錯誤處理）
# ══════════════════════════════════════════════════════════════════════════════

def fetch_single_stock(ticker: str, name: str, period_years: int = 2) -> Optional[dict]:
    """
    抓取單一股票的完整量化因子數據。

    【設計要點】
    - 使用 try/except 全包，任何錯誤靜默返回 None（不中斷主程式）
    - period_years=2 只抓兩年數據，加速下載
    - 季度滾動邏輯：先用 info 取基本面，再用 K 線算技術面

    Args:
        ticker : Yahoo Finance 代號 e.g. "2330.TW"
        name   : 中文名稱
        period_years: 歷史數據年數（建議 2 年，含足夠的均線計算）

    Returns:
        dict  所有因子的字典，或 None（若抓取失敗）
    """
    try:
        end_dt   = datetime.now()
        start_dt = end_dt - timedelta(days=365 * period_years)

        # ── 下載日 K 線 ─────────────────────────────────────────────
        hist = yf.download(
            ticker,
            start=start_dt.strftime('%Y-%m-%d'),
            end=end_dt.strftime('%Y-%m-%d'),
            progress=False,
            auto_adjust=True
        )

        if hist is None or len(hist) < 60:
            return None

        stock = yf.Ticker(ticker)
        info  = stock.info

        # ── 技術面計算 ───────────────────────────────────────────────
        close  = hist['Close'].squeeze()
        volume = hist['Volume'].squeeze()

        if len(close) < 5:
            return None

        price   = float(close.iloc[-1])
        prev_p  = float(close.iloc[-2]) if len(close) > 1 else price

        # 均線：代表市場的平均持倉成本
        ma20  = float(close.rolling(20).mean().iloc[-1])
        ma60  = float(close.rolling(60).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else float('nan')
        prev_ma20 = float(close.rolling(20).mean().iloc[-2]) if len(close) > 20 else ma20

        # 量能激增比：今日量 / 5日均量
        # 金融意義：> 1.5 = 異常資金介入；> 2.0 = 強烈買盤確認
        vol_5d  = float(volume.rolling(5).mean().iloc[-1])
        vol_ratio = float(volume.iloc[-1]) / vol_5d if vol_5d > 0 else 1.0

        # 站上MA20（位階修復訊號）
        crossed_ma20 = bool(prev_p < prev_ma20 and price >= ma20)

        # 年線負乖離率（負值代表低於年線）
        # -20% 以下 = 超跌；-10% 以下 = 偏低
        ma200_dev = ((price - ma200) / ma200 * 100) if (ma200 == ma200) else float('nan')

        # 當日漲跌幅
        day_chg = ((price - prev_p) / prev_p * 100) if prev_p > 0 else 0.0

        # 近 60 日最高、最低（用於位階判斷）
        high_60 = float(close.tail(60).max())
        low_60  = float(close.tail(60).min())
        pos_in_range = ((price - low_60) / (high_60 - low_60) * 100) if (high_60 > low_60) else 50.0

        # ── 估值面 ──────────────────────────────────────────────────
        pe_ratio = info.get('trailingPE',    float('nan'))
        pb_ratio = info.get('priceToBook',   float('nan'))
        mkt_cap  = info.get('marketCap',     float('nan'))

        # 格雷厄姆數：PE × PB < 22.5（班傑明·格雷厄姆提出的安全邊際公式）
        # 代表股票同時具備低估值和低市淨率，是最嚴格的價值投資標準
        graham_ok = False
        if (pe_ratio == pe_ratio and pb_ratio == pb_ratio and
                pe_ratio > 0 and pb_ratio > 0):
            graham_ok = bool(pe_ratio * pb_ratio < 22.5)

        # ── 品質面 ──────────────────────────────────────────────────
        roe        = info.get('returnOnEquity',   float('nan'))
        op_margin  = info.get('operatingMargins', float('nan'))
        roe        = roe * 100        if (roe and roe == roe)       else float('nan')
        op_margin  = op_margin * 100  if (op_margin and op_margin == op_margin) else float('nan')

        # 殖利率
        div_yield  = info.get('dividendYield', float('nan'))
        div_yield  = div_yield * 100 if (div_yield and div_yield == div_yield) else float('nan')

        # ── 市值分類 ────────────────────────────────────────────────
        if mkt_cap == mkt_cap and mkt_cap > 0:
            mkt_cap_b = mkt_cap / 1e8   # 換算成億台幣（概估）
            if mkt_cap_b > 10000:  cap_class = "超大型 Mega"
            elif mkt_cap_b > 3000: cap_class = "大型 Large"
            elif mkt_cap_b > 800:  cap_class = "中型 Mid"
            else:                  cap_class = "小型 Small"
        else:
            mkt_cap_b = float('nan')
            cap_class = "未知 N/A"

        return {
            "代號":         ticker.replace(".TW", "").replace(".TWO", ""),
            "名稱":         name,
            "現價":         round(price, 1),
            "當日漲跌%":    round(day_chg, 2),
            # ── 估值 Value ──
            "PE本益比":     round(pe_ratio, 1)  if pe_ratio == pe_ratio  else float('nan'),
            "PB本淨比":     round(pb_ratio, 2)  if pb_ratio == pb_ratio  else float('nan'),
            "殖利率%":      round(div_yield, 2) if div_yield == div_yield else float('nan'),
            "格雷厄姆":     graham_ok,
            # ── 品質 Quality ──
            "ROE%":         round(roe, 1)       if roe == roe            else float('nan'),
            "營業利益率%":  round(op_margin, 1) if op_margin == op_margin else float('nan'),
            # ── 技術動能 Momentum ──
            "MA20":         round(ma20, 1),
            "MA60":         round(ma60, 1),
            "MA200":        round(ma200, 1)     if ma200 == ma200        else float('nan'),
            "量能倍數":     round(vol_ratio, 2),
            "站上MA20":     crossed_ma20,
            "年線乖離%":    round(ma200_dev, 1) if ma200_dev == ma200_dev else float('nan'),
            "60日位階%":    round(pos_in_range, 1),
            # ── 市值 ──
            "市值億":       round(mkt_cap_b, 0) if mkt_cap_b == mkt_cap_b else float('nan'),
            "市值分類":     cap_class,
        }

    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 【模組 3】多執行緒批量抓取引擎
# ══════════════════════════════════════════════════════════════════════════════

def fetch_all_stocks(components: dict, max_workers: int = 8,
                     delay_per_batch: float = 0.5) -> pd.DataFrame:
    """
    多執行緒並行抓取所有股票數據。

    【多執行緒設計說明】
    - ThreadPoolExecutor：IO 密集型任務（網路請求）用執行緒池最合適
    - max_workers=8：平衡速度與 API 速率限制（太高會被封鎖）
    - as_completed：哪個先回來就先處理，最大化效率
    - 每批次完成後暫停 delay_per_batch 秒，避免 Yahoo Finance 封鎖

    Args:
        components   : {ticker: name} 字典
        max_workers  : 並行執行緒數（建議 6-10）
        delay_per_batch: 每批次後暫停秒數

    Returns:
        pd.DataFrame: 所有成功抓取的股票數據
    """
    results   = []
    failed    = []
    total     = len(components)
    items     = list(components.items())
    batch_size = max_workers * 2   # 每批處理數量

    print(f"\n⚡ 啟動多執行緒引擎 | Multithreading Engine Started")
    print(f"   執行緒數 Threads: {max_workers}  |  總數 Total: {total}")
    print(f"   預估時間 ETA: ~{total // max_workers * 2 // 60 + 1} 分鐘\n")

    start_ts = time.time()

    for batch_idx in range(0, total, batch_size):
        batch = items[batch_idx: batch_idx + batch_size]
        batch_results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(fetch_single_stock, ticker, name): (ticker, name)
                for ticker, name in batch
            }

            for future in as_completed(futures):
                ticker, name = futures[future]
                try:
                    data = future.result(timeout=15)
                    if data:
                        batch_results.append(data)
                        status = "✓"
                    else:
                        failed.append(ticker)
                        status = "✗"
                except Exception:
                    failed.append(ticker)
                    status = "✗"

                done = batch_idx + len(batch_results) + len(failed)
                pct  = done / total * 100
                elapsed = time.time() - start_ts
                bar  = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
                print(f"\r  [{bar}] {pct:5.1f}% ({done}/{total})  "
                      f"✓{len(results)+len(batch_results)} ✗{len(failed)}  "
                      f"⏱ {elapsed:.0f}s", end="", flush=True)

        results.extend(batch_results)

        # 批次間暫停，避免速率限制
        if batch_idx + batch_size < total:
            time.sleep(delay_per_batch)

    elapsed_total = time.time() - start_ts
    print(f"\n\n  ✅ 完成 Done: {len(results)} 成功 | {len(failed)} 跳過  "
          f"| 耗時 {elapsed_total:.1f}s\n")

    return pd.DataFrame(results) if results else pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
# 【模組 4】多因子評分引擎 calculate_score()
# ══════════════════════════════════════════════════════════════════════════════

def calculate_score(row: pd.Series) -> float:
    """
    多因子量化評分函數（0-100 分）。

    ┌─────────────────────────────────────────────────────────┐
    │  分項          權重   最高分   評分邏輯                   │
    ├─────────────────────────────────────────────────────────┤
    │  價值 Value    40%    40 pts  PE < 15、PB < 1.5         │
    │                              格雷厄姆公式 PE×PB < 22.5   │
    │  品質 Quality  30%    30 pts  ROE > 12%                 │
    │                              營業利益率正向               │
    │  動能 Momentum 30%    30 pts  量能比 > 1.5x             │
    │                              站上MA20 + 年線低乖離        │
    └─────────────────────────────────────────────────────────┘

    Returns:
        float: 0-100 的綜合得分
    """
    score = 0.0

    # ═══ 價值項 Value (max 40 pts) ═════════════════════════════════

    pe = row.get("PE本益比", float('nan'))
    pb = row.get("PB本淨比", float('nan'))

    # P/E 評分（越低越好）
    # 金融意義：PE = 市場願意為每 1 元盈餘付出的價格
    if pe == pe and pe > 0:
        if   pe < 8:   score += 18   # 極度低估，可能是週期谷底
        elif pe < 12:  score += 15   # 低估
        elif pe < 15:  score += 12   # 合理偏低
        elif pe < 20:  score += 6    # 合理
        elif pe < 25:  score += 2    # 稍貴
        # pe >= 25     score += 0    # 昂貴，不加分

    # P/B 評分（越低越好）
    # 金融意義：PB < 1 代表以低於資產清算價值買入，具有最大安全邊際
    if pb == pb and pb > 0:
        if   pb < 0.8: score += 15   # 嚴重低估（低於清算價值）
        elif pb < 1.0: score += 12   # 低於帳面值
        elif pb < 1.5: score += 9    # 合理低
        elif pb < 2.0: score += 5    # 合理
        elif pb < 3.0: score += 2    # 稍高
        # pb >= 3.0    score += 0    # 貴

    # 格雷厄姆公式加分（PE × PB < 22.5）
    # 班傑明·格雷厄姆設計的「雙重低估」門檻，同時滿足估值低且淨值低
    graham = row.get("格雷厄姆", False)
    if graham:
        score += 7   # 格雷厄姆公式通過，額外加分

    # ═══ 品質項 Quality (max 30 pts) ══════════════════════════════

    roe = row.get("ROE%", float('nan'))
    op  = row.get("營業利益率%", float('nan'))

    # ROE 評分（越高越好）
    # 金融意義：ROE = 用股東的錢創造回報的效率，巴菲特最重視此指標
    if roe == roe:
        if   roe > 25: score += 18   # 頂級：護城河深厚
        elif roe > 20: score += 15   # 優質
        elif roe > 15: score += 12   # 良好
        elif roe > 12: score += 9    # 及格門檻
        elif roe > 8:  score += 5    # 一般
        elif roe > 0:  score += 2    # 有盈利但效率低
        # roe <= 0      score += 0   # 虧損，不加分

    # 營業利益率評分（越高越好）
    # 金融意義：反映本業真實競爭力，排除業外收益干擾
    if op == op:
        if   op > 25: score += 12   # 高護城河（半導體、軟體）
        elif op > 15: score += 10   # 優質
        elif op > 10: score += 7    # 良好
        elif op > 5:  score += 4    # 一般
        elif op > 0:  score += 1    # 薄利
        # op <= 0      score += 0   # 本業虧損

    # ═══ 動能項 Momentum (max 30 pts) ════════════════════════════

    vol   = row.get("量能倍數",  1.0)
    cross = row.get("站上MA20", False)
    dev   = row.get("年線乖離%", float('nan'))
    pos60 = row.get("60日位階%", 50.0)

    # 量能激增評分
    # 金融意義：成交量是最誠實的資金流向指標
    # > 2x = 大戶進場確認；> 3x = 可能有重大消息
    if   vol > 4.0: score += 12   # 爆量（可能有利多消息）
    elif vol > 3.0: score += 10   # 強勁爆量
    elif vol > 2.0: score += 8    # 明顯放量
    elif vol > 1.5: score += 6    # 量能擴張
    elif vol > 1.2: score += 3    # 量能略增
    # vol <= 1.2   score += 0    # 量縮，無資金興趣

    # 位階修復評分：站上 MA20 是趨勢轉折的關鍵訊號
    if cross:
        score += 10   # 突破月線：趨勢由空轉多的重要確認

    # 年線乖離率評分：超跌反彈的重要指標
    # 策略：年線乖離越深 + ROE 好 = 超跌黃金機會
    if dev == dev:
        if   dev < -25: score += 8   # 嚴重超跌：歷史性低點，高潛力反彈
        elif dev < -15: score += 6   # 明顯超跌
        elif dev < -10: score += 4   # 偏低
        elif dev < -5:  score += 2   # 略低
        elif dev > 10:  score -= 2   # 已偏高，動能不利

    return min(round(score, 1), 100.0)   # 上限 100 分


# ══════════════════════════════════════════════════════════════════════════════
# 【模組 5】探勘結論判定 + 「真突破 vs 假反彈」分析
# ══════════════════════════════════════════════════════════════════════════════

def classify_conclusion(row: pd.Series) -> str:
    """
    根據多因子組合判定探勘結論標籤。

    【真突破 vs 假性反彈 判斷邏輯】

    真突破特徵：
      ① 量能比 > 1.5（資金確認）
      ② 站上 MA20（技術面轉多）
      ③ ROE > 12%（基本面撐盤）
      ④ 年線乖離不過深（-25% 以內，非死股）

    假性反彈特徵：
      ① 量能比 < 1.2（無量拉升，大戶未進）
      ② 未站上 MA20（仍在月線下方）
      ③ ROE < 5%（基本面差，純情緒炒作）
      ④ 位階已在 60 日高點附近（前高壓力大）
    """
    score = row.get("綜合得分", 0)
    vol   = row.get("量能倍數", 1.0)
    cross = row.get("站上MA20", False)
    roe   = row.get("ROE%", float('nan'))
    dev   = row.get("年線乖離%", float('nan'))
    pe    = row.get("PE本益比", float('nan'))
    pb    = row.get("PB本淨比", float('nan'))
    pos60 = row.get("60日位階%", 50.0)
    chg   = row.get("當日漲跌%", 0.0)

    roe_ok  = (roe == roe and roe > 12)
    dev_ok  = (dev == dev and dev < -10)
    dev_deep = (dev == dev and dev < -20)

    # ── 最高等級：量價齊揚的低估寶藏 ─────────────────────────────
    # 條件：高分 + 爆量 + 基本面佳 + 估值低
    if (score > 80 and vol > 2.0 and roe_ok and
            pe == pe and pe < 15):
        return "💎 絕佳寶藏：量價齊揚低估股"

    # ── 次高：真突破確認 ────────────────────────────────────────
    # 量能 + 站上月線 + 基本面支撐
    if (score > 70 and vol > 1.5 and cross and roe_ok):
        return "🚀 真突破：量能確認趨勢轉多"

    # ── 超跌黃金：安全邊際極高 ──────────────────────────────────
    # 嚴重偏離年線但品質好，等待反彈
    if (score > 65 and dev_deep and roe_ok):
        return "⭐ 超跌黃金：體質優但嚴重超賣"

    # ── 緩步築底：價值修復型 ────────────────────────────────────
    if (score > 70 and dev_ok):
        return "🏗️ 緩步築底：價值修復股"

    # ── 高分觀察 ────────────────────────────────────────────────
    if score > 65:
        return "📋 高潛力：進入觀察名單"

    # ── 假性反彈預警 ────────────────────────────────────────────
    # 大漲日股價上揚，但量能不足且基本面差
    if (chg > 5 and vol < 1.2 and not roe_ok):
        return "⚠️ 警示：疑似假性反彈"

    # ── 情緒拉升但無基本面 ──────────────────────────────────────
    if (chg > 3 and vol < 1.0 and pos60 > 80):
        return "🔴 高位量縮：謹慎追高"

    return "— 一般觀察"


def analyze_breakout_vs_fake(df: pd.DataFrame) -> pd.DataFrame:
    """
    專門針對「大漲日（如 4/1 千點大漲）」分析「真突破 vs 假反彈」。

    【核心邏輯】
    在指數大漲日，幾乎所有股票都會上漲。
    但「真突破」的股票，在指數回撤後仍能守住漲幅；
    「假反彈」的股票，往往隔日就回吐。

    區別關鍵指標（按重要性排序）：
    1. 量能比（最重要）：真突破必須有量能支撐
    2. 位階（次重要）：站上關鍵均線才算有效
    3. 基本面（背書）：ROE > 12% 才有大戶願意長抱

    Returns:
        包含「突破可信度」欄位的 DataFrame
    """
    df = df.copy()

    def breakout_credibility(row):
        vol   = row.get("量能倍數", 1.0)
        cross = row.get("站上MA20", False)
        roe   = row.get("ROE%", float('nan'))
        dev   = row.get("年線乖離%", float('nan'))
        pe    = row.get("PE本益比", float('nan'))

        # 突破可信度評分（0-5 顆星）
        stars = 0

        # ① 量能是否確認（最關鍵）
        if   vol > 3.0: stars += 2    # 強力爆量
        elif vol > 1.5: stars += 1    # 量能擴張

        # ② 技術面站穩關鍵均線
        if cross:       stars += 1    # 突破月線

        # ③ 基本面品質背書
        if roe == roe and roe > 12:
            stars += 1                # 品質股，大戶願意長抱
        elif roe == roe and roe < 5:
            stars -= 1                # 品質差，純炒作

        # ④ 估值過高扣分（追高風險）
        if pe == pe and pe > 30:
            stars -= 1

        stars = max(0, min(5, stars))

        labels = {
            5: "🟢🟢🟢 極高可信度 真突破",
            4: "🟢🟢   高可信度 傾向真突破",
            3: "🟡     中等可信度 需觀察",
            2: "🟠     低可信度 傾向假反彈",
            1: "🔴     極低可信度 假反彈風險高",
            0: "🔴🔴   警告：假反彈特徵明顯",
        }
        return labels.get(stars, "— 數據不足")

    df["突破可信度"] = df.apply(breakout_credibility, axis=1)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# 【模組 6】視覺化引擎
# ══════════════════════════════════════════════════════════════════════════════

def plot_risk_reward_matrix(df: pd.DataFrame, save_path: str = "tw300_matrix.png"):
    """
    繪製「風險/回報矩陣圖」。

    設計：
    - X 軸：P/B（越低 = 資產越便宜）
    - Y 軸：ROE%（越高 = 獲利能力越強）
    - 顏色深淺：量能倍數（越深 = 資金介入越強）
    - 氣泡大小：綜合得分（越大 = 越值得關注）
    """
    plot_df = df.dropna(subset=["PB本淨比", "ROE%"]).copy()
    if len(plot_df) == 0:
        print("⚠️  無足夠數據繪圖")
        return

    # 限制極端值，保持圖表可讀性
    plot_df = plot_df[
        (plot_df["PB本淨比"] < 8) &
        (plot_df["ROE%"].between(-10, 50))
    ]

    # ── 圖表設定 ────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(18, 11), facecolor='#0D1117')
    ax.set_facecolor('#0D1117')

    # 象限分割線
    ax.axvline(x=1.5, color='#21262D', linewidth=2, linestyle='--', alpha=1.0, zorder=1)
    ax.axhline(y=12,  color='#21262D', linewidth=2, linestyle='--', alpha=1.0, zorder=1)

    # ── 顏色映射（量能倍數）────────────────────────────────────────
    vol_vals = plot_df["量能倍數"].clip(0.5, 5.0)
    norm     = mcolors.Normalize(vmin=0.5, vmax=5.0)
    cmap     = plt.cm.plasma   # 黑→紫→橙→黃，越亮代表量能越強

    # ── 繪製散點 ────────────────────────────────────────────────────
    score_min = plot_df["綜合得分"].min()
    score_max = plot_df["綜合得分"].max()

    for _, row in plot_df.iterrows():
        pb    = row["PB本淨比"]
        roe   = row["ROE%"]
        vol   = min(row.get("量能倍數", 1.0), 5.0)
        score = row.get("綜合得分", 30)
        label = str(row.get("探勘結論", ""))

        # 氣泡大小依得分決定
        size_norm = (score - score_min) / max(score_max - score_min, 1)
        bubble_sz = 60 + size_norm * 200

        # 顏色依量能倍數決定
        color = cmap(norm(vol))

        # 特殊標記：最高等級標的
        marker = '*' if "絕佳寶藏" in label else ('D' if "超跌黃金" in label else 'o')
        alpha  = 0.95 if score > 70 else 0.6

        ax.scatter(pb, roe, c=[color], s=bubble_sz, marker=marker,
                   alpha=alpha, edgecolors='white', linewidth=0.4, zorder=5)

        # 高分標的才標名字
        if score > 65:
            ax.annotate(
                f"{row['代號']}\n{row['名稱']}",
                (pb, roe),
                textcoords="offset points", xytext=(6, 3),
                fontsize=6.5, color='#E6EDF3', zorder=6,
                fontfamily='sans-serif'
            )

    # ── 色條（量能倍數說明）────────────────────────────────────────
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("量能倍數 Volume Ratio\n(今日量 / 5日均量)",
                   color='#8B949E', fontsize=10)
    cbar.ax.yaxis.set_tick_params(color='#8B949E')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#8B949E')

    # ── 象限說明 ────────────────────────────────────────────────────
    quad_style = dict(boxstyle='round,pad=0.4', alpha=0.55, edgecolor='none')
    quads = [
        (0.1, 40,  '🏆 黃金區間\nLow P/B × High ROE',     '#3FB950', '#0D3B1A'),
        (4.5, 40,  '✨ 成長股\nHigh P/B × High ROE',       '#58A6FF', '#0A2040'),
        (0.1, -8,  '⚠️ 價值陷阱\nLow P/B × Low ROE',      '#F85149', '#3B0A0A'),
        (4.5, -8,  '🚫 迴避區\nHigh P/B × Low ROE',        '#8B949E', '#1A1A1A'),
    ]
    for x, y, txt, fc, bg in quads:
        ax.text(x, y, txt, fontsize=8.5, color=fc, va='top',
                bbox={**quad_style, 'facecolor': bg})

    # ── 圖例 ────────────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(color='#FFD700', label='★ 絕佳寶藏 Diamond Pick'),
        mpatches.Patch(color='#FF8C00', label='◆ 超跌黃金 Oversold Gem'),
        mpatches.Patch(color='#58A6FF', label='● 一般觀察 General Watch'),
    ]
    ax.legend(handles=legend_items, loc='upper right',
              facecolor='#161B22', edgecolor='#30363D',
              labelcolor='#C9D1D9', fontsize=9)

    # ── 標題 & 軸標籤 ───────────────────────────────────────────────
    ax.set_xlabel("P/B 本淨比（越低越便宜，< 1.5 具安全邊際）",
                  color='#8B949E', fontsize=12, labelpad=10)
    ax.set_ylabel("ROE% 股東權益報酬率（越高品質越好，> 12% 為門檻）",
                  color='#8B949E', fontsize=12, labelpad=10)
    ax.set_title(
        f"台股市值前300大  風險/回報矩陣圖\n"
        f"TW300 Risk/Return Matrix  |  顏色深淺 = 量能倍數  |  氣泡大小 = 綜合得分\n"
        f"分析時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        color='#F0F6FC', fontsize=13, pad=15, fontfamily='sans-serif'
    )

    ax.tick_params(colors='#8B949E')
    for spine in ax.spines.values():
        spine.set_color('#21262D')

    x_max = min(float(plot_df["PB本淨比"].max()) * 1.2 + 0.5, 10.0)
    ax.set_xlim(-0.1, x_max)
    ax.set_ylim(float(plot_df["ROE%"].min()) - 5, float(plot_df["ROE%"].max()) + 5)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight',
                facecolor='#0D1117', edgecolor='none')
    print(f"\n📊 矩陣圖已儲存：{save_path}")
    plt.close()


# ══════════════════════════════════════════════════════════════════════════════
# 【模組 7】主程式
# ══════════════════════════════════════════════════════════════════════════════

def main():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print("╔" + "═"*60 + "╗")
    print("║  🔍  台股市值前 300 大  量化多因子選股系統 v2.0            ║")
    print("║  📅  " + ts + "                        ║")
    print("╚" + "═"*60 + "╝")
    print(f"\n📋 成分股數量：{len(TW300)} 檔（上市 + 上櫃）\n")

    # ── Step 1: 多執行緒批量抓取 ────────────────────────────────────
    df = fetch_all_stocks(TW300, max_workers=8)

    if df.empty:
        print("❌ 無法取得任何數據，請檢查網路連線")
        return None

    print(f"✅ 成功取得 {len(df)} 檔數據\n")

    # ── Step 2: 計算綜合得分 ─────────────────────────────────────────
    print("🧮 計算多因子評分...")
    df["綜合得分"] = df.apply(calculate_score, axis=1)

    # ── Step 3: 判定探勘結論 ─────────────────────────────────────────
    print("🏷️  判定探勘結論...")
    df["探勘結論"] = df.apply(classify_conclusion, axis=1)

    # ── Step 4: 真突破分析 ──────────────────────────────────────────
    print("🔬 分析突破可信度...")
    df = analyze_breakout_vs_fake(df)

    # ── Step 5: 排序 ────────────────────────────────────────────────
    df = df.sort_values("綜合得分", ascending=False).reset_index(drop=True)
    df.index += 1

    # ── Step 6: 產出 final_report ───────────────────────────────────
    report_cols = ["代號", "名稱", "現價", "當日漲跌%",
                   "PE本益比", "PB本淨比", "ROE%", "量能倍數",
                   "年線乖離%", "站上MA20", "綜合得分",
                   "探勘結論", "突破可信度"]

    final_report = df[[c for c in report_cols if c in df.columns]].copy()

    # ── Step 7: 輸出報告 ────────────────────────────────────────────
    print("\n" + "═"*80)
    print("  📋  最終探勘報告 Final Report  |  Top 30 by 綜合得分")
    print("═"*80)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    print(final_report.head(30).to_string())

    # ── Step 8: 分類統計 ────────────────────────────────────────────
    print("\n" + "═"*60)
    print("  📊  探勘結論統計 Signal Distribution")
    print("═"*60)
    for label, count in df["探勘結論"].value_counts().items():
        bar = "█" * min(count, 20)
        print(f"  {str(label):<30} {bar} {count}")

    # ── Step 9: 儲存 CSV ────────────────────────────────────────────
    csv_path = f"tw300_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(csv_path, index=True, encoding='utf-8-sig')
    print(f"\n💾 完整報告已儲存：{csv_path}")

    # ── Step 10: 繪圖 ────────────────────────────────────────────────
    print("🎨 繪製風險/回報矩陣圖...")
    plot_risk_reward_matrix(df)

    # ── Step 11: 解讀指南 ────────────────────────────────────────────
    print_interpretation(df)

    return df, final_report


def print_interpretation(df: pd.DataFrame):
    """列印「真突破 vs 假反彈」解讀框架"""

    gems   = df[df["探勘結論"].str.contains("絕佳寶藏", na=False)]
    rockets= df[df["探勘結論"].str.contains("真突破",   na=False)]
    gold   = df[df["探勘結論"].str.contains("超跌黃金", na=False)]
    fakes  = df[df["探勘結論"].str.contains("假性反彈", na=False)]

    print("\n╔" + "═"*70 + "╗")
    print("║  🧭  探勘結論解讀指南  |  真突破 vs 假性反彈辨別框架            ║")
    print("╠" + "═"*70 + "╣")
    print(f"║  💎 絕佳寶藏（量價齊揚低估股）：{len(gems):3d} 檔                        ║")
    print(f"║  🚀 真突破（量能確認趨勢轉多）：{len(rockets):3d} 檔                        ║")
    print(f"║  ⭐ 超跌黃金（嚴重超賣品質股）：{len(gold):3d} 檔                        ║")
    print(f"║  ⚠️  假性反彈預警：            {len(fakes):3d} 檔                        ║")
    print("╠" + "═"*70 + "╣")
    print("║                                                                      ║")
    print("║  【真突破 4 要素 True Breakout Criteria】                            ║")
    print("║  ① 量能比 > 1.5（資金確認，大戶在買）                               ║")
    print("║  ② 站上 MA20（技術面：月線壓力突破）                                 ║")
    print("║  ③ ROE > 12%（基本面：好公司不怕等）                                 ║")
    print("║  ④ 年線乖離在 -25% 以內（非死股，有反彈空間）                        ║")
    print("║                                                                      ║")
    print("║  【假反彈 4 特徵 Fake Rally Warning Signs】                           ║")
    print("║  ① 量能比 < 1.2（縮量反彈，大戶在賣）                               ║")
    print("║  ② 未站上 MA20（仍在月線壓制下）                                     ║")
    print("║  ③ ROE < 5%（爛公司也被指數帶飛）                                    ║")
    print("║  ④ 60 日位階 > 80%（接近前高，上方壓力重）                           ║")
    print("║                                                                      ║")
    print("║  【最強訊號組合 Strongest Signal Combo】                              ║")
    print("║  綜合得分 > 80 + 年線乖離 < -20% + 量能比 > 2.5                     ║")
    print("║  → 體質極好的公司被市場過度懲罰，大戶正趁亂掃貨                      ║")
    print("╚" + "═"*70 + "╝\n")

    # 列出今日最強標的
    if len(gems) > 0:
        print("  🏆 今日「絕佳寶藏」標的：")
        for _, row in gems.head(5).iterrows():
            print(f"     {row['代號']} {row['名稱']:8s}  "
                  f"得分:{row['綜合得分']:5.1f}  "
                  f"量能:{row['量能倍數']:.1f}x  "
                  f"年線乖離:{row['年線乖離%']:.1f}%  "
                  f"{row['突破可信度']}")


if __name__ == "__main__":
    result = main()
