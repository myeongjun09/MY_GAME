# 제목: Streamlit 턴제 RPG (보스 방 포함)
import streamlit as st
import random

# =========================
# 초기화
# =========================
if 'player' not in st.session_state:
    st.session_state.player = {
        'name': '',
        'hp': 100,
        'max_hp': 100,
        'attack': 10,
        'exp': 0,
        'level': 1,
        'inventory': []
    }
if 'room' not in st.session_state:
    st.session_state.room = 1
if 'game_over' not in st.session_state:
    st.session_state.game_over = False
if 'message' not in st.session_state:
    st.session_state.message = ''

# =========================
# 레벨업 함수
# =========================
def level_up():
    player = st.session_state.player
    exp_needed = player['level'] * 50
    while player['exp'] >= exp_needed:
        player['level'] += 1
        player['max_hp'] += 20
        player['hp'] = player['max_hp']
        player['attack'] += 5
        player['exp'] -= exp_needed
        st.session_state.message += f"\n레벨업! 현재 레벨: {player['level']}"

# =========================
# 몬스터 생성
# =========================
def spawn_monster(is_boss=False):
    if is_boss:
        return {'name': '보스', 'hp': 200, 'attack': 20, 'exp': 100}
    else:
        hp = random.randint(20, 50)
        attack = random.randint(5, 15)
        exp = random.randint(10, 30)
        return {'name': f'몬스터 Lv{st.session_state.room}', 'hp': hp, 'attack': attack, 'exp': exp}

# =========================
# 전투 함수
# =========================
def battle(monster):
    player = st.session_state.player
    st.session_state.message = f"{monster['name']}가 나타났다!\n"
    while monster['hp'] > 0 and player['hp'] > 0:
        # 플레이어 턴
        if st.button("공격"):
            damage = player['attack']
            monster['hp'] -= damage
            st.session_state.message += f"플레이어가 {damage} 피해를 입혔다. 몬스터 HP: {max(monster['hp'],0)}\n"
        if monster['hp'] <= 0:
            st.session_state.message += f"{monster['name']} 처치!\n"
            player['exp'] += monster['exp']
            level_up()
            break
        # 몬스터 턴
        damage = monster['attack']
        player['hp'] -= damage
        st.session_state.message += f"{monster['name']}가 {damage} 피해를 입혔다. 플레이어 HP: {max(player['hp'],0)}\n"
        if player['hp'] <= 0:
            st.session_state.game_over = True
            st.session_state.message += "플레이어가 사망했습니다. 게임 오버!"
            break

# =========================
# 방 진행
# =========================
st.title("턴제 RPG 게임")
player = st.session_state.player

# 캐릭터 생성
if player['name'] == '':
    name = st.text_input("캐릭터 이름을 입력하세요")
    if st.button("생성"):
        if name.strip() != '':
            st.session_state.player['name'] = name
            st.experimental_rerun()
else:
    st.write(f"캐릭터: {player['name']} | HP: {player['hp']}/{player['max_hp']} | 공격력: {player['attack']} | 레벨: {player['level']} | EXP: {player['exp']}")
    st.write(f"현재 방: {st.session_state.room}")

    if st.session_state.game_over:
        if st.button("재시작"):
            for key in ['player','room','game_over','message']:
                del st.session_state[key]
            st.experimental_rerun()
    else:
        if st.button("다음 방으로 이동"):
            # 보스 방 체크
            if st.session_state.room % 50 == 0:
                monster = spawn_monster(is_boss=True)
            else:
                event_type = random.choice(['monster','item','trap','nothing'])
                if event_type == 'monster':
                    monster = spawn_monster()
                elif event_type == 'item':
                    item = random.choice(['포션', '강화 물약'])
                    st.session_state.player['inventory'].append(item)
                    st.session_state.message = f"아이템 획득: {item}"
                    st.session_state.room += 1
                    st.experimental_rerun()
                elif event_type == 'trap':
                    damage = random.randint(5,15)
                    st.session_state.player['hp'] -= damage
                    st.session_state.message = f"함정에 걸려 {damage} 피해!"
                    st.session_state.room += 1
                    st.experimental_rerun()
                else:
                    st.session_state.message = "아무 일도 일어나지 않았다."
                    st.session_state.room += 1
                    st.experimental_rerun()
            # 전투 시작
            if 'monster' in locals():
                battle(monster)
                if not st.session_state.game_over:
                    st.session_state.room += 1

    st.text_area("게임 로그", value=st.session_state.message, height=300)