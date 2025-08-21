import streamlit as st
import random
import collections # 아이템 개수를 세기 위해 collections 모듈을 임포트합니다.
from typing import Dict, List, Any

# -----------------------------
# 초기 설정 및 상태 키 상수
# -----------------------------
BOSS_INTERVAL = 50 # 보스 몬스터가 등장하는 방 간격
FINAL_BOSS_ROOM = 250 # 최종 보스가 등장하는 방 번호

# 세션 상태에 저장될 주요 키 목록
STATE_KEYS = [
    "player", "room", "mode", "monster", "log",
    "defending", "shop_offer", "initial_monster_hp",
    "game_over", "game_clear"
]

# 무기 티어와 해당 무기가 제공하는 공격력 보너스 정의
WEAPON_TIERS: Dict[str, int] = {
    "낡은 검": 0,
    "돌 검": 5,
    "철 검": 10,
    "강철 검": 20,
    "미스릴 검": 35,
    "전설의 검": 50
}
WEAPON_ORDER = list(WEAPON_TIERS.keys()) # 무기 업그레이드 순서를 위한 리스트

# -----------------------------
# 유틸리티 함수 / 초기화
# -----------------------------
def init_game():
    """게임 전체 상태를 초기화합니다."""
    st.session_state.player = {
        "name": "",        # 플레이어 이름
        "level": 1,        # 레벨
        "exp": 0,          # 경험치
        "hp": 100,         # 현재 체력
        "max_hp": 100,     # 최대 체력
        "base_atk": 12,    # 레벨업으로 증가하는 기본 공격력
        "def": 4,          # 방어력
        "gold": 0,         # 골드
        "inventory": {"포션": 1, "무기 강화석": 0}, # 시작 아이템
        "current_weapon": "낡은 검" # 시작 무기
    }
    st.session_state.room = 1 # 현재 방 번호
    st.session_state.mode = "create" # 게임 모드 (create, explore, battle, game_over, game_clear)
    st.session_state.monster = None # 현재 전투 중인 몬스터 정보
    st.session_state.log: List[str] = [] # 게임 로그 메시지 (리스트)
    st.session_state.defending = False # 방어 중인지 여부
    st.session_state.shop_offer = None # 상점 제공 상품 정보
    st.session_state.initial_monster_hp = 0 # 몬스터 초기 HP (프로그레스 바용)
    st.session_state.game_over = False # 게임 오버 상태
    st.session_state.game_clear = False # 게임 클리어 상태

def log(msg: str):
    """게임 로그에 메시지를 추가합니다."""
    st.session_state.log.append(msg)

def ensure_state():
    """필수 세션 상태 키가 없는 경우 게임을 초기화합니다."""
    # 모든 STATE_KEYS가 존재하는지 확인하여 게임의 연속성을 보장
    if not all(k in st.session_state for k in STATE_KEYS):
        init_game()

def get_effective_atk() -> int:
    """플레이어의 유효 공격력을 계산하여 반환합니다 (기본 공격력 + 무기 보너스)."""
    p = st.session_state.player
    return p['base_atk'] + WEAPON_TIERS[p['current_weapon']]

# -----------------------------
# 규칙: 레벨업/경험치
# -----------------------------
def exp_needed(level: int) -> int:
    """다음 레벨업에 필요한 경험치를 계산합니다."""
    # 난이도 곡선: 레벨 * 50
    return level * 50

def check_level_up():
    """플레이어의 경험치를 확인하고 레벨업을 처리합니다."""
    p = st.session_state.player
    while p["exp"] >= exp_needed(p["level"]):
        p["exp"] -= exp_needed(p["level"]) # 필요한 경험치 차감
        p["level"] += 1 # 레벨 증가
        p["max_hp"] += 20 # 최대 HP 증가
        p["hp"] = p["max_hp"] # HP 완전 회복
        p["base_atk"] += 4 # 기본 공격력 증가
        p["def"] += 2 # 방어력 증가
        log(f"🎉 레벨업! Lv.{p['level']} (HP+20, ATK+4, DEF+2)")

