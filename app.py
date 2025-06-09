import streamlit as st
import pandas as pd
import pydeck as pdk

# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv("2024 기본통계_지역별 - 기본통계_지역별.csv")
    
    # 지역명
    df['지역'] = df['Unnamed: 0']
    
    # 위도/경도 매핑
    region_coords = {
        '서울': (37.5665, 126.9780), '부산': (35.1796, 129.0756), '대구': (35.8714, 128.6014),
        '인천': (37.4563, 126.7052), '광주': (35.1595, 126.8526), '대전': (36.3504, 127.3845),
        '울산': (35.5384, 129.3114), '세종': (36.4801, 127.2890), '경기': (37.4138, 127.5183),
        '강원': (37.8228, 128.1555), '충북': (36.6358, 127.4917), '충남': (36.5184, 126.8000),
        '전북': (35.7167, 127.1442), '전남': (34.8161, 126.4630), '경북': (36.4919, 128.8889),
        '경남': (35.4606, 128.2132), '제주': (33.4996, 126.5312)
    }
    
    df['위도'] = df['지역'].map(lambda x: region_coords.get(x, (None, None))[0])
    df['경도'] = df['지역'].map(lambda x: region_coords.get(x, (None, None))[1])
    df = df[df['지역'] != '전국']
    df = df.dropna(subset=['위도', '경도'])
    return df

# 데이터 로드
df = load_data()

# 전염병 선택
disease = st.selectbox("전염병을 선택하세요", ("수두", "간염", "폐렴"))
column_map = {"수두": "수두 퍼센트", "간염": "간염 퍼센트", "폐렴": "폐렴 퍼센트"}
selected_col = column_map[disease]

st.subheader(f"📍 {disease} 감염률 지도")

# 지도 시각화
st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=pdk.ViewState(
        latitude=36.5,
        longitude=127.8,
        zoom=5.5,
        pitch=40,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position='[경도, 위도]',
            get_radius=f"{selected_col} * 20000",
            get_fill_color='[255, 0, 0, 160]',
            pickable=True,
        )
    ],
    tooltip={"text": "{지역}\n" + f"{disease} 감염률: {{{selected_col}}}%"}
))
