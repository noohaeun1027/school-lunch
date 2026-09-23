import calendar
from datetime import datetime
import re
import pytz
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="한 달 중 디저트는 몇 번?", page_icon="🧁", layout="centered"
)

st.title("🧁 송탄고 한 달 디저트 탐험")
st.caption("송탄고등학교 월별 디저트 빈도 분석 및 달력 급식 조회")

# 송탄고등학교 고정 정보 (나이스 개방 포털 문서 기준)
MEAL_INFO_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"
OFFICE_CODE = "J10"  # 경기도교육청
SCHOOL_CODE = "7530480"  # 송탄고등학교

# 디저트 판별 키워드 목록
DESSERT_KEYWORDS = [
    "케이크",
    "케익",
    "푸딩",
    "에이드",
    "주스",
    "쥬스",
    "라떼",
    "요거트",
    "요구르트",
    "아이스크림",
    "와플",
    "파이",
    "타르트",
    "쿠키",
    "빵",
    "도넛",
    "마카롱",
    "슈",
    "젤리",
    "식혜",
    "수정과",
    "과일",
    "바나나",
    "사과",
    "포도",
    "귤",
    "한라봉",
    "천혜향",
    "딸기",
    "수박",
    "참외",
    "멜론",
    "메론",
    "복숭아",
    "자두",
    "파인애플",
    "망고",
    "샤인머스캣",
    "플레인",
    "스무디",
    "초코",
    "바닐라",
]


# 메뉴에서 알레르기 번호 제거 함수
def remove_allergy_info(menu_item):
    return re.sub(r"\([0-9\.]+\)", "", menu_item).strip()


# 메뉴명이 디저트에 해당하는지 판별하는 함수
def is_dessert(menu_name):
    clean_name = remove_allergy_info(menu_name)
    return any(keyword in clean_name for keyword in DESSERT_KEYWORDS)


# 선택한 월 전체의 급식 정보를 가져오는 함수
@st.cache_data(ttl=3600)
def get_monthly_meals(year, month):
    _, last_day = calendar.monthrange(year, month)
    from_ymd = f"{year}{month:02d}01"
    to_ymd = f"{year}{month:02d}{last_day:02d}"

    params = {
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": OFFICE_CODE,
        "SD_SCHUL_CODE": SCHOOL_CODE,
        "MMEAL_SC_CODE": "2",  # 중식
        "MLSV_FROM_YMD": from_ymd,
        "MLSV_TO_YMD": to_ymd,
        "pSize": 100,  # 한 달 급식 데이터 전체 수신
    }

    try:
        response = requests.get(MEAL_INFO_URL, params=params, timeout=5)
        data = response.json()

        if "mealServiceDietInfo" in data:
            rows = data["mealServiceDietInfo"][1]["row"]
            return {row["MLSV_YMD"]: row for row in rows}
        return {}
    except Exception:
        return {}


# --- UI 레이아웃 ---

kst = pytz.timezone("Asia/Seoul")
today_kst = datetime.now(kst).date()

# 상단 입력 컨트롤 영역 (날짜 및 알레르기 스위치 나란히 배치)
col_date, col_toggle = st.columns([2, 1], vertical_alignment="bottom")

with col_date:
    selected_date = st.date_input("날짜 선택", value=today_kst)

with col_toggle:
    show_allergy = st.toggle("알레르기 정보 보기", value=True)

st.divider()

# 선택한 날짜 기준 연도/월/일 파싱
year = selected_date.year
month = selected_date.month
date_str = selected_date.strftime("%Y%m%d")

# 해당 월 전체 급식 데이터 조회
monthly_meals = get_monthly_meals(year, month)

# 1. 월간 디저트 통계 계산
total_meal_days = len(monthly_meals)
dessert_days_count = 0

for day_data in monthly_meals.values():
    raw_menu = day_data.get("DDISH_NM", "")
    items = raw_menu.split("<br/>")
    # 그날 디저트가 하나라도 포함되어 있는지 검사
    if any(is_dessert(item) for item in items if item.strip()):
        dessert_days_count += 1

# 디저트 통계 지표 카드 출력
st.subheader(f"📊 {year}년 {month}월 디저트 통계")
m1, m2 = st.columns(2)
m1.metric(label=f"{month}월 급식 제공일", value=f"{total_meal_days}일")
m2.metric(
    label=f"{month}월 디저트 나온 횟수",
    value=f"{dessert_days_count}회",
    delta=f"제공률 {round(dessert_days_count / total_meal_days * 100, 1)}%"
    if total_meal_days > 0
    else "0%",
)

st.divider()

# 2. 선택한 날짜의 상세 급식 보기
meal_data = monthly_meals.get(date_str)

st.subheader(f"🍽️ {selected_date.strftime('%Y년 %m월 %d일')} 메뉴 카드")

if meal_data:
    raw_menu_str = meal_data.get("DDISH_NM", "")
    items = [i.strip() for i in raw_menu_str.split("<br/>") if i.strip()]

    display_items = []
    today_desserts = []

    for item in items:
        item_text = item if show_allergy else remove_allergy_info(item)
        display_items.append(item_text)

        if is_dessert(item):
            today_desserts.append(remove_allergy_info(item))

    calorie_info = meal_data.get("CAL_INFO", "정보 없음")

    # 오늘 나온 디저트가 있다면 상단에 강조 표시
    if today_desserts:
        st.success(f"🧁 오늘 나온 디저트: **{', '.join(today_desserts)}**")

    st.caption(f"⚡ **오늘의 칼로리:** {calorie_info}")

    # 메뉴 가짓수와 식단 카드를 3열로 정렬하여 표시
    cols = st.columns(3)
    for index, menu in enumerate(display_items):
        col = cols[index % 3]
        with col:
            with st.container(border=True):
                if is_dessert(menu):
                    st.markdown(f"🧁 **{menu}**")
                else:
                    st.markdown(f"**{menu}**")
else:
    st.info("💡 급식이 없는 날입니다.")
