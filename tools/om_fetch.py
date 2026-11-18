"""每天抓 Open-Meteo 熱點預報，存成 om_hot.json，讓網頁不必即時向 Open-Meteo 要 21 個地點的資料。
Weather data by Open-Meteo.com（CC BY 4.0）。不需要金鑰。"""
import json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HOTS = json.load(open(os.path.join(HERE, "hots.json"), encoding="utf-8"))
Q = {
    "latitude": ",".join(str(h["lat"]) for h in HOTS),
    "longitude": ",".join(str(h["lon"]) for h in HOTS),
    "elevation": ",".join(str(h["alt"]) for h in HOTS),
    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_gusts_10m_max,sunset",
    "hourly": "precipitation,temperature_2m,relative_humidity_2m,dew_point_2m,visibility",
    "wind_speed_unit": "ms", "timezone": "Asia/Taipei", "past_days": "2", "forecast_days": "8",
}
url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(Q)
data = None
for i in range(4):
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            data = json.load(r); break
    except Exception as e:
        print("retry", i, e); time.sleep(20)
if not isinstance(data, list) or len(data) != len(HOTS):
    sys.exit("Open-Meteo 資料不完整，不更新")
keep = []
for x in data:
    keep.append({"daily": x["daily"], "hourly": x["hourly"]})
out = {"at": int(time.time() * 1000), "names": [h["t"] for h in HOTS], "v": keep}
open(os.path.join(HERE, "..", "om_hot.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print("ok", len(keep))
