import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(layout="wide")

# 한글 폰트 설정
font_path = os.path.join("fonts", "NanumGothic.ttf")
font_manager.fontManager.addfont(font_path)
plt.rc('font', family='NanumGothic')
plt.rcParams['axes.unicode_minus'] = False

# -----------------------------
# 데이터 로딩 함수
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df['지역'] = df['Unnamed: 0']

    coords = {
        '서울': (37.5665, 126.9780), '부산': (35.1796, 129.0756), '대구': (35.8714, 128.6014),
        '인천': (37.4563, 126.7052), '광주': (35.1595, 126.8526), '대전': (36.3504, 127.3845),
        '울산': (35.5384, 129.3114), '세종': (36.4801, 127.2890), '경기': (37.4138, 127.5183),
        '강원': (37.8228, 128.1555), '충북': (36.6358, 127.4917), '충남': (36.5184, 126.8000),
        '전북': (35.7167, 127.1442), '전남': (34.8161, 126.4630), '경북': (36.4919, 128.8889),
        '경남': (35.4606, 128.2132), '제주': (33.4996, 126.5312), '양주': (37.7853, 127.0459)
    }

    df['위도'] = df['지역'].map(lambda x: coords.get(x, (None, None))[0])
    df['경도'] = df['지역'].map(lambda x: coords.get(x, (None, None))[1])

    df = df[df['지역'] != '전국']
    df = df.dropna(subset=['위도', '경도'])

    percent_cols = [col for col in df.columns if '퍼센트' in col]
    for col in percent_cols:
        df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '').astype(float)

    return df, percent_cols

@st.cache_data
def load_past_data():
    return pd.read_csv("past_data.csv", encoding='utf-8')

# -----------------------------
# 데이터 준비
# -----------------------------
df, percent_cols = load_data()
past_df = load_past_data()
df.columns = df.columns.str.strip()
past_df.columns = past_df.columns.str.strip()

# -----------------------------
# 감염률 지도 시각화
# -----------------------------
st.title("🦠 지역별 전염병 감염률 시각화")
selected = st.selectbox("📌 전염병을 선택하세요", percent_cols)

min_val = df[selected].min()
max_val = df[selected].max()

def get_color(value):
    ratio = (value - min_val) / (max_val - min_val + 1e-5)
    r = int(255 * ratio)
    g = int(255 * (1 - ratio))
    b = 60
    return [r, g, b, 160]

df["color"] = df[selected].apply(get_color)
df["radius"] = df[selected] * 20000

# 지도 데이터 분리
yangju_df = df[df["지역"] == "양주"].copy()
gyeonggi_df = df[df["지역"] == "경기"].copy()
others_df = df[(df["지역"] != "양주") & (df["지역"] != "경기")]

# 아이콘 설정
yangju_icon = {
    "url": "https://cdn-icons-png.flaticon.com/512/684/684908.png",
    "width": 128,
    "height": 128,
    "anchorY": 128,
}
yangju_df["icon_data"] = [yangju_icon for _ in range(len(yangju_df))]

# 지도 + 표 표시
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ 감염률 지도")
    st.pydeck_chart(pdk.Deck(
        map_provider='carto',
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=37.6, longitude=127.1, zoom=7, pitch=45),
        layers=[
            pdk.Layer("ScatterplotLayer", data=others_df, get_position='[경도, 위도]',
                      get_radius="radius", get_fill_color="color", pickable=True),
            pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{"경도": 127.5183, "위도": 37.4138}]),
                      get_position='[경도, 위도]', get_radius=30000,
                      get_fill_color=[0, 100, 255, 40], pickable=False),
            pdk.Layer("IconLayer", data=yangju_df, get_icon="icon_data",
                      size_scale=15, get_position='[경도, 위도]', pickable=True),
        ],
        tooltip={"text": "{지역}\n" + selected + ": {" + selected + "}%"}
    ))
    st.markdown("🟥 감염률 높음 | 🟩 감염률 낮음")

with col2:
    st.subheader("📋 감염률 데이터")
    st.dataframe(
        df[['지역', selected]].sort_values(by=selected, ascending=False).reset_index(drop=True),
        use_container_width=True
    )

# -----------------------------
# 예측: 양주 & 경기 비교 예측
# -----------------------------
def predict_region_change(region_name, year_start, year_now, year_future):
    past_row = past_df[past_df['Unnamed: 0'] == region_name].squeeze()
    curr_row = df[df['지역'] == region_name].squeeze()

    cols = {
        '수두': '수두 퍼센트',
        '간염': '간염 퍼센트',
        '폐렴': '폐렴 퍼센트'
    }

    results = []
    for name, col in cols.items():
        try:
            past_val = float(past_row[col])
            curr_val = float(curr_row[col])
            diff = curr_val - past_val
            annual_growth = diff / (year_now - year_start)
            predicted = curr_val + annual_growth * (year_future - year_now)
            results.append({
                "질병": name,
                f"{year_start}년 감염률": round(past_val, 3),
                f"{year_now}년 감염률": round(curr_val, 3),
                f"예상 {year_future}년 감염률": round(predicted, 3)
            })
        except:
            continue

    return pd.DataFrame(results)

st.markdown("---")
with st.expander("📈 **양주 vs 경기도 감염률 예측 비교 (2014 → 2024 → 2034)**", expanded=True):
    pred_yangju_df = predict_region_change("양주", 2014, 2024, 2034)
    pred_gyeonggi_df = predict_region_change("경기", 2014, 2024, 2034)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### 📍 양주 예측")
        st.dataframe(pred_yangju_df, use_container_width=True)
    with col4:
        st.markdown("#### 📍 경기도 예측")
        st.dataframe(pred_gyeonggi_df, use_container_width=True)

    st.subheader("📊 양주 vs 경기도 감염률 변화 비교 그래프")
    labels = pred_yangju_df["질병"]
    x = range(len(labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([i - width for i in x], pred_yangju_df["2024년 감염률"], width=width, label='양주 2024')
    ax.bar(x, pred_gyeonggi_df["2024년 감염률"], width=width, label='경기 2024')
    ax.bar([i + width for i in x], pred_yangju_df["10년 후 예상 감염률"], width=width, label='양주 +10')
    ax.bar([i + 2*width for i in x], pred_gyeonggi_df["10년 후 예상 감염률"], width=width, label='경기 +10')

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("감염률 (%)")
    ax.set_title("양주 vs 경기도 감염률 예측 비교")
    ax.legend()

    st.pyplot(fig)
