import streamlit as st
import random
import time

# --- 게임 설정 ---
DIFFICULTY = {
    "쉬움 (8x8)": (8, 8, 10),
    "보통 (16x16)": (16, 16, 40),
    "어려움 (24x24)": (24, 24, 99)
}

# 세션 초기화
if "board" not in st.session_state:
    st.session_state.started = False
    st.session_state.start_time = None
    st.session_state.board = []
    st.session_state.revealed = []
    st.session_state.flags = []
    st.session_state.game_over = False
    st.session_state.victory = False
    st.session_state.rows = 0
    st.session_state.cols = 0
    st.session_state.mines = 0

def new_game(level="쉬움 (8x8)"):
    rows, cols, mines = DIFFICULTY[level]
    board = [[0]*cols for _ in range(rows)]
    revealed = [[False]*cols for _ in range(rows)]
    flags = [[False]*cols for _ in range(rows)]

    # 지뢰 배치
    mine_positions = random.sample(range(rows*cols), mines)
    for m in mine_positions:
        r, c = divmod(m, cols)
        board[r][c] = -1
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != -1:
                    board[nr][nc] += 1

    st.session_state.started = True
    st.session_state.start_time = time.time()
    st.session_state.board = board
    st.session_state.revealed = revealed
    st.session_state.flags = flags
    st.session_state.rows = rows
    st.session_state.cols = cols
    st.session_state.mines = mines
    st.session_state.game_over = False
    st.session_state.victory = False

# 칸 열기
def reveal(r, c):
    if st.session_state.revealed[r][c] or st.session_state.flags[r][c]:
        return
    st.session_state.revealed[r][c] = True
    if st.session_state.board[r][c] == -1:
        st.session_state.game_over = True
        return
    if st.session_state.board[r][c] == 0:
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < st.session_state.rows and 0 <= nc < st.session_state.cols:
                    reveal(nr, nc)

# 깃발 토글
def toggle_flag(r, c):
    if not st.session_state.revealed[r][c]:
        st.session_state.flags[r][c] = not st.session_state.flags[r][c]

# 승리 판정
def check_victory():
    rows, cols = st.session_state.rows, st.session_state.cols
    for r in range(rows):
        for c in range(cols):
            if st.session_state.board[r][c] != -1 and not st.session_state.revealed[r][c]:
                return
    st.session_state.victory = True

# --- UI ---
st.title("💣 스트림릿 지뢰찾기")

level = st.sidebar.selectbox("난이도 선택", DIFFICULTY.keys())
if st.sidebar.button("새 게임 시작"):
    new_game(level)

if not st.session_state.started:
    st.info("왼쪽에서 난이도를 선택하고 새 게임을 시작하세요.")
    st.stop()

elapsed = int(time.time() - st.session_state.start_time)
st.sidebar.write(f"⏱ 경과 시간: {elapsed}초")

# 게임 보드 출력
rows, cols = st.session_state.rows, st.session_state.cols
for r in range(rows):
    cols_ui = st.columns(cols)
    for c in range(cols):
        if st.session_state.revealed[r][c]:
            val = st.session_state.board[r][c]
            if val == -1:
                cols_ui[c].button("💣", key=f"{r}-{c}", disabled=True)
            elif val == 0:
                cols_ui[c].button(" ", key=f"{r}-{c}", disabled=True)
            else:
                cols_ui[c].button(str(val), key=f"{r}-{c}", disabled=True)
        else:
            if st.session_state.flags[r][c]:
                if cols_ui[c].button("🚩", key=f"{r}-{c}"):
                    toggle_flag(r, c)
            else:
                if cols_ui[c].button("■", key=f"{r}-{c}"):
                    reveal(r, c)
                    check_victory()

# 게임 상태 메시지
if st.session_state.game_over:
    st.error("💥 게임 오버! 새로 시작하세요.")
elif st.session_state.victory:
    st.success("🎉 축하합니다! 모든 지뢰를 찾았습니다!")