"""每天抓中央氣象署「鄉鎮天氣預報－未來1週」，只留有營地的鄉鎮，存成 cwa.json。
需要環境變數 CWA_API_KEY（放在 GitHub Secrets，不要寫進程式）。"""
import json, os, sys, time, urllib.parse, urllib.request, datetime

KEY = os.environ.get("CWA_API_KEY", "").strip()
if not KEY:
    sys.exit("CWA_API_KEY 未設定")
HERE = os.path.dirname(os.path.abspath(__file__))
WANT = {w.replace("臺", "台") for w in json.load(open(os.path.join(HERE, "cwa_towns.json"), encoding="utf-8"))}
IDS = [f"F-D0047-{n:03d}" for n in range(3, 88, 4)]  # 各縣市未來1週（003、007 … 087）
FIELD = {"最高溫度": "MaxTemperature", "最低溫度": "MinTemperature", "12小時降雨機率": "ProbabilityOfPrecipitation", "天氣現象": "Weather"}

def get(ds):
    u = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/{ds}?" + urllib.parse.urlencode({"Authorization": KEY, "format": "JSON"})
    for i in range(3):
        try:
            with urllib.request.urlopen(u, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            print(ds, "retry", i, e.__class__.__name__); time.sleep(5)
    return None

def num(v):
    try: return round(float(v))
    except Exception: return None

towns = {}
for ds in IDS:
    j = get(ds)
    if not j: continue
    for L in j.get("records", {}).get("Locations", []):
        county = L.get("LocationsName", "").replace("臺", "台")
        for loc in L.get("Location", []):
            key = county + loc.get("LocationName", "").replace("臺", "台")
            if key not in WANT: continue
            el = {e["ElementName"]: e["Time"] for e in loc.get("WeatherElement", []) if e.get("ElementName") in FIELD}
            base = el.get("天氣現象") or []
            rows = []
            for k, t in enumerate(base):
                def val(name, f):
                    arr = el.get(name) or []
                    if k < len(arr) and arr[k].get("ElementValue"): return arr[k]["ElementValue"][0].get(f)
                    return None
                ev = t["ElementValue"][0]
                rows.append([t["StartTime"][:16], ev.get("Weather", ""), ev.get("WeatherCode", ""),
                             num(val("最高溫度", "MaxTemperature")), num(val("最低溫度", "MinTemperature")),
                             num(val("12小時降雨機率", "ProbabilityOfPrecipitation"))])
            towns[key] = rows
    time.sleep(1)

if len(towns) < len(WANT) * 0.5:
    sys.exit(f"資料太少（{len(towns)}/{len(WANT)}），不更新")
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M")
out = {"issued": now, "source": "中央氣象署 鄉鎮天氣預報－未來1週", "towns": towns}
open(os.path.join(HERE, "..", "cwa.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print("towns", len(towns), "of", len(WANT))
