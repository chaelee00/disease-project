import streamlit as st
import pandas as pd
import pydeck as pdk

# -----------------------
# 데이터 불러오기 함수
# -----------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")

    # 컬럼명 정리 (공백 제거)
    df.columns = df.columns.str.strip()

    # 지역 이름 정리
    df['지역'] = df['Unnamed: 0']

    # 위도, 경도 매핑
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

    # 전국 제외 및 결측 제거
    df = df[df['지역'] != '전국']
    df = df.dropna(subset=['위도', '경도'])

    # 퍼센트 열만 추출하여 전처리
    percent_cols = [col for col in df.columns if '퍼센트' in col]
    for col in percent_cols:
        df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '').astype(float)

    return df, percent_cols

# -----------------------
# 앱 구성
# -----------------------
st.set_page_config(layout="wide")
df, percent_cols = load_data()

st.title("🦠 지역별 전염병 감염률 시각화")

# 전염병 선택
selected = st.selectbox("📌 전염병을 선택하세요", percent_cols)

# 색상 계산
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

# -----------------------
# 화면 구성
# -----------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ 감염률 지도")
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=36.5,
            longitude=127.8,
            zoom=5.5,
            pitch=45,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[경도, 위도]',
                get_radius="radius",
                get_fill_color="color",
                pickable=True,
            )
        ],
        tooltip={"text": "{지역}\n" + f"{selected}: {{{selected}}}%"}
    ))

with col2:
    st.subheader("📋 감염률 데이터")
    st.dataframe(
        df[['지역', selected]].sort_values(by=selected, ascending=False).reset_index(drop=True),
        use_container_width=True
    )
