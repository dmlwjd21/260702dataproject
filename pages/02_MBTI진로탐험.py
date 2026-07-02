import streamlit as st
import random
import urllib.request

# ──────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="MBTI 포켓몬 진로 탐험대",
    page_icon="🧬",
    layout="centered"
)

# ──────────────────────────────────────────────
# MBTI × 포켓몬 × 진로 데이터
# 이미지: PokeAPI 공식 아트워크 (별도 라이브러리 없이 URL만 사용)
# ──────────────────────────────────────────────
MBTI_DATA = {
    "INTJ": {"emoji": "🧠", "pokemon": "És/알라카잠", "poke_kr": "알라카잠", "id": 65,
              "desc": "치밀한 전략가! 미래를 내다보는 초능력자 타입 🔮",
              "jobs": ["데이터 과학자 📊", "경영 전략 컨설턴트 ♟️", "AI 연구원 🤖"],
              "color": "#4B0082"},
    "INTP": {"emoji": "🧪", "pokemon": "폴리곤", "poke_kr": "폴리곤", "id": 137,
              "desc": "논리와 코드로 세상을 분석하는 디지털 사색가 💾",
              "jobs": ["소프트웨어 엔지니어 💻", "물리학자 🌌", "게임 개발자 🎮"],
              "color": "#2F4F4F"},
    "ENTJ": {"emoji": "🔥", "pokemon": "리자몽", "poke_kr": "리자몽", "id": 6,
              "desc": "타고난 리더! 무리를 이끄는 카리스마 폭발 🐉",
              "jobs": ["CEO / 창업가 🚀", "경영 컨설턴트 📈", "정치인 🏛️"],
              "color": "#FF4500"},
    "ENTP": {"emoji": "😈", "pokemon": "팬텀", "poke_kr": "팬텀", "id": 94,
              "desc": "재치 넘치는 도전자! 새로운 아이디어의 장난꾸러기 💡",
              "jobs": ["스타트업 창업가 🚀", "광고 기획자 🎬", "변호사 ⚖️"],
              "color": "#6A0DAD"},
    "INFJ": {"emoji": "🌙", "pokemon": "가디안", "poke_kr": "가디안", "id": 282,
              "desc": "조용하지만 깊은 통찰의 신비주의자 ✨",
              "jobs": ["상담 심리사 🧑‍⚕️", "작가 ✍️", "사회복지사 🤝"],
              "color": "#9370DB"},
    "INFP": {"emoji": "🌸", "pokemon": "이브이", "poke_kr": "이브이", "id": 133,
              "desc": "무한한 가능성을 품은 순수한 몽상가 🌈",
              "jobs": ["예술가 🎨", "소설가 📖", "사회운동가 🌱"],
              "color": "#DDA0DD"},
    "ENFJ": {"emoji": "🌟", "pokemon": "루카리오", "poke_kr": "루카리오", "id": 448,
              "desc": "사람들의 마음을 읽고 이끄는 따뜻한 선도자 💙",
              "jobs": ["교사 👩‍🏫", "인사(HR) 매니저 🧑‍💼", "커뮤니티 리더 🤗"],
              "color": "#1E90FF"},
    "ENFP": {"emoji": "🎉", "pokemon": "피카츄", "poke_kr": "피카츄", "id": 25,
              "desc": "에너지 넘치는 자유로운 영혼! 어디서든 반짝반짝 ⚡",
              "jobs": ["이벤트 기획자 🎪", "마케터 📣", "배우/방송인 🎤"],
              "color": "#FFD700"},
    "ISTJ": {"emoji": "🛡️", "pokemon": "메타그로스", "poke_kr": "메타그로스", "id": 376,
              "desc": "철두철미! 규칙과 신뢰의 강철 심장 ⚙️",
              "jobs": ["공인회계사 🧾", "공무원 🏢", "시스템 엔지니어 🔧"],
              "color": "#708090"},
    "ISFJ": {"emoji": "🤲", "pokemon": "럭키", "poke_kr": "럭키", "id": 113,
              "desc": "따뜻하게 남을 돌보는 든든한 수호자 💗",
              "jobs": ["간호사 🩺", "사서 📚", "사회복지사 🏠"],
              "color": "#FFB6C1"},
    "ESTJ": {"emoji": "📋", "pokemon": "괴력몬", "poke_kr": "괴력몬", "id": 68,
              "desc": "추진력 만렙! 조직을 움직이는 실행형 리더 💪",
              "jobs": ["프로젝트 매니저 📅", "군인/경찰 🚓", "생산관리자 🏭"],
              "color": "#B22222"},
    "ESFJ": {"emoji": "🎀", "pokemon": "밀로틱", "poke_kr": "밀로틱", "id": 350,
              "desc": "사교적이고 배려심 넘치는 분위기 메이커 🥰",
              "jobs": ["이벤트 플래너 🎊", "초등 교사 🍎", "인사 담당자 🧑‍💼"],
              "color": "#FF69B4"},
    "ISTP": {"emoji": "🔩", "pokemon": "스라크", "poke_kr": "스라크", "id": 123,
              "desc": "손끝의 마법사! 문제를 해결하는 실전형 장인 ⚒️",
              "jobs": ["자동차/항공 정비사 ✈️", "응급구조사 🚑", "파일럿 🛩️"],
              "color": "#556B2F"},
    "ISFP": {"emoji": "🎨", "pokemon": "샤미드", "poke_kr": "샤미드", "id": 134,
              "desc": "감성 충만! 조용히 아름다움을 창조하는 예술가 🌊",
              "jobs": ["디자이너 🖌️", "사진작가 📷", "셰프 👨‍🍳"],
              "color": "#20B2AA"},
    "ESTP": {"emoji": "⚡", "pokemon": "초염몽", "poke_kr": "초염몽", "id": 392,
              "desc": "행동파! 짜릿한 순간을 즐기는 액션 스타 🔥",
              "jobs": ["프로 스포츠 선수 🏅", "영업/세일즈 전문가 💼", "응급구조대원 🚒"],
              "color": "#FF6347"},
    "ESFP": {"emoji": "🎤", "pokemon": "푸린", "poke_kr": "푸린", "id": 39,
              "desc": "무대 위의 스타! 흥과 끼가 넘치는 엔터테이너 🎈",
              "jobs": ["배우 🎬", "방송인/유튜버 📹", "이벤트 MC 🎙️"],
              "color": "#FF1493"},
}

