# 台股量化多因子選股系統
## Taiwan Stock Quantitative Multi-Factor Screener

> **策略核心 Strategy Core**：好公司 (Quality) × 好價格 (Value) × 好時機 (Momentum) = 超額報酬  
> Good Company × Good Price × Good Timing = Alpha Returns

---

## 📁 專案檔案結構 | Project File Structure

| 檔案 File | 說明 Description |
|-----------|-----------------|
| `tw50_screener.py` | 台股前 50 大權值股選股引擎（TW50）<br>Screener engine for top 50 Taiwan blue-chip stocks |
| `tw300_screener.py` | 台股市值前 300 大選股引擎 v2.0（TW300）<br>Screener engine for top 300 Taiwan stocks by market cap |
| `TW50_Quant_Screener.ipynb` | TW50 選股系統 Jupyter Notebook 互動版<br>Interactive Jupyter Notebook version for TW50 |
| `TW300_MultiFactor_Screener.ipynb` | TW300 多因子選股系統 Jupyter Notebook 互動版<br>Interactive Jupyter Notebook version for TW300 |
| `requirements.txt` | Python 依賴套件清單 / Python dependency list |

---

## 🚀 快速上手 | Quick Start

### 安裝依賴套件 | Install Dependencies
```bash
pip install -r requirements.txt
```

### 執行 TW50 版本 | Run TW50 Version
```bash
python tw50_screener.py
```

### 執行 TW300 版本（推薦）| Run TW300 Version (Recommended)
```bash
python tw300_screener.py
```

---

## 🆚 TW50 vs TW300 版本差異 | Version Comparison

| 功能 Feature | `tw50_screener.py` | `tw300_screener.py` v2.0 |
|---|---|---|
| 涵蓋股票數 Coverage | ~50 檔 | ~300 檔 |
| 資料抓取方式 Data Fetch | 單執行緒循序 Sequential | **多執行緒並行 Multithreaded** |
| 評分架構 Scoring | 3 層，總分 100 | 3 層，總分 100（重新調校）|
| 格雷厄姆公式 Graham Formula | ❌ | ✅ PE × PB < 22.5 |
| 突破真假分析 Breakout Analysis | ❌ | ✅ 5 星可信度評分 |
| 60 日位階 60-Day Range | ❌ | ✅ |
| 市值分類 Market Cap Class | ❌ | ✅ 超大/大/中/小型 |
| 矩陣圖顏色 Matrix Color | 信號標籤 | **量能倍數漸層（plasma）** |
| 輸出報告 Output | `tw50_report_*.csv` | `tw300_report_*.csv` |
| 矩陣圖 Matrix Image | `tw50_matrix.png` | `tw300_matrix.png` |

---

## 📊 系統架構 | System Architecture

### TW50 架構
```
tw50_screener.py
│
├── 模組 1：成分股清單（TW50_COMPONENTS）
│         → 約 50 檔台灣前50大權值股
│
├── 模組 2：數據抓取引擎（fetch_stock_data）
│         → yfinance 循序抓取，每5檔暫停1秒
│         → 計算 MA5／MA20／MA60／MA200 及量能倍數
│         → 計算近5年平均殖利率
│
├── 模組 3：多維度評分引擎
│   ├── calculate_composite_score → 綜合得分（0~100分）
│   └── classify_signals          → 三大信號標籤判定
│
└── 模組 4：視覺化引擎
    ├── print_summary_table       → 終端機摘要表格
    ├── print_interpretation_guide→ 解讀指南與信號統計
    └── plot_risk_reward_matrix   → 風險/回報矩陣散佈圖
```

