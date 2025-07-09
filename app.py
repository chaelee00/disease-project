pip install folium streamlit-folium
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ---------------------
# 데이터 로드 함수
# ---------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df.columns = df.columns.str.strip()
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

# ---------------------
# 앱 구성
# ---------------------
st.set_page_config(layout="wide")
df, percent_cols = load_data()

st.title("🦠 지역별 전염병 감염률 지도")

selected = st.selectbox("📌 전염병을 선택하세요", percent_cols)

# 지도 생성
if not df.empty:
    m = folium.Map(location=[36.5, 127.8], zoom_start=6)

    for _, row in df.iterrows():
        popup = f"{row['지역']}<br>{selected}: {row[selected]}%"
        color = 'red' if row[selected] > df[selected].mean() else 'green'

        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=row[selected] * 3,
            color=color,
            fill=True,
            fill_opacity=0.6,
            popup=popup
        ).add_to(m)

    st.subheader("📍 감염률 지도")
    st_folium(m, width=700, height=500)
else:
    st.info("데이터가 없습니다.")

# 표 출력
st.subheader("📋 감염률 데이터")
st.dataframe(
    df[['지역', selected]].sort_values(by=selected, ascending=False).reset_index(drop=True),
    use_container_width=True
)
