import streamlit as st

# 1. 페이지 기본 설정 및 타이틀
st.set_page_config(
    page_title="MBTI 포켓몬 & 직업 매칭",
    page_icon="🔮",
    layout="centered"
)

# 헤더 부분 (이모지와 꾸미기)
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>✨ MBTI 몬스터 연구소 ✨</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>나의 MBTI에 딱 맞는 포켓몬 파트너와 운명의 직업은 무엇일까요?</p>", unsafe_allow_html=True)
st.write("---")

# 2. MBTI 데이터베이스 (포켓몬 고유 번호 및 직업)
# 정수형 ID를 사용하여 가장 안정적인 GitHub Raw 이미지 주소와 매칭합니다.
MBTI_DATA = {
    "INTJ": {"name": "뮤츠 (Mewtwo)", "id": 150, "emoji": "🧠", "jobs": ["🗂️ 데이터 과학자", "🧠 AI 시스템 아키텍트", "🎯 전략 기획가"]},
    "INTP": {"name": "후딘 (Alakazam)", "id": 65, "emoji": "🔬", "jobs": ["💻 소프트웨어 엔지니어", "🔬 기초과학 연구원", "📊 보안 분석가"]},
    "ENTJ": {"name": "리자몽 (Charizard)", "id": 6, "emoji": "👑", "jobs": ["🚀 스타트업 CEO", "👔 경영 컨설턴트", "🏛️ 정책 분석가"]},
    "ENTP": {"name": "팬텀 (Gengar)", "id": 94, "emoji": "💡", "jobs": ["💡 신사업 기획자", "🎨 크리에이티브 디렉터", "📈 벤처 캐피탈리스트"]},
    
    "INFJ": {"name": "가디안 (Gardevoir)", "id": 282, "emoji": "🔮", "jobs": ["🏫 상담 심리사", "✍️ 작가/저널리스트", "🌱 환경 운동가"]},
    "INFP": {"name": "이브이 (Eevee)", "id": 133, "emoji": "🎨", "jobs": ["🎨 웹툰 작가/일러스트레이터", "🎵 음악 치료사", "📚 콘텐츠 에디터"]},
    "ENFJ": {"name": "토게키스 (Togekiss)", "id": 468, "emoji": "❤️", "jobs": ["👥 인사담당자(HRD) 전문가", "🌍 NGO 활동가", "🗣️ 스피치 코치"]},
    "ENFP": {"name": "뮤 (Mew)", "id": 151, "emoji": "🌈", "jobs": ["🎉 이벤트 기획자", "🛍️ 마케터", "🎬 크리에이터"]},
    
    "ISTJ": {"name": "메타그로스 (Metagross)", "id": 376, "emoji": "📐", "jobs": ["📊 회계사/세무사", "🔎 품질 관리(QA) 엔지니어", "⚖️ 법률 전문가"]},
    "ISFJ": {"name": "메가니움 (Meganium)", "id": 154, "emoji": "🏡", "jobs": ["🩺 간호사/의료 보건직", "🏫 초등 교사", "👶 아동 복지사"]},
    "ESTJ": {"name": "윈디 (Arcanine)", "id": 59, "emoji": "⚔️", "jobs": ["👮 경찰관/소방관", "🏢 프로젝트 매니저(PM)", "🏦 금융 자산 관리사"]},
    "ESFJ": {"name": "해피너스 (Blissey)", "id": 242, "emoji": "🤝", "jobs": ["🤝 서비스 기획/CS 매니저", "✈️ 항공 승무원", "🍎 영양사"]},
    
    "ISTP": {"name": "루카리오 (Lucario)", "id": 448, "emoji": "🔧", "jobs": ["🛠️ 엔지니어링 전문가", "🏎️ 카레이서/스포츠 선수", "🕵️ 과학 수사관"]},
    "ISFP": {"name": "피카츄 (Pikachu)", "id": 25, "emoji": "🎵", "jobs": ["🛋️ 인테리어 디자이너", "💐 플로리스트", "📸 사진작가"]},
    "ESTP": {"name": "괴력몬 (Machamp)", "id": 68, "emoji": "⚡", "jobs": ["📈 주식 트레이더", "🚒 구급대원", "🏋️ 스포츠 에이전트"]},
    "ESFP": {"name": "푸린 (Jigglypuff)", "id": 39, "emoji": "🎤", "jobs": ["🎤 연예인/뮤지컬 배우", "🛍️ 쇼핑호스트", "✈️ 여행 가이드"]}
}

# 3. 사용자 입력 (MBTI 선택)
mbti_list = sorted(list(MBTI_DATA.keys()))
selected_mbti = st.selectbox(
    "👉 당신의 MBTI를 선택하고 운명의 파트너를 만나보세요!",
    mbti_list,
    index=None,
    placeholder="여기를 눌러 선택하세요... 🔍"
)

# 4. 결과 출력 및 연출 효과
if selected_mbti:
    # 💥 흥미로운 시각 효과 팡팡!
    st.balloons()
    st.snow()
    
    data = MBTI_DATA[selected_mbti]
    
    # [💡 핵심 수정] 전 세계 개발자들이 애용하는 안정적인 공식 PokeAPI GitHub Raw 이미지 주소로 복구
    pokemon_image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{data['id'].png}"
    # 혹시 모를 내부 주소 매칭 에러 방지를 위해 안전한 포맷 스트링으로 한 번 더 확인
    pokemon_image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{int(data['id'])}.png"
    
    st.write("")
    st.markdown(f"<h2 style='text-align: center;'>🔮 {selected_mbti}의 결과 분석 🔮</h2>", unsafe_allow_html=True)
    
    # 레이아웃 분할 (좌측: 이미지, 우측: 설명 및 직업)
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown(f"<h3 style='text-align: center;'>{data['emoji']} {data['name']}</h3>", unsafe_allow_html=True)
        # 이미지를 깨짐 없이 웹앱에 띄우는 함수
        st.image(pokemon_image_url, use_container_width=True)
        
    with col2:
        st.success(f"🎉 **{selected_mbti}** 타입인 당신은 성향상 **{data['name']}**와(과) 완벽한 싱크로율을 자랑합니다!")
        
        st.markdown("### 💼 추천하는 운명의 직업 TOP 3")
        for i, job in enumerate(data['jobs'], 1):
            st.info(f"**{i}순위:** {job}")
            
    st.warning(f"💡 {data['name']}와 함께라면 어떤 업무든 마스터할 수 있을 거예요! 화이팅! 🔥")

else:
    st.info("⬆️ 위 드롭다운 메뉴에서 MBTI를 선택하면 화려한 효과와 함께 결과가 나타납니다! ✨")