### TW300 架構（v2.0）
```
tw300_screener.py
│
├── 模組 1：成分股清單（TW300）
│         → 約 300 檔，涵蓋上市（.TW）＋上櫃（.TWO）
│         → 分類：超大型 Mega / 大型 Large / 中型 Mid / 小型 Small
│
├── 模組 2：單股數據抓取（fetch_single_stock）
│         → 計算 MA20／MA60／MA200、量能倍數、60日位階
│         → 新增：格雷厄姆公式判定、年線乖離率、市值分類
│
├── 模組 3：多執行緒批量抓取引擎（fetch_all_stocks）
│         → ThreadPoolExecutor，max_workers=8
│         → 即時進度條，預估剩餘時間
│
├── 模組 4：多因子評分引擎（calculate_score）
│         → 價值 40% + 品質 30% + 動能 30%
│         → 格雷厄姆公式加分機制
│
├── 模組 5：探勘結論判定（classify_conclusion）
│   └── analyze_breakout_vs_fake → 真突破 vs 假反彈分析
│
├── 模組 6：視覺化引擎（plot_risk_reward_matrix）
│         → 氣泡大小 = 綜合得分，顏色 = 量能倍數（plasma 色階）
│
└── 模組 7：主程式（main）
    └── print_interpretation → 解讀框架 + 今日最強標的
```

---

## 📈 量化因子完整說明 | All Quantitative Indicators

### 一、價值面因子 | Value Indicators

#### 📌 P/E 本益比（Price-to-Earnings Ratio）
- **定義**：股價 ÷ 每股盈餘（EPS），代表市場為每 1 元盈餘願意付出的價格
- **Definition**: Stock Price ÷ EPS. How much the market pays for $1 of earnings.
- **來源**：`info['trailingPE']`（過去12個月滾動）
- **評分邏輯**（TW300）：

| PE 範圍 | 得分 | 意義 |
|---------|------|------|
| < 8 | +18 | 極度低估，可能是週期谷底 Extremely undervalued |
| 8–12 | +15 | 低估 Undervalued |
| 12–15 | +12 | 合理偏低 Reasonably low |
| 15–20 | +6 | 合理 Fair |
| 20–25 | +2 | 稍貴 Slightly expensive |
| ≥ 25 | 0 | 昂貴 Expensive |

---

#### 📌 P/B 本淨比（Price-to-Book Ratio）
- **定義**：股價 ÷ 每股帳面淨值，代表市場為每 1 元帳面資產付出的價格
- **Definition**: Stock Price ÷ Book Value per Share. P/B < 1 means buying below liquidation value.
- **來源**：`info['priceToBook']`
- **評分邏輯**（TW300）：

| PB 範圍 | 得分 | 意義 |
|---------|------|------|
| < 0.8 | +15 | 嚴重低估（低於清算價值）Below liquidation value |
| 0.8–1.0 | +12 | 低於帳面值 Below book value |
| 1.0–1.5 | +9 | 合理偏低 Reasonably low |
| 1.5–2.0 | +5 | 合理 Fair |
| 2.0–3.0 | +2 | 稍高 Slightly high |
| ≥ 3.0 | 0 | 昂貴 Expensive |

---

#### 📌 格雷厄姆公式（Graham Formula）— TW300 專屬
- **定義**：`PE × PB < 22.5`，班傑明·格雷厄姆提出的「雙重低估」安全邊際標準
- **Definition**: Benjamin Graham's "double discount" safety margin: PE × PB < 22.5
- **邏輯**：同時滿足低估值（PE 低）且低市淨率（PB 低），是最嚴格的價值投資門檻
- **加分**：通過格雷厄姆公式 **+7 分**
- **欄位**：`格雷厄姆`（True/False）

---

#### 📌 殖利率（Dividend Yield）
- **TW50**：計算近5年年度股利 ÷ 年末股價，取平均（`平均殖利率%`）
- **TW300**：使用即時殖利率 `info['dividendYield']`（`殖利率%`）
- **金融意義**：現金回報率越高，持有成本越低；高殖利率股通常具防禦性

---

### 二、品質面因子 | Quality Indicators

#### 📌 ROE 股東權益報酬率（Return on Equity）
- **定義**：淨利 ÷ 股東權益，衡量公司用股東資金賺錢的效率
- **Definition**: Net Income ÷ Shareholders' Equity. Warren Buffett's most important metric.
- **來源**：`info['returnOnEquity']`（自動 ×100 換算成百分比）
- **評分邏輯**（TW300）：