# -----------------------------
# 전투/몬스터
# -----------------------------
def spawn_monster(is_boss: bool = False) -> Dict[str, Any]:
    """
    새로운 몬스터 또는 보스 몬스터를 생성하여 반환합니다.
    몬스터의 능력치는 플레이어의 현재 레벨에 비례하여 조정됩니다.
    """
    player_level = st.session_state.player['level']
    current_room = st.session_state.room

    if is_boss:
        if current_room == FINAL_BOSS_ROOM:
            # 최종 보스 (250층)
            boss_hp = 500 + (player_level * 25)
            boss_atk = 40 + (player_level * 5)
            boss_def = 15 + (player_level * 2)
            boss_exp = 500
            boss_gold = 200
            return {
                "name": "최종 보스: 어둠의 군주",
                "hp": boss_hp, "atk": boss_atk, "def": boss_def,
                "exp": boss_exp, "gold": boss_gold, "boss": True
            }
        else:
            # 일반 보스 (50, 100, 150, 200층)
            boss_hp = 250 + (player_level * 15)
            boss_atk = 22 + (player_level * 3)
            boss_def = 8 + (player_level * 1)
            boss_exp = 120 + (player_level * 10)
            boss_gold = 60 + (player_level * 5)
            return {
                "name": f"보스 – 심연의 수호자 (방 {current_room})",
                "hp": boss_hp, "atk": boss_atk, "def": boss_def,
                "exp": boss_exp, "gold": boss_gold, "boss": True
            }
    else:
        # 일반 몬스터: 플레이어 레벨 ±3 범위에서 몬스터 레벨 결정, 최소 1레벨
        monster_level = max(1, player_level + random.randint(-3, 3))
        
        # 몬스터 능력치도 몬스터 레벨에 비례하여 조정
        hp = random.randint(25, 40) + (monster_level * 7)
        atk = random.randint(7, 12) + (monster_level * 3)
        defense = random.randint(2, 5) + (monster_level * 1)
        exp = random.randint(20, 35) + (monster_level * 7)
        gold = random.randint(8, 15) + (monster_level * 2)
        
        return {
            "name": random.choice(["슬라임", "고블린", "스켈레톤", "도적", "오크"]),
            "hp": hp, "atk": atk, "def": defense,
            "exp": exp, "gold": gold, "boss": False
        }

def start_battle(is_boss: bool = False):
    """전투를 시작하고 몬스터를 생성합니다."""
    st.session_state.monster = spawn_monster(is_boss)
    st.session_state.initial_monster_hp = st.session_state.monster['hp'] # 몬스터 초기 HP 저장
    st.session_state.mode = "battle"
    m = st.session_state.monster
    log(f"⚔️ {m['name']} 등장! (HP {m['hp']}, ATK {m['atk']}, DEF {m['def']})")

def player_turn(action: str):
    """플레이어의 턴 행동을 처리하고 몬스터의 반격을 진행합니다."""
    p = st.session_state.player
    m = st.session_state.monster
    
    # 방어 상태 초기화 (이전 턴의 방어 효과 해제)
    st.session_state.defending = False

    if action == "attack":
        dmg = max(0, get_effective_atk() - m["def"]) # 플레이어의 유효 공격력 사용
        m["hp"] -= dmg
        log(f"👊 공격! {m['name']}에게 {dmg} 피해 (남은 HP {max(0, m['hp'])})")

    elif action == "defend":
        st.session_state.defending = True
        log("🛡️ 방어 태세! (이번 턴 몬스터 피해 50% 감소)")

    elif action == "potion":
        if p["inventory"].get("포션", 0) > 0:
            heal = min(40, p["max_hp"] - p["hp"])
            p["hp"] += heal
            p["inventory"]["포션"] -= 1
            log(f"🍖 포션 사용! HP {heal} 회복 ({p['hp']}/{p['max_hp']})")
        else:
            log("⚠️ 포션이 없습니다.")
            return # 행동 소모하지 않도록 조기 종료

    elif action == "upgrade_weapon":
        if p["inventory"].get("무기 강화석", 0) > 0:
            upgrade_weapon() # 무기 강화 함수 호출
            p["inventory"]["무기 강화석"] -= 1
        else:
            log("⚠️ 무기 강화석이 없습니다.")
            return
        
    # 몬스터 사망 체크
    if m["hp"] <= 0:
        if m["name"] == "최종 보스: 어둠의 군주":
            log(f"🎉 {m['name']}를 물리쳤습니다! 게임 클리어! 용사님의 위업을 칭송합니다!")
            st.session_state.game_clear = True
            st.session_state.mode = "game_clear"
        else:
            log(f"✅ {m['name']} 처치! EXP {m['exp']} / GOLD {m['gold']} 획득")
            p["exp"] += m["exp"]
            p["gold"] += m["gold"]
            check_level_up() # 경험치 획득 후 레벨업 시도
        
        st.session_state.monster = None
        st.session_state.in_battle = False
        if not st.session_state.game_clear: # 게임 클리어가 아니라면 다음 방으로 이동
            st.session_state.room += 1
        st.rerun()
        return

    # 몬스터 턴 (몬스터가 살아있을 경우에만 공격)
    dmg_to_player = max(0, m["atk"] - p["def"])
    if st.session_state.defending:
        dmg_to_player = dmg_to_player // 2 # 방어 시 피해 50% 감소
    p["hp"] -= dmg_to_player
    log(f"💢 {m['name']}의 공격! {dmg_to_player} 피해 (플레이어 HP {max(0, p['hp'])}/{p['max_hp']})")

    if p["hp"] <= 0:
        st.session_state.mode = "game_over"
        log("☠️ 쓰러졌습니다… 게임 오버")
        st.rerun()

