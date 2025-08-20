import streamlit as st
import random

# 보드 크기와 지뢰 개수
ROWS, COLS = 8, 8
MINES = 10

# 세션 초기화
if "board" not in st.session_state:
    st.session_state.board = [[0]*COLS for _ in range(ROWS)]
    st.session_state.revealed = [[False]*COLS for _ in range(ROWS)]
    st.session_state.game_over = False
    
    # 지뢰 설치
    mines = random.sample(range(ROWS*COLS), MINES)
    for m in mines:
        r, c = divmod(m, COLS)
        st.session_state.board[r][c] = -1  # 지뢰는 -1
        # 주변 숫자 증가
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and st.session_state.board[nr][nc] != -1:
                    st.session_state.board[nr][nc] += 1

def reveal(r, c):
    if st.session_state.revealed[r][c]:
        return
    st.session_state.revealed[r][c] = True
    if st.session_state.board[r][c] == -1:
        st.session_state.game_over = True
    elif st.session_state.board[r][c] == 0:
        # 주변 자동 오픈
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    reveal(nr, nc)

# UI 출력
st.title("💣 지뢰찾기")

for r in range(ROWS):
    cols = st.columns(COLS)
    for c in range(COLS):
        if st.session_state.revealed[r][c]:
            if st.session_state.board[r][c] == -1:
                cols[c].button("💣", key=f"{r}-{c}", disabled=True)
            elif st.session_state.board[r][c] == 0:
                cols[c].button(" ", key=f"{r}-{c}", disabled=True)
            else:
                cols[c].button(str(st.session_state.board[r][c]), key=f"{r}-{c}", disabled=True)
        else:
            if cols[c].button("■", key=f"{r}-{c}"):
                reveal(r, c)

if st.session_state.game_over:
    st.error("게임 오버! 💥 새로고침해서 다시 시작하세요.")