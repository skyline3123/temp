import requests
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, render_template
from datetime import datetime
#import urllib.parse
import math

app = Flask(__name__)

# 🔹 기상청 API에서 XML 데이터 가져오기
def get_weather_forecast(service_key):
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = "0500"
    #encoded_service_key = urllib.parse.quote(service_key)

    query_string = f"serviceKey={service_key}&pageNo=1&numOfRows=1000&dataType=XML&base_date={base_date}&base_time={base_time}&nx=60&ny=127"
    response = requests.get(url + "?" + query_string)

    if response.status_code != 200:
        print("❌ API 요청 실패:", response.text)
        return None
    return response.text

# 🔹 XML 데이터에서 기온(TMP) 및 습도(REH) 추출하여 체감온도 계산
def parse_weather_data(xml_data):
    root = ET.fromstring(xml_data)
    forecast_data = []
    temp_data = {}
    humidity_data = {}

    for item in root.findall(".//item"):
        category_element = item.find("category")
        fcst_date_element = item.find("fcstDate")  
        fcst_time_element = item.find("fcstTime")  
        fcst_value_element = item.find("fcstValue")  

        if fcst_date_element is not None and fcst_time_element is not None and fcst_value_element is not None:
            fcst_date = fcst_date_element.text  
            fcst_time = fcst_time_element.text  
            value_text = fcst_value_element.text.strip()  # 🔹 문자열 값 가져오기

            # 🔹 숫자가 아닌 값 필터링 (예: "강수없음", "흐림" 등)
            try:
                value = float(value_text)
            except ValueError:
                print(f"⚠️ 숫자로 변환할 수 없는 값 발견: {value_text} (무시됨)")
                continue  # 숫자가 아니면 건너뛰기

            if category_element.text == "TMP":  # 기온 데이터 저장
                temp_data[(fcst_date, fcst_time)] = value
            elif category_element.text == "REH":  # 습도 데이터 저장
                humidity_data[(fcst_date, fcst_time)] = value

    # 🔹 체감온도 계산 (기온(Ta), 습도(RH), 습구온도(Tw))
    for key in temp_data:
        Ta = temp_data[key]  
        RH = humidity_data.get(key, 50)  # 기본 습도 50%

        try:
            # 🔹 Stull의 습구온도(Tw) 계산
            Tw = (Ta * math.atan(0.151977 * ((RH + 8.313659) ** 0.5)) +
                  math.atan(Ta + RH) - math.atan(RH - 1.67633) +
                  0.00391838 * (RH ** (3/2)) * math.atan(0.023101 * RH) - 4.686035)

            # 🔹 체감온도 계산 공식 적용
            feels_like_temp = (-0.2442 + 0.55399 * Tw + 0.45535 * Ta - 
                               0.0022 * (Tw ** 2) + 0.00278 * Tw * Ta + 3.0)

            forecast_data.append({
                "date": key[0], 
                "time": key[1], 
                "feels_like": round(feels_like_temp, 1)
            })

        except Exception as e:
            print(f"🚨 체감온도 계산 오류: {e} (Ta={Ta}, RH={RH})")

    return forecast_data

@app.route("/")
def index():
    return render_template("index.html")

# 🔹 API 엔드포인트 (체감온도 데이터 반환)
@app.route("/api/weather")
def get_weather():
    service_key = "4WbcPl8cpZjq8VXOePfsXjYGid7SRm5olpV5s6WVU2qwe6cuzQCFIwqjhf45FV1x0fEtTkZnwFEoLZSG%2B69j6g%3D%3D"  # API 키 입력
    xml_data = get_weather_forecast(service_key)

    if xml_data:
        weather_data = parse_weather_data(xml_data)
        return jsonify(weather_data)

    return jsonify({"error": "데이터를 가져올 수 없습니다."})

if __name__ == "__main__":
    app.run(debug=True)
    
    