| ROE 範圍 | 得分 | 意義 |
|----------|------|------|
| > 25% | +18 | 頂級：護城河深厚 Top-tier moat |
| 20–25% | +15 | 優質 Excellent |
| 15–20% | +12 | 良好 Good |
| 12–15% | +9 | 及格門檻 Minimum threshold |
| 8–12% | +5 | 一般 Average |
| 0–8% | +2 | 有盈利但效率低 Low efficiency |
| ≤ 0% | 0 | 虧損 Loss |

---

#### 📌 營業利益率（Operating Margin）
- **定義**：營業利益 ÷ 營業收入，反映本業真實競爭力，剔除業外收益干擾
- **Definition**: Operating Income ÷ Revenue. Reflects true business competitiveness, excluding non-operating items.
- **來源**：`info['operatingMargins']`（自動 ×100 換算）
- **評分邏輯**（TW300）：

| 營業利益率 | 得分 | 意義 |
|-----------|------|------|
| > 25% | +12 | 高護城河（半導體/軟體）High moat |
| 15–25% | +10 | 優質 Excellent |
| 10–15% | +7 | 良好 Good |
| 5–10% | +4 | 一般 Average |
| 0–5% | +1 | 薄利 Thin margin |
| ≤ 0% | 0 | 本業虧損 Operating loss |

---

### 三、技術動能因子 | Momentum Indicators

#### 📌 移動平均線（Moving Averages，MA）
- **MA5**（TW50 專屬）：5日均線，極短期趨勢參考
- **MA20**：月線（20日），最重要的短中期趨勢分界
- **MA60**：季線（60日），中期趨勢參考
- **MA200**：年線（200日），長期趨勢基準
- **計算方式**：`close.rolling(N).mean().iloc[-1]`

---

#### 📌 站上 MA20 / 穿越 MA20（Crossed MA20）
- **定義**：「昨日收盤在 MA20 之下，今日收盤突破到 MA20 之上」
- **Definition**: Yesterday's close was below MA20; today's close is at or above MA20.
- **金融意義**：短期趨勢由空轉多的技術轉折訊號（月線穿越）
- **計算**：`prev_close < prev_MA20 AND close >= MA20`
- **TW300 加分**：穿越 MA20 **+10 分**
- **欄位**：`站上MA20`（TW300） / `穿越MA20`（TW50）

---

#### 📌 量能倍數（Volume Ratio）
- **定義**：今日成交量 ÷ 近5日平均成交量
- **Definition**: Today's volume ÷ 5-day average volume
- **金融意義**：成交量是最誠實的資金流向指標
- **計算**：`volume[-1] / volume.rolling(5).mean()[-1]`
- **評分邏輯**（TW300）：

| 量能倍數 | 得分 | 意義 |
|---------|------|------|
| > 4.0x | +12 | 爆量，可能有重大利多 Major volume surge |
| 3.0–4.0x | +10 | 強勁爆量 Strong surge |
| 2.0–3.0x | +8 | 明顯放量 Notable increase |
| 1.5–2.0x | +6 | 量能擴張 Volume expansion |
| 1.2–1.5x | +3 | 量能略增 Slight increase |
| ≤ 1.2x | 0 | 量縮，無資金興趣 Shrinking volume |

---

#### 📌 年線乖離率（Deviation from MA200）
- **定義**：`(現價 − MA200) ÷ MA200 × 100%`，負值代表股價低於年線
- **Definition**: `(Price − MA200) ÷ MA200 × 100%`. Negative = trading below 200-day MA.
- **評分邏輯**（TW300）：

| 乖離率 | 得分 | 意義 |
|--------|------|------|
| < −25% | +8 | 嚴重超跌，歷史性低點 Extremely oversold |
| −25% ~ −15% | +6 | 明顯超跌 Clearly oversold |
| −15% ~ −10% | +4 | 偏低 Slightly low |
| −10% ~ −5% | +2 | 略低 Marginally low |
| > +10% | −2 | 已偏高，動能不利 Overbought |
| **欄位**：`年線乖離%`（TW300）/ `偏離年線%`（TW50）

---

#### 📌 60 日位階（60-Day Position）— TW300 專屬
- **定義**：`(現價 − 60日最低) ÷ (60日最高 − 60日最低) × 100%`
- **Definition**: Current position within the 60-day trading range (0% = low, 100% = high).
- **金融意義**：> 80% 代表接近60日高點，追高風險大；< 20% 代表處於近期低點
- **欄位**：`60日位階%`

