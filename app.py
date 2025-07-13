import streamlit as st
import pandas as pd
import pydeck as pdk

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
        '경남': (35.4606, 128.2132), '제주': (33.4996, 126.5312)
    }

    df['위도'] = df['지역'].map(lambda x: coords.get(x, (None, None))[0])
    df['경도'] = df['지역'].map(lambda x: coords.get(x, (None, None))[1])

    df = df[df['지역'] != '전국']
    df = df.dropna(subset=['위도', '경도'])

    percent_cols = [col for col in df.columns if '퍼센트' in col]
    for col in percent_cols:
        df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '').astype(float)

    return df, percent_cols

# -----------------------
# 앱 시작
# -----------------------
st.set_page_config(layout="wide")
df, percent_cols = load_data()

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

# 경기만 분리
gyeonggi_df = df[df["지역"] == "경기"].copy()
others_df = df[df["지역"] != "경기"]

# 핀 아이콘
icon_url = "https://cdn-icons-png.flaticon.com/512/684/684908.png"
icon_data = {
    "url": icon_url,
    "width": 128,
    "height": 128,
    "anchorY": 128,
}
gyeonggi_df["icon_data"] = [icon_data for _ in range(len(gyeonggi_df))]

# -----------------------
# 지도 + 표
# -----------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ 감염률 지도")
    st.pydeck_chart(pdk.Deck(
        map_provider='carto',
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=37.4138,  # 경기 중심
            longitude=127.5183,
            zoom=6.5,
            pitch=45,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=others_df,
                get_position='[경도, 위도]',
                get_radius="radius",
                get_fill_color="color",
                pickable=True,
            ),
            pdk.Layer(
                "IconLayer",
                data=gyeonggi_df,
                get_icon="icon_data",
                size_scale=15,  # get_size 제거
                get_position='[경도, 위도]',
                pickable=True,
            ),
        ],
        tooltip={"text": "{지역}\n" + selected + ": {" + selected + "}%"}
    ))

    # 색상 범례
    st.markdown("🟥 감염률 높음 | 🟩 감염률 낮음")

with col2:
    st.subheader("📋 감염률 데이터")
    st.dataframe(
        df[['지역', selected]].sort_values(by=selected, ascending=False).reset_index(drop=True),
        use_container_width=True
    )

# -----------------------
# 예측 기능: 경기도 기준 감염률 예측
# -----------------------

import pandas as pd

# 과거 데이터 불러오기
@st.cache_data
def load_past_data():
    return pd.read_csv("past_data.csv", encoding='utf-8')  # 확장자 없는 파일 불러오기

past_df = load_past_data()

st.markdown("---")
with st.expander("📈 **경기도 감염률 예측 (2015 → 현재 → 10년 후)**", expanded=False):
    past_gyeonggi = past_df[past_df['Unnamed: 0'] == '경기'].squeeze()
    current_gyeonggi = df[df['지역'] == '경기'].squeeze()

    disease_percent_cols = {
        '수두': '수두 퍼센트',
        '간염': '간염 퍼센트',
        '폐렴': '폐렴 퍼센트'
    }

    rows = []
    for name, col in disease_percent_cols.items():
        try:
            past_val = float(past_gyeonggi[col])
            curr_val = float(str(current_gyeonggi[col]).replace('%', '').replace(',', ''))
            diff = curr_val - past_val
            annual_growth = diff / 10
            predicted = curr_val + annual_growth * 10
            rows.append({
                "질병": name,
                "2015년 감염률": round(past_val, 3),
                "현재 감염률": round(curr_val, 3),
                "10년간 변화량": round(diff, 3),
                "예상 10년 후 감염률": round(predicted, 3)
            })
        except:
            continue

    pred_df = pd.DataFrame(rows)
    st.dataframe(pred_df, use_container_width=True)

import matplotlib.pyplot as plt

# 예측 그래프 그리기
st.subheader("📊 감염률 변화 시각화 (경기 지역)")

# 그래프용 데이터 정리
if not pred_df.empty:
    fig, ax = plt.subplots(figsize=(8, 5))
    width = 0.2
    x = range(len(pred_df))

    ax.bar([i - width for i in x], pred_df['2015년 감염률'], width=width, label='2015년')
    ax.bar(x, pred_df['현재 감염률'], width=width, label='현재')
    ax.bar([i + width for i in x], pred_df['예상 10년 후 감염률'], width=width, label='10년 후 예측')

    ax.set_xticks(x)
    ax.set_xticklabels(pred_df['질병'])
    ax.set_ylabel("감염률 (%)")
    ax.set_title("경기도 감염률 변화 예측")
    ax.legend()
    st.pyplot(fig)
else:
    st.info("예측할 데이터가 없습니다.")