# -----------------------------
# 무기 강화 시스템
# -----------------------------
def upgrade_weapon():
    """플레이어의 현재 무기를 다음 티어로 강화합니다."""
    p = st.session_state.player
    current_weapon_idx = WEAPON_ORDER.index(p['current_weapon'])
    
    if current_weapon_idx < len(WEAPON_ORDER) - 1:
        next_weapon = WEAPON_ORDER[current_weapon_idx + 1]
        log(f"✨ {p['current_weapon']}이(가) {next_weapon}으로 강화되었습니다! (ATK +{WEAPON_TIERS[next_weapon] - WEAPON_TIERS[p['current_weapon']]})")
        p['current_weapon'] = next_weapon
    else:
        log("✅ 더 이상 강화할 수 없습니다. 이미 최고의 무기를 가지고 있습니다!")

# -----------------------------
# 탐험(방 이벤트)
# -----------------------------
def roll_event():
    """다음 방 이벤트 결정 및 진행"""
    st.session_state.log = [] # 방 이동 시 로그 초기화
    st.session_state.initial_monster_hp = 0 # 새로운 몬스터를 위해 초기화

    r = st.session_state.room
    
    # 최종 보스 방 체크
    if r == FINAL_BOSS_ROOM:
        start_battle(is_boss=True)
        st.rerun()
        return

    # 일반 보스 방 체크
    if r % BOSS_INTERVAL == 0:
        start_battle(is_boss=True)
        st.rerun()
        return

    # 일반 방 이벤트
    event = random.choices(
        population=["monster", "item", "shop", "trap", "nothing"],
        weights=[0.45, 0.15, 0.15, 0.15, 0.10], # 몬스터 등장 확률 높임
        k=1
    )[0]

    if event == "monster":
        start_battle(is_boss=False)
        st.rerun()
        return

    elif event == "item":
        # 랜덤 아이템 드랍: 포션 또는 무기 강화석
        drop = random.choice(["포션", "포션", "무기 강화석"]) # 포션 확률 높임
        if drop == "포션":
            st.session_state.player["inventory"]["포션"] = st.session_state.player["inventory"].get("포션", 0) + 1
            log("🎁 아이템 발견: 포션 1개 획득!")
        elif drop == "무기 강화석":
            st.session_state.player["inventory"]["무기 강화석"] = st.session_state.player["inventory"].get("무기 강화석", 0) + 1
            log("💎 아이템 발견: 무기 강화석 1개 획득!")
        st.session_state.room += 1
        st.rerun()
        return

    elif event == "shop":
        # 상점: 포션 구매 / (무기 강화석은 인벤토리 사용으로 대체, 상점에서는 다른 버프만 제공)
        st.session_state.shop_offer = {
            "포션(1개) 구매": {"type": "potion", "cost": 20},
            "체력 회복(HP+50)": {"type": "heal", "cost": 30},
            "공격력 증폭(ATK+3)": {"type": "buff_atk", "cost": 50},
        }
        log("🏪 상점을 발견했습니다. 둘러보시겠습니까?")
        # 상점은 전투 아님, explore 상태 유지, 같은 방에서 처리
        return

    elif event == "trap":
        dmg = random.randint(10, 25)
        st.session_state.player["hp"] -= dmg
        if st.session_state.player["hp"] <= 0:
            log(f"💥 함정 발동! {dmg} 피해 → 사망")
            st.session_state.mode = "game_over"
            st.rerun()
            return
        log(f"💥 함정 발동! {dmg} 피해 (HP {st.session_state.player['hp']}/{st.session_state.player['max_hp']})")
        st.session_state.room += 1
        st.rerun()
        return

    else: # "nothing" 이벤트
        log("😶 아무 일도 일어나지 않았다.")
        st.session_state.room += 1
        st.rerun()
        return