POKE_IMG_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{}.png"

# ──────────────────────────────────────────────
# 이미지를 서버(Streamlit Cloud) 쪽에서 미리 받아와 페이지에 내장
# → 학교/기관 네트워크가 GitHub 도메인을 막아도 이미지가 정상 표시됨
# (표준 라이브러리 urllib만 사용, 별도 설치 불필요)
# ──────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_pokemon_image(poke_id: int):
    url = POKE_IMG_URL.format(poke_id)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            return response.read()
    except Exception:
        return None

# ──────────────────────────────────────────────
# CSS 효과 (그라디언트 배경, 카드 애니메이션, 이모지 흩날리기)
# ──────────────────────────────────────────────
st.markdown("""
<style>
@keyframes gradientShift {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}
.stApp {
    background: linear-gradient(-45deg, #FDEB71, #F8D800, #ee9ca7, #ffdde1, #a1c4fd, #c2e9fb);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
}
@keyframes floatUp {
    0% {transform: translateY(0) rotate(0deg); opacity: 1;}
    100% {transform: translateY(-120px) rotate(360deg); opacity: 0;}
}
.emoji-float {
    display: inline-block;
    animation: floatUp 2.5s ease-in infinite;
    font-size: 28px;
}
@keyframes popIn {
    0% {transform: scale(0.5); opacity: 0;}
    70% {transform: scale(1.08);}
    100% {transform: scale(1); opacity: 1;}
}
.result-card {
    animation: popIn 0.6s ease-out;
    border-radius: 24px;
    padding: 28px;
    text-align: center;
    box-shadow: 0 8px 28px rgba(0,0,0,0.25);
    margin-top: 10px;
}
@keyframes wiggle {
    0%, 100% {transform: rotate(-2deg);}
    50% {transform: rotate(2deg);}
}
.job-badge {
    display: inline-block;
    background: white;
    color: #333;
    padding: 10px 18px;
    margin: 6px;
    border-radius: 999px;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    animation: wiggle 1.8s ease-in-out infinite;
}
.title-glow {
    text-align: center;
    font-size: 42px;
    font-weight: 900;
    text-shadow: 0 0 12px rgba(255,255,255,0.8);
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 타이틀
# ──────────────────────────────────────────────
st.markdown('<div class="title-glow">🧬 MBTI 포켓몬 진로 탐험대 🧭</div>', unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; font-size:18px;'>당신의 MBTI를 고르면, 어울리는 포켓몬과 딱 맞는 진로 3가지를 알려드려요! 🎯</p>",
    unsafe_allow_html=True
)

floating_emojis = "".join(
    f'<span class="emoji-float" style="animation-delay:{i*0.3}s;">{e}</span> '
    for i, e in enumerate(["✨", "🎈", "⭐", "🌈", "💫", "🎊"])
)
st.markdown(f"<div style='text-align:center;'>{floating_emojis}</div>", unsafe_allow_html=True)

st.write("")

# ──────────────────────────────────────────────
# MBTI 선택
# ──────────────────────────────────────────────
mbti_list = list(MBTI_DATA.keys())
selected = st.selectbox(
    "🔍 당신의 MBTI를 선택하세요",
    mbti_list,
    format_func=lambda x: f"{MBTI_DATA[x]['emoji']}  {x}"
)

go = st.button("✨ 나의 포켓몬 & 진로 확인하기 ✨", use_container_width=True)

if go:
    data = MBTI_DATA[selected]
    st.balloons()

    st.markdown(
        f"""
        <div class="result-card" style="background: linear-gradient(135deg, {data['color']}22, {data['color']}55);">
            <h2 style="margin-bottom:0;">{data['emoji']} {selected} {data['emoji']}</h2>
            <p style="font-size:16px; color:#444;">{data['desc']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        img_bytes = load_pokemon_image(data["id"])
        if img_bytes:
            st.image(img_bytes, caption=f"당신의 포켓몬: {data['poke_kr']} 🎴", use_container_width=True)
        else:
            st.warning("🙁 이미지를 불러오지 못했어요. 네트워크 상태를 확인하거나 아래 링크를 눌러보세요.")
            st.markdown(f"[🖼️ {data['poke_kr']} 이미지 직접 보기]({POKE_IMG_URL.format(data['id'])})")

    st.markdown("<h3 style='text-align:center;'>💼 추천 진로 TOP 3</h3>", unsafe_allow_html=True)
    badges_html = "".join(f'<span class="job-badge">{job}</span>' for job in data["jobs"])
    st.markdown(f"<div style='text-align:center;'>{badges_html}</div>", unsafe_allow_html=True)

    st.write("")
    st.info(f"🎓 {selected} 유형은 **{data['poke_kr']}**처럼 {data['desc'].split('!')[0]}인 특징을 가지고 있어요. 위 진로들을 탐색해보세요!")

    if random.random() < 0.3:
        st.snow()
else:
    st.markdown(
        "<p style='text-align:center; color:#666;'>👆 MBTI를 선택하고 버튼을 눌러보세요!</p>",
        unsafe_allow_html=True
    )

st.markdown("---")
st.caption("🧑‍🏫 진로 탐색 수업용 웹앱 | Made with Streamlit 🎈 | 이미지 출처: PokeAPI")
