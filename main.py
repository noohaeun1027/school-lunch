from datetime import datetime
import pytz
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="학교 급식 알아보기", page_icon="🏫", layout="centered"
)

# --- [추가] 사이드바에 페이지 이동 링크 및 안내 배치 ---
st.sidebar.title("📌 페이지 이동")
st.sidebar.page_link("main.py", label="🏫 학교 검색 (메인)", icon="🏠")
st.sidebar.page_link(
    "pages/1_디저트_급식.py", label="🧁 송탄고 디저트 분석", icon="📅"
)
st.sidebar.divider()
st.sidebar.info(
    "왼쪽 메뉴에서 이동하고 싶은 페이지를 클릭하세요!"
)

# 메인 화면 타이틀
st.title("🏫 학교 급식 알아보기")

# NEIS API Base URLs
SCHOOL_INFO_URL = "https://open.neis.go.kr/hub/schoolInfo"
MEAL_INFO_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


# 1. 학교 이름 변환 함수 (약어 처리)
def get_search_keywords(school_name):
    """원래 이름과 약어를 풀어서 만든 대체 이름을 반환합니다."""
    keywords = [school_name.strip()]

    replaced = school_name.strip()
    replacements = [
        ("여자고등학교", "여자고등학교"),
        ("여자중학교", "여자중학교"),
        ("여고", "여자고등학교"),
        ("여중", "여자중학교"),
        ("남고", "남자고등학교"),
        ("남중", "남자중학교"),
        ("고등학교", "고등학교"),
        ("중학교", "중학교"),
        ("초등학교", "초등학교"),
        ("고", "고등학교"),
        ("중", "중학교"),
        ("초", "초등학교"),
    ]

    temp_name = replaced
    if "여고" in temp_name:
        temp_name = temp_name.replace("여고", "여자고등학교")
    elif "고" in temp_name and not temp_name.endswith("고등학교"):
        if temp_name.endswith("고"):
            temp_name = temp_name[:-1] + "고등학교"

    if temp_name != school_name and temp_name not in keywords:
        keywords.append(temp_name)

    return keywords


# 2. 학교 정보 조회 함수
def search_school(keyword):
    params = {"Type": "json", "SCHUL_NM": keyword, "pSize": 5}
    try:
        response = requests.get(SCHOOL_INFO_URL, params=params, timeout=5)
        data = response.json()

        if "schoolInfo" in data:
            rows = data["schoolInfo"][1]["row"]
            return rows
        return []
    except Exception:
        return []


# 3. 급식 정보 조회 함수
def get_meal_info(office_code, school_code, date_str):
    params = {
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": office_code,
        "SD_SCHUL_CODE": school_code,
        "MMEAL_SC_CODE": "2",  # 중식
        "MLSV_FROM_YMD": date_str,
        "MLSV_TO_YMD": date_str,
    }

    try:
        response = requests.get(MEAL_INFO_URL, params=params, timeout=5)
        data = response.json()

        if "mealServiceDietInfo" in data:
            rows = data["mealServiceDietInfo"][1]["row"]
            if rows:
                return rows[0]
        return None
    except Exception:
        return None


# --- UI 레이아웃 ---

# 학교 검색 입력
search_input = st.text_input(
    "학교 이름을 입력하세요", placeholder="예: 수도여고, 서울고"
)

selected_school = None

if search_input:
    keywords = get_search_keywords(search_input)
    schools = []

    for kw in keywords:
        results = search_school(kw)
        if results:
            schools = results
            break

    if not schools:
        st.warning("입력한 이름으로 학교를 찾을 수 없습니다.")
    else:
        school_options = {
            f"{sch['SCHUL_NM']} ({sch['LCTN_SC_NM']})": sch for sch in schools
        }

        selected_label = st.selectbox(
            "학교를 선택하세요", options=list(school_options.keys())
        )
        selected_school = school_options[selected_label]

st.divider()

# 날짜 선택 (한국 시간 KST 기준 오늘 날짜)
kst = pytz.timezone("Asia/Seoul")
today_kst = datetime.now(kst).date()

selected_date = st.date_input("날짜 선택", value=today_kst)

# 급식 조회 버튼 및 결과 출력
if selected_school:
    date_str = selected_date.strftime("%Y%m%d")

    meal_data = get_meal_info(
        selected_school["ATPT_OFCDC_SC_CODE"],
        selected_school["SD_SCHUL_CODE"],
        date_str,
    )

    st.subheader(
        f"🍱 {selected_school['SCHUL_NM']} ({selected_date.strftime('%Y년 %m월 %d일')}) 중식"
    )

    if meal_data:
        raw_menu = meal_data.get("DDISH_NM", "")
        formatted_menu = raw_menu.replace("<br/>", "\n")
        calorie_info = meal_data.get("CAL_INFO", "정보 없음")

        st.info(formatted_menu)
        st.caption(f"⚡ **칼로리:** {calorie_info}")
    else:
        st.error("해당 날짜에는 급식 정보가 없습니다.")
else:
    if search_input:
        st.info("위 목록에서 학교를 선택해 주세요.")
    else:
        st.info("학교 이름을 입력하면 급식 정보를 확인할 수 있습니다.")