# -----------------------------
# 상점 구매 처리
# -----------------------------
def buy(item_label: str):
    """상점에서 아이템 구매를 처리합니다."""
    offer = st.session_state.shop_offer.get(item_label)
    if not offer:
        return
    p = st.session_state.player
    if p["gold"] < offer["cost"]:
        log("💸 골드가 부족합니다.")
        return
    
    p["gold"] -= offer["cost"]
    
    if offer["type"] == "potion":
        p["inventory"]["포션"] = p["inventory"].get("포션", 0) + 1
        log("🧴 포션 1개 구매 완료!")
    elif offer["type"] == "heal":
        heal_amount = 50
        p["hp"] = min(p["max_hp"], p["hp"] + heal_amount)
        log(f"❤️ 체력 회복! HP {heal_amount} 회복 ({p['hp']}/{p['max_hp']})")
    elif offer["type"] == "buff_atk":
        p["base_atk"] += 3
        log(f"💪 공격력 증폭! ATK +3 ({get_effective_atk()})")

    # 상점은 1회 등장 후 종료
    st.session_state.shop_offer = None
    st.rerun() # 구매 후 UI 업데이트

# -----------------------------
# 메인 앱
# -----------------------------
st.set_page_config(page_title="턴제 RPG (최종 보스 250층)", page_icon="🗡️", layout="centered")
ensure_state() # 게임 상태가 초기화되었는지 확인

# 헤더/요약
st.title("🗡️ 텍스트 어드벤처 RPG")
p = st.session_state.player
mode = st.session_state.mode

# 사이드바 정보
with st.sidebar:
    st.markdown("### 캐릭터 상태")
    if p["name"]:
        st.write(f"**{p['name']}** |  Lv.{p['level']}")
    st.write(f"HP: {p['hp']}/{p['max_hp']}")
    st.write(f"ATK/DEF: {get_effective_atk()} / {p['def']}") # 유효 공격력 표시
    st.write(f"현재 무기: {p['current_weapon']} (ATK +{WEAPON_TIERS[p['current_weapon']]})") # 현재 무기 및 보너스 표시
    st.write(f"EXP: {p['exp']} / {exp_needed(p['level'])}")
    st.write(f"Gold: {p['gold']}")
    
    # 인벤토리 표시 (개수 포함)
    st.markdown("---")
    st.markdown("### 인벤토리")
    item_counts = collections.Counter(p["inventory"])
    displayed_items = False
    for item_name, count in item_counts.items():
        if count > 0:
            st.write(f"- {item_name} ×{count}")
            displayed_items = True
    if not displayed_items:
        st.write("인벤토리가 비었습니다.")

    st.markdown("---")
    st.write(f"현재 방: {st.session_state.room} (보스: {BOSS_INTERVAL}의 배수, 최종 보스: {FINAL_BOSS_ROOM})")
    if st.button("🔄 새 게임", key="sidebar_new_game_button"):
        init_game() # 모든 상태 초기화
        st.rerun()

