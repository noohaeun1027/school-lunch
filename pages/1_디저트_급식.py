import calendar
from datetime import datetime
import re
import pytz
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="우리 학교 달력별 급식", page_icon="📅", layout="centered"
)

st.title("📅 우리 학교 달력별 급식")
st.caption("송탄고등학교 전용 급식 및 디저트 통계 페이지")

# 송탄고등학교 고정 정보
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
]


# 알레르기 번호 제거 함수
def remove_allergy_info(menu_item):
    return re.sub(r"\([0-9\.]+\)", "", menu_item).strip()


# 디저트 여부 확인 함수
def is_dessert(menu_name):
    clean_name = remove_allergy_info(menu_name)
    return any(keyword in clean_name for keyword in DESSERT_KEYWORDS)


# 한 달 급식 데이터 전체 조회 함수
@st.cache_data(ttl=3600)  # API 요청을 줄이기 위한 캐싱
def get_monthly_meals(year, month):
    # 해당 월의 시작일과 마지막일 구하기
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
        "pSize": 100,  # 한 달 급식일은 보통 20일 안팎이므로 100건으로 한 번에 수신
    }

    try:
        response = requests.get(MEAL_INFO_URL, params=params, timeout=5)
        data = response.json()

        if "mealServiceDietInfo" in data:
            rows = data["mealServiceDietInfo"][1]["row"]
            # 날짜(YMD)를 키로 하는 사전 형태로 정리
            meal_dict = {row["MLSV_YMD"]: row for row in rows}
            return meal_dict
        return {}
    except Exception:
        return {}


# --- UI 레이아웃 ---

kst = pytz.timezone("Asia/Seoul")
today_kst = datetime.now(kst).date()

# 컨트롤 영역
col_date, col_toggle = st.columns([2, 1], vertical_alignment="bottom")

with col_date:
    selected_date = st.date_input("날짜 선택", value=today_kst)

with col_toggle:
    show_allergy = st.toggle("알레르기 정보 보기", value=True)

st.divider()

# 선택한 날짜의 연월 급식 데이터 가져오기
year = selected_date.year
month = selected_date.month
date_str = selected_date.strftime("%Y%m%d")

monthly_meals = get_monthly_meals(year, month)

# 1. 한 달간 디저트 통계 계산
total_dessert_count = 0
for day_data in monthly_meals.values():
    raw_menu = day_data.get("DDISH_NM", "")
    items = raw_menu.split("<br/>")
    # 그날 디저트가 하나라도 포함되었는지 체크
    has_dessert = any(is_dessert(item) for item in items if item.strip())
    if has_dessert:
        total_dessert_count += 1

# 통계 정보 출력
st.subheader(f"📊 {year}년 {month}월 디저트 통계")
st.metric(
    label=f"이번 달({month}월) 디저트가 나온 날",
    value=f"{total_dessert_count}회",
    help="메뉴명에 케이크, 푸딩, 음료, 과일, 아이스크림 등의 디저트 키워드가 포함된 날의 수입니다.",
)

st.divider()

# 2. 선택한 날짜의 상세 급식 정보
meal_data = monthly_meals.get(date_str)

st.subheader(
    f"🍽️ {selected_date.strftime('%Y년 %m월 %d일')} 급식 메뉴"
)

if meal_data:
    raw_menu_str = meal_data.get("DDISH_NM", "")
    items = [i.strip() for i in raw_menu_str.split("<br/>") if i.strip()]

    display_items = []
    dessert_items = []

    for item in items:
        item_text = item if show_allergy else remove_allergy_info(item)
        display_items.append(item_text)

        if is_dessert(item):
            dessert_items.append(remove_allergy_info(item))

    calorie_info = meal_data.get("CAL_INFO", "정보 없음")

    # 오늘 디저트 안내
    if dessert_items:
        st.success(f"🧁 오늘 나온 디저트: **{', '.join(dessert_items)}**")

    # 칼로리 정보
    st.caption(f"⚡ **오늘의 칼로리:** {calorie_info}")

    # 메뉴 카드로 출력 (3열 배치)
    cols = st.columns(3)
    for index, menu in enumerate(display_items):
        col = cols[index % 3]
        with col:
            with st.container(border=True):
                # 디저트 항목은 강조 표시
                if is_dessert(menu):
                    st.markdown(f"🧁 **{menu}**")
                else:
                    st.markdown(f"**{menu}**")
else:
    st.info("💡 급식이 없는 날입니다.")