---

#### 📌 市值分類（Market Cap Classification）— TW300 專屬
| 分類 | 中文 | 市值門檻（億台幣） |
|------|------|-----------------|
| Mega | 超大型 | > 10,000 億 |
| Large | 大型 | 3,000 – 10,000 億 |
| Mid | 中型 | 800 – 3,000 億 |
| Small | 小型 | < 800 億 |

---

## 🔍 選股策略 | Stock Selection Strategies

### 策略一：💎 被低估的寶藏（Value Discovery）
| 條件 Condition | 門檻 Threshold | 金融意義 Financial Meaning |
|------|------|----------|
| P/E < 15 | 本益比低 | 每賺 1 元只需付 15 元以下 |
| P/B < 1.5 | 本淨比低 | 接近或低於帳面清算價值 |
| ROE > 8% | 品質過關 | **排除「便宜但衰退」的價值陷阱** |

### 策略二：🚀 趨勢轉強（Momentum Signal）
| 條件 Condition | 門檻 | 金融意義 |
|------|------|----------|
| 穿越 MA20 | 昨在線下今在線上 | 短期趨勢由空轉多 |
| 量能倍數 > 1.2 | 今日量 / 5日均量 | 有資金積極介入確認 |

### 策略三：⭐ 超跌黃金（Safety Margin）
| 條件 Condition | 門檻 | 金融意義 |
|------|------|----------|
| 低於年線 > 10% | 年線乖離% < −10 | 股價遭市場過度懲罰 |
| ROE > 15% | 獲利能力仍強 | 基本面完好，非真正衰退 |

---

## 🧮 TW300 評分架構詳解 | TW300 Composite Score (0–100)

```
┌───────────────────────────────────────────────────────────────┐
│  分項 Category    權重 Weight   最高 Max   評分因子 Factors    │
├───────────────────────────────────────────────────────────────┤
│  價值 Value         40%          ~40 pts   PE, PB, Graham     │
│  品質 Quality       30%          ~30 pts   ROE, Op.Margin     │
│  動能 Momentum      30%          ~30 pts   Vol., MA20, MA200  │
└───────────────────────────────────────────────────────────────┘
```

| 得分範圍 | 意義 | 建議行動 |
|----------|------|----------|
| 70–100 | 三層因子高度共鳴 | **優先深入研究** |
| 50–69 | 部分因子表現優異 | 列入觀察名單 |
| 30–49 | 一般水準 | 不急於行動 |
| 0–29 | 訊號薄弱 | 暫時回避 |

---

## 🏷️ TW300 探勘結論標籤 | Signal Labels (TW300)

| 標籤 Label | 觸發條件 Trigger |
|-----------|----------------|
| 💎 絕佳寶藏：量價齊揚低估股 | 得分 > 80 + 量能 > 2.0x + ROE > 12% + PE < 15 |
| 🚀 真突破：量能確認趨勢轉多 | 得分 > 70 + 量能 > 1.5x + 站上MA20 + ROE > 12% |
| ⭐ 超跌黃金：體質優但嚴重超賣 | 得分 > 65 + 年線乖離 < −20% + ROE > 12% |
| 🏗️ 緩步築底：價值修復股 | 得分 > 70 + 年線乖離 < −10% |
| 📋 高潛力：進入觀察名單 | 得分 > 65 |
| ⚠️ 警示：疑似假性反彈 | 當日漲幅 > 5% + 量能 < 1.2x + ROE < 12% |
| 🔴 高位量縮：謹慎追高 | 當日漲幅 > 3% + 量能 < 1.0x + 60日位階 > 80% |
| — 一般觀察 | 其他狀況 |

---

## 🔬 突破可信度評分 | Breakout Credibility Score (TW300)

TW300 特有的「真突破 vs 假反彈」分析框架，以 0–5 星評分：