# 메인 UI (모드별 분기)
if mode == "create":
    st.subheader("캐릭터 생성")
    name = st.text_input("이름을 입력하세요", max_chars=12, placeholder="용사 명준", key="create_name_input")
    if st.button("생성", key="create_character_button"):
        if name.strip():
            st.session_state.player["name"] = name.strip()
            st.session_state.mode = "explore"
            log(f"👤 캐릭터 생성: {name} (무기: {st.session_state.player['current_weapon']})")
            log("새로운 모험을 시작합니다!")
            st.rerun()
        else:
            st.warning("이름을 입력해주세요.")

elif mode == "explore":
    st.subheader(f"탐험 – 방 {st.session_state.room}")
    if st.session_state.shop_offer:
        st.info("🏪 상점: 아래 상품을 구매할 수 있습니다.")
        shop_cols = st.columns(len(st.session_state.shop_offer))
        for idx, (item_label, offer_details) in enumerate(st.session_state.shop_offer.items()):
            with shop_cols[idx]:
                if st.button(f"{item_label} – {offer_details['cost']}G", key=f"shop_buy_{item_label}"):
                    buy(item_label)
        st.divider() # 상점과 다음 방 이동 버튼 분리

    # 인벤토리에서 아이템 사용 버튼 (상점과 별개로 항상 표시)
    if st.session_state.player['inventory'].get("포션", 0) > 0:
        if st.button(f"🍖 포션 사용 (x{st.session_state.player['inventory']['포션']})", key="use_potion_explore"):
            player_turn("potion") # 아이템 사용은 player_turn 함수에서 처리
    
    if st.session_state.player['inventory'].get("무기 강화석", 0) > 0:
        if st.button(f"💎 무기 강화석 사용 (x{st.session_state.player['inventory']['무기 강화석']})", key="use_upgrade_stone_explore"):
            player_turn("upgrade_weapon") # 무기 강화석 사용은 player_turn 함수에서 처리

    st.markdown("---") # 아이템 사용 버튼과 다음 방 이동 버튼 사이 구분

    if st.button("➡️ 다음 방으로 이동", key="explore_next_room_button"):
        roll_event()

elif mode == "battle":
    m = st.session_state.monster
    st.subheader(f"전투 – {m['name']}")
    st.write(f"**몬스터 HP:** {max(0, m['hp'])}  |  **ATK/DEF:** {m['atk']} / {m['def']}")
    
    # 몬스터 HP 프로그레스 바
    st.progress(max(0, m['hp']) / st.session_state.initial_monster_hp, text=f"{m['name']} HP: {max(0, m['hp'])}/{st.session_state.initial_monster_hp}")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⚔️ 공격", key="battle_attack_button"):
            player_turn("attack")
    with c2:
        if st.button("🛡️ 방어", key="battle_defend_button"):
            player_turn("defend")
    with c3:
        # 전투 중에도 포션 사용 가능
        if st.session_state.player["inventory"].get("포션", 0) > 0:
            if st.button(f"🍖 포션 사용 (x{st.session_state.player['inventory']['포션']})", key="battle_potion_button"):
                player_turn("potion")
        else:
            st.button("🍖 포션 없음", disabled=True, key="battle_potion_disabled") # 포션 없으면 비활성화
    
    st.caption("힌트: 보스에게는 도망 불가! (애초에 도망 버튼도 안 달았습니다 😅)")

elif mode == "game_over":
    st.subheader("☠️ 게임 오버")
    st.error("당신은 쓰러졌습니다...")
    if st.button("🔁 다시 시작", key="game_over_restart_button"):
        init_game()
        st.rerun()

elif mode == "game_clear":
    st.subheader("🎉 게임 클리어!")
    st.balloons() # 축하 효과
    st.success("당신은 어둠의 군주를 물리치고 세상을 구원했습니다! 용사님의 위업을 칭송합니다!")
    st.write("모험의 끝에 도달했음을 축하합니다.")
    if st.button("🌟 새로운 게임 시작", key="game_clear_new_game_button"):
        init_game()
        st.rerun()

# 게임 로그 (최근 12줄만 표시, 최신순)
st.divider()
st.markdown("### 로그")
for line in st.session_state.log[-12:][::-1]: # 최근 12줄을 역순으로 출력 (가장 최근 메시지가 위로)
    st.write(line)
