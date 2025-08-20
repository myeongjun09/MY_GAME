import streamlit as st
import random

# =========================
# 초기화
# =========================
# 필요한 세션 상태 변수들을 초기화합니다. 게임이 시작되거나 재시작될 때 사용됩니다.
if 'player' not in st.session_state:
    st.session_state.player = {
        'name': '',        # 플레이어 이름
        'hp': 100,         # 현재 체력
        'max_hp': 100,     # 최대 체력
        'attack': 10,      # 공격력
        'exp': 0,          # 경험치
        'level': 1,        # 레벨
        'inventory': []    # 인벤토리 (아이템 저장)
    }
if 'room' not in st.session_state:
    st.session_state.room = 1 # 현재 방 번호
if 'game_over' not in st.session_state:
    st.session_state.game_over = False # 게임 오버 상태
if 'message' not in st.session_state:
    st.session_state.message = '새로운 모험을 시작합니다!' # 게임 로그 메시지
if 'in_battle' not in st.session_state:
    st.session_state.in_battle = False # 전투 중인지 여부
if 'current_monster' not in st.session_state:
    st.session_state.current_monster = None # 현재 전투 중인 몬스터 정보

# =========================
# 레벨업 함수
# =========================
def level_up():
    """
    플레이어의 경험치를 확인하고, 필요한 경험치에 도달하면 레벨업을 처리합니다.
    레벨업 시 체력과 공격력이 증가하고, 경험치는 차감됩니다.
    """
    player = st.session_state.player
    exp_needed = player['level'] * 50 # 다음 레벨업에 필요한 경험치
    
    # 필요한 경험치를 충족하면 반복적으로 레벨업을 처리합니다.
    while player['exp'] >= exp_needed:
        player['level'] += 1
        player['max_hp'] += 20
        player['hp'] = player['max_hp'] # 체력 회복
        player['attack'] += 5
        player['exp'] -= exp_needed # 초과 경험치는 다음 레벨로 이월되지 않음 (간단한 방식)
        st.session_state.message += f"\n🎉레벨업! 현재 레벨: {player['level']} (최대 HP: {player['max_hp']}, 공격력: {player['attack']})"
        exp_needed = player['level'] * 50 # 다음 레벨업에 필요한 경험치 갱신

# =========================
# 몬스터 생성 함수
# =========================
def spawn_monster(is_boss=False):
    """
    새로운 몬스터 또는 보스 몬스터를 생성하여 반환합니다.
    """
    if is_boss:
        # 보스 몬스터는 고정된 능력치를 가집니다.
        return {'name': '최종 보스', 'hp': 200, 'attack': 20, 'exp': 100}
    else:
        # 일반 몬스터는 현재 방 번호에 따라 능력치가 무작위로 결정됩니다.
        hp = random.randint(20, 50) + (st.session_state.room * 2) # 방이 높아질수록 HP 증가
        attack = random.randint(5, 15) + (st.session_state.room // 5) # 방이 높아질수록 공격력 증가
        exp = random.randint(10, 30) + (st.session_state.room // 2) # 방이 높아질수록 경험치 증가
        return {'name': f'몬스터 Lv.{st.session_state.room}', 'hp': hp, 'attack': attack, 'exp': exp}

# =========================
# 아이템 사용 함수
# =========================
def use_item(item_name):
    """
    플레이어가 인벤토리에서 아이템을 사용하는 함수입니다.
    """
    player = st.session_state.player
    if item_name == '포션':
        heal_amount = random.randint(20, 40)
        player['hp'] = min(player['max_hp'], player['hp'] + heal_amount)
        st.session_state.message += f"\n포션을 사용하여 HP를 {heal_amount} 회복했습니다. 현재 HP: {player['hp']}/{player['max_hp']}"
    elif item_name == '강화 물약':
        buff_amount = random.randint(3, 7)
        player['attack'] += buff_amount
        st.session_state.message += f"\n강화 물약을 사용하여 공격력이 {buff_amount} 증가했습니다. 현재 공격력: {player['attack']}"
    
    # 사용한 아이템을 인벤토리에서 제거합니다.
    st.session_state.player['inventory'].remove(item_name)
    st.rerun() # 아이템 사용 후 UI 업데이트를 위해 다시 실행

# =========================
# 전투 진행 함수 (한 턴)
# =========================
def execute_battle_turn():
    """
    전투 중 '공격' 버튼이 클릭될 때마다 호출되어 한 턴의 전투를 진행합니다.
    플레이어 공격 -> 몬스터 공격 순서로 진행됩니다.
    """
    player = st.session_state.player
    monster = st.session_state.current_monster

    # 플레이어 턴
    player_damage = player['attack']
    monster['hp'] -= player_damage
    st.session_state.message += f"⚔️ 플레이어가 {player_damage} 피해를 입혔다. {monster['name']} HP: {max(monster['hp'], 0)}\n"

    # 몬스터 사망 체크
    if monster['hp'] <= 0:
        st.session_state.message += f"✅ {monster['name']} 처치!\n"
        player['exp'] += monster['exp']
        level_up() # 경험치 획득 후 레벨업 시도
        st.session_state.in_battle = False # 전투 종료
        st.session_state.current_monster = None # 몬스터 정보 초기화
        st.session_state.room += 1 # 다음 방으로 이동
        st.rerun() # 전투 종료 후 UI 업데이트
        return

    # 몬스터 턴 (몬스터가 살아있을 경우에만 공격)
    monster_damage = monster['attack']
    player['hp'] -= monster_damage
    st.session_state.message += f"👹 {monster['name']}가 {monster_damage} 피해를 입혔다. 플레이어 HP: {max(player['hp'], 0)}\n"

    # 플레이어 사망 체크
    if player['hp'] <= 0:
        st.session_state.game_over = True
        st.session_state.message += "💀 플레이어가 사망했습니다. 게임 오버!"
        st.session_state.in_battle = False # 전투 종료
        st.session_state.current_monster = None # 몬스터 정보 초기화
        st.rerun() # 게임 오버 후 UI 업데이트
        return

# =========================
# 메인 게임 루프
# =========================
st.title("텍스트 어드벤처 RPG 게임")

player = st.session_state.player

# 캐릭터 이름 입력 (게임 시작 시 한 번만)
if player['name'] == '':
    st.header("새로운 모험의 시작")
    name = st.text_input("당신의 이름을 입력하세요, 용사여!", key="player_name_input") # 고유 key 추가
    if st.button("캐릭터 생성 🚀", key="create_character_button"): # 고유 key 추가
        if name.strip() != '':
            st.session_state.player['name'] = name
            st.rerun() # 이름 생성 후 UI를 업데이트하기 위해 다시 실행
else:
    # 게임 상태 표시
    st.header(f"용사: {player['name']}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("레벨", player['level'])
    with col2:
        st.metric("HP", f"{player['hp']}/{player['max_hp']}")
    with col3:
        st.metric("공격력", player['attack'])
    st.progress(player['hp'] / player['max_hp'], text=f"HP: {player['hp']}/{player['max_hp']}")
    st.progress(player['exp'] / (player['level'] * 50), text=f"EXP: {player['exp']} / {player['level'] * 50}")
    
    st.subheader(f"현재 방: {st.session_state.room} 🚪")

    # 인벤토리 표시 및 아이템 사용
    if st.session_state.player['inventory']:
        st.subheader("인벤토리 🎒")
        # set()을 사용하면 아이템이 여러 개여도 하나의 버튼만 표시되므로, 리스트 그대로 반복하며 key를 다르게 부여
        for idx, item in enumerate(st.session_state.player['inventory']): 
            # 각 아이템 사용 버튼에 고유한 key를 부여 (아이템 이름과 인덱스를 조합)
            if st.button(f"{item} 사용", key=f"use_item_{item}_{idx}"): 
                use_item(item)
    
    # 게임 오버 상태
    if st.session_state.game_over:
        st.error("Game Over...")
        if st.button("다시 시작 🔄", key="restart_button"): # 고유 key 추가
            # 세션 상태 초기화 (player 정보만 남기고 다른 것들은 새로 시작)
            st.session_state.clear() # 모든 세션 상태 지우기
            st.rerun() # 게임 재시작

    # 게임 진행 중
    else:
        # 전투 중인 경우
        if st.session_state.in_battle:
            monster = st.session_state.current_monster
            st.subheader(f"전투 중! 🆚 {monster['name']}")
            st.write(f"{monster['name']} HP: {max(monster['hp'], 0)}")
            # 몬스터의 초기 HP를 저장하여 프로그레스 바 계산에 사용 (재실행 시 HP 감소로 인한 스케일 변화 방지)
            if 'initial_monster_hp' not in st.session_state:
                st.session_state.initial_monster_hp = monster['hp']
            st.progress(max(monster['hp'], 0) / st.session_state.initial_monster_hp, text=f"몬스터 HP: {max(monster['hp'], 0)}") 
            
            # 공격 버튼을 누르면 한 턴의 전투 진행
            if st.button("공격 💥", key="attack_button"): # 고유 key 추가
                execute_battle_turn()

        # 전투 중이 아닌 경우 (다음 방으로 이동 또는 이벤트 발생)
        else:
            if st.button("다음 방으로 이동 ➡️", key="next_room_button"): # 고유 key 추가
                # 몬스터 초기 HP 초기화 (새로운 몬스터를 위해)
                if 'initial_monster_hp' in st.session_state:
                    del st.session_state.initial_monster_hp

                # 보스 방 체크 (50의 배수 방)
                if st.session_state.room % 50 == 0:
                    monster = spawn_monster(is_boss=True)
                    st.session_state.current_monster = monster
                    st.session_state.in_battle = True # 보스와 전투 시작
                    st.session_state.message += f"🚨 방 {st.session_state.room}: 강력한 {monster['name']}가 나타났다!\n"
                    st.rerun() # 전투 시작 UI 업데이트
                else:
                    # 일반 방 이벤트 처리
                    event_type = random.choice(['monster', 'item', 'trap', 'nothing'])
                    
                    if event_type == 'monster':
                        monster = spawn_monster()
                        st.session_state.current_monster = monster
                        st.session_state.in_battle = True # 몬스터와 전투 시작
                        st.session_state.message += f"⚔️ 방 {st.session_state.room}: {monster['name']}가 나타났다!\n"
                        st.rerun() # 전투 시작 UI 업데이트
                    
                    elif event_type == 'item':
                        item = random.choice(['포션', '강화 물약'])
                        st.session_state.player['inventory'].append(item)
                        st.session_state.message += f"✨ 방 {st.session_state.room}: 아이템 '{item}'을(를) 획득했습니다!"
                        st.session_state.room += 1 # 아이템 획득 후 다음 방으로
                        st.rerun()
                    
                    elif event_type == 'trap':
                        damage = random.randint(5, 15)
                        st.session_state.player['hp'] -= damage
                        st.session_state.message += f"⚠️ 방 {st.session_state.room}: 함정에 걸려 {damage} 피해를 입었다! 현재 HP: {player['hp']}/{player['max_hp']}"
                        if st.session_state.player['hp'] <= 0:
                            st.session_state.game_over = True
                            st.session_state.message += "💀 플레이어가 함정에 의해 사망했습니다. 게임 오버!"
                        st.session_state.room += 1 # 함정 후 다음 방으로
                        st.rerun()
                    
                    else: # 'nothing' 이벤트
                        st.session_state.message = f"🤔 방 {st.session_state.room}: 아무 일도 일어나지 않았다."
                        st.session_state.room += 1 # 아무 일 없이 다음 방으로
                        st.rerun()
    
    # 게임 로그 표시
    st.text_area("게임 로그", value=st.session_state.message, height=300, key="game_log") # 고유 key 추가