| 星級 | 標籤 | 條件說明 |
|------|------|---------|
| ★★★ 5星 | 🟢🟢🟢 極高可信度 真突破 | 量能爆量 + 站上MA20 + ROE優 + PE合理 |
| ★★★★ 4星 | 🟢🟢 高可信度 傾向真突破 | 大部分條件滿足 |
| ★★★ 3星 | 🟡 中等可信度 需觀察 | 量能確認或技術面擇一 |
| ★★ 2星 | 🟠 低可信度 傾向假反彈 | 量能不足或基本面差 |
| ★ 1星 | 🔴 極低可信度 假反彈風險高 | 多項負面條件 |
| 0星 | 🔴🔴 警告：假反彈特徵明顯 | ROE差 + 無量 + 追高 |

**評分規則 Scoring Logic：**
- 量能 > 3.0x → **+2**（最關鍵 Most critical）
- 量能 1.5–3.0x → **+1**
- 站上 MA20 → **+1**
- ROE > 12% → **+1**（品質背書）
- ROE < 5% → **−1**（品質差扣分）
- PE > 30 → **−1**（追高風險扣分）

---

## 📉 矩陣圖閱讀方式 | Risk/Return Matrix Guide

```
ROE% (Y軸 / Y-axis)
  ↑
30%│    🏆 黃金區間                    ✨ 高品質成長
   │  Low P/B × High ROE            High P/B × High ROE
12%│ - - - - - - - - - - - - - - - - - - - - - - - →
   │    ⚠️ 價值陷阱                    🚫 迴避區
 0%│  Low P/B × Low ROE             High P/B × Low ROE
   └────────────────────────────────────────→ P/B (X軸)
      0.8      1.5      2.0         3.0+
    （便宜 Cheap）  （合理 Fair）  （昂貴 Expensive）
```

**各視覺元素說明 Visual Elements：**
- **氣泡大小**（TW300）：綜合得分越高，氣泡越大
- **顏色深淺**（TW300）：量能倍數（plasma色階）：暗紫 → 亮黃，越亮代表資金越強
- **★ 星形標記**：探勘結論為「絕佳寶藏」
- **◆ 菱形標記**：探勘結論為「超跌黃金」
- **● 圓形標記**：一般觀察標的

---

## 🧭 必須立刻關注的信號組合 | High-Priority Signal Combos

### ① 雙重確認信號（最強，勝率最高）
```
💎 被低估 + 🚀 趨勢轉多 同時出現
→ 估值便宜（好價格）+ 資金介入（好時機）
→ 搭配 ROE > 15% = 三層共振，優先關注
```

### ② 超跌反轉機會
```
ROE > 15%（體質健康）
+ 低於年線 > 20%（股價嚴重超跌）
+ 量能倍數開始放大
→ 代表市場情緒過度悲觀，等待反彈時機
```

### ③ 量能爆發穿線（短線動能）
```
量能倍數 > 2.0（成交量暴增兩倍）
+ 當日突破 MA20（月線）
→ 強烈的資金進場訊號，技術面轉多
```

### ⚠️ 必須排除的「假便宜陷阱」
```
P/E < 10 但 ROE < 5% → 公司可能正在衰退（價值陷阱）  
P/B < 1.0 但 營業利益率 < 3% → 本業已無法獲利
```

---

## 💻 程式模組詳解 | Module Reference

### TW50：`fetch_stock_data(ticker, name, period_years=5)`
抓取單一股票數據，計算所有因子。回傳包含以下欄位的字典：

| 欄位 | 說明 | 類型 |
|------|------|------|
| `代號` | 股票代號 | str |
| `名稱` | 中文名稱 | str |
| `現價` | 最新收盤價 | float |
| `本益比(PE)` | 過去12個月本益比 | float |
| `本淨比(PB)` | 本淨比 | float |
| `平均殖利率%` | 近5年平均殖利率 | float |
| `ROE%` | 股東權益報酬率 | float |
| `營業利益率%` | 營業利益率 | float |
| `MA5/MA20/MA60/MA200` | 各均線值 | float |
| `量能倍數` | 今日量/5日均量 | float |
| `穿越MA20` | 是否剛突破月線 | bool |
| `偏離年線%` | 年線乖離率 | float |

---

### TW300：`fetch_single_stock(ticker, name, period_years=2)`
多執行緒版本，額外回傳：

| 欄位 | 說明 | 類型 |
|------|------|------|
| `格雷厄姆` | PE×PB < 22.5 | bool |
| `年線乖離%` | 偏離MA200百分比 | float |
| `60日位階%` | 近60日價格位置 | float |
| `市值億` | 市值（億台幣概估）| float |
| `市值分類` | 超大/大/中/小型 | str |
| `當日漲跌%` | 當日漲跌幅 | float |

---

### `fetch_all_stocks(components, max_workers=8)` — TW300 專屬
多執行緒批量抓取引擎：
- **ThreadPoolExecutor**：IO 密集型任務最佳方案，同時處理8檔股票的網路請求
- **as_completed**：哪個先完成就先處理，最大化效率
- **批次間暫停**：避免 Yahoo Finance API 速率限制
- **即時進度條**：顯示完成百分比、成功/失敗數、耗時

---

### `calculate_composite_score(row)` — TW50
```
價值層（40分）：PE < 20 → 8/15/20分；PB < 2 → 8/15/20分
品質層（35分）：ROE → 8/15/20分；營業利益率 → 5/10/15分
動能層（25分）：穿越MA20 → +15分；量能倍數 → +4/7/10分
```

### `calculate_score(row)` — TW300
```
價值項（最高~40分）：PE(18) + PB(15) + Graham(7)
品質項（最高~30分）：ROE(18) + 營業利益率(12)
動能項（最高~30分）：量能倍數(12) + 站上MA20(10) + 年線乖離(8)
```

---

### `classify_signals(df)` — TW50
為每檔股票貼三大策略標籤：`💎 被低估`、`🚀 趨勢轉多`、`⭐ 超跌黃金`

### `classify_conclusion(row)` — TW300
依多因子組合判定 8 種探勘結論標籤（見上方標籤表）

### `analyze_breakout_vs_fake(df)` — TW300
計算突破可信度（`突破可信度` 欄位），協助辨別大漲日的真假突破

---

## 📂 輸出檔案說明 | Output Files

| 檔案 | 說明 |
|------|------|
| `tw50_report_YYYYMMDD_HHMM.csv` | TW50 完整報表（可用 Excel 開啟，含所有因子）|
| `tw300_report_YYYYMMDD_HHMM.csv` | TW300 完整報表（含探勘結論、突破可信度）|
| `tw50_matrix.png` | TW50 風險/回報矩陣圖 |
| `tw300_matrix.png` | TW300 風險/回報矩陣圖（顏色代表量能強度）|
| `tw50_matrix_demo.png` | TW50 矩陣圖示範截圖 |

---

## 🔄 維護與更新 | Maintenance & Updates

### 手動更新成分股清單
每季度（3月、6月、9月、12月）台灣證交所會調整 0050 成分股：
- https://www.twse.com.tw/zh/indices/twse/MI_I005.html
- https://www.etf.com.tw/etf/0050

TW300 名單請參考台灣證交所市值排行：
- https://www.twse.com.tw/zh/products/indices/TWGTSi.html

### 代號格式 | Ticker Format
台股代號需加後綴，例如：
- 上市股票（TWSE）：`"2330.TW"`（台積電）
- 上櫃股票（OTC）：`"6488.TWO"`（環球晶）

### 調整多執行緒數量
如果 Yahoo Finance 回傳錯誤或資料缺失，可降低 `max_workers`：
```python
df = fetch_all_stocks(TW300, max_workers=4)  # 降低並發數
```

---

## ⚙️ 技術依賴 | Technical Dependencies

```
yfinance >= 0.2.40    # Yahoo Finance 數據抓取
pandas  >= 2.0.0      # 數據處理與 DataFrame
numpy   >= 1.24.0     # 數值計算
matplotlib >= 3.7.0   # 矩陣圖繪製（TW300 使用 plasma 色階）
```

---

## ⚠️ 免責聲明 | Disclaimer

本系統純屬量化學術研究工具，所有分析結果**不構成投資建議**。  
投資有風險，決策前請務必進行完整的個股基本面研究。

This system is purely an academic quantitative research tool. All analysis results **do not constitute investment advice**.  
Investing involves risk. Always conduct thorough fundamental research before making any investment decision.
