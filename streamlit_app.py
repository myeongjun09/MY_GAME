import streamlit as st
import random

# 세션 초기화
if "player" not in st.session_state:
    st.session_state.player = {
        "level": 1,
        "hp": 30,
        "max_hp": 30,
        "atk": 5,
        "def": 2,
        "exp": 0,
        "gold": 0
    }
    st.session_state.room = 1
    st.session_state.log = ["게임 시작!"]
    st.session_state.monster = None

def log(message):
    st.session_state.log.append(message)

# 레벨업 체크
def check_levelup():
    player = st.session_state.player
    exp_needed = player["level"] * 10
    while player["exp"] >= exp_needed:
        player["exp"] -= exp_needed
        player["level"] += 1
        player["max_hp"] += 10
        player["atk"] += 2
        player["def"] += 1
        player["hp"] = player["max_hp"]
        log(f"🎉 레벨업! Lv.{player['level']} (HP+10, ATK+2, DEF+1)")
        exp_needed = player["level"] * 10

# 방 이벤트
def next_room():
    st.session_state.room += 1
    event = random.choice(["monster", "item", "shop", "trap", "nothing"])
    if event == "monster":
        monster = {
            "name": random.choice(["고블린", "슬라임", "스켈레톤"]),
            "hp": random.randint(10, 25),
            "atk": random.randint(3, 7),
            "def": random.randint(1, 3),
            "exp": random.randint(5, 10),
            "gold": random.randint(3, 8)
        }
        st.session_state.monster = monster
        log(f"⚔️ {monster['name']} 등장! (HP {monster['hp']})")
    elif event == "item":
        heal = random.randint(5, 15)
        st.session_state.player["hp"] = min(st.session_state.player["hp"] + heal, st.session_state.player["max_hp"])
        log(f"🍖 아이템 발견! HP {heal} 회복")
    elif event == "shop":
        cost = 10
        if st.session_state.player["gold"] >= cost:
            st.session_state.player["gold"] -= cost
            st.session_state.player["atk"] += 1
            log("🏪 상점: 무기를 강화했다! ATK +1")
        else:
            log("🏪 상점: 골드가 부족하다...")
    elif event == "trap":
        dmg = random.randint(5, 12)
        st.session_state.player["hp"] -= dmg
        log(f"💥 함정 발동! HP {dmg} 감소")
    else:
        log("😶 아무 일도 일어나지 않았다.")

# 전투
def attack():
    player = st.session_state.player
    monster = st.session_state.monster
    dmg = max(0, player["atk"] - monster["def"])
    monster["hp"] -= dmg
    log(f"👊 플레이어가 {monster['name']}에게 {dmg} 피해")

    if monster["hp"] <= 0:
        log(f"✅ {monster['name']} 처치! EXP {monster['exp']} / GOLD {monster['gold']} 획득")
        player["exp"] += monster["exp"]
        player["gold"] += monster["gold"]
        st.session_state.monster = None
        check_levelup()
        return

    # 몬스터 반격
    dmg = max(0, monster["atk"] - player["def"])
    player["hp"] -= dmg
    log(f"💢 {monster['name']}의 반격! {dmg} 피해")

    if player["hp"] <= 0:
        log("☠️ 플레이어가 쓰러졌다! 게임 오버!")

# --- UI ---
st.title("🧙 텍스트 RPG")

# 상태 표시
p = st.session_state.player
st.write(f"**Lv.{p['level']} HP:{p['hp']}/{p['max_hp']} ATK:{p['atk']} DEF:{p['def']} EXP:{p['exp']} Gold:{p['gold']}**")
st.write(f"현재 방: {st.session_state.room}")

# 전투 중인지 확인
if st.session_state.monster:
    m = st.session_state.monster
    st.write(f"👹 {m['name']} (HP {m['hp']})")
    if st.button("⚔️ 공격"):
        attack()
else:
    if st.button("➡️ 다음 방으로"):
        next_room()

# 로그 출력
st.write("### 로그")
for line in st.session_state.log[::-1][:10]:
    st.write(line)