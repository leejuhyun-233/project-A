import pygame
import random
import math
import os

# Initialize Pygame
pygame.init()

# Initialize mixer for sound
try:
    pygame.mixer.init()
except pygame.error as e:
    print(f"Warning: {e}")
    pygame.mixer = None

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Player settings
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 60
PLAYER_SPEED = 5

# Bullet settings
BULLET_WIDTH = 5
BULLET_HEIGHT = 10
BULLET_SPEED = 7

# Enemy settings
ENEMY_WIDTH = 50
ENEMY_HEIGHT = 60
INITIAL_ENEMY_SPEED = 3
ENEMY_SPEED = INITIAL_ENEMY_SPEED

# 발사 난이도 조정(전역)
ENEMY_SHOOT_PROB = 0.25           # 적이 발사 시도할 확률 (0.0 ~ 1.0)
ENEMY_BULLET_MIN_SPEED = 2.0     # 적 총알 최소 속도
ENEMY_BULLET_MAX_SPEED = 3.0     # 적 총알 최대 속도

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("슈팅 게임")  # 한국어 타이틀

# Load player image
player_img = pygame.image.load("fighter.png")
player_img = pygame.transform.scale(player_img, (PLAYER_WIDTH, PLAYER_HEIGHT))

# Load background image
background_img = pygame.image.load("background.jpg")
background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# 사용자 약한 적 이미지 로드 (우선순위: assets/enemies/weak_enemy.png -> 프로젝트 루트 weak_enemy.png)
weak_enemy_img = None
for p in (
    os.path.join(os.path.dirname(__file__), "assets", "enemies", "weak_enemy.png"),
    os.path.join(os.path.dirname(__file__), "weak_enemy.png"),
    "weak_enemy.png",
):
    try:
        if os.path.exists(p):
            weak_enemy_img = pygame.image.load(p).convert_alpha()
            break
    except Exception:
        weak_enemy_img = None

# 배경 스크롤 속도 (위로 이동)
BG_SCROLL_SPEED = 1.5
bg_y = 0

# Load background music if mixer is initialized
if pygame.mixer:
    try:
        pygame.mixer.music.load("background_music.mp3")
        pygame.mixer.music.play(-1)  # Play the music in a loop
    except Exception:
        pass

# 한글 폰트 선택 (Windows 기본 한글 폰트 시도, 실패하면 기본 폰트)
def get_korean_font(size):
    try:
        return pygame.font.SysFont("malgungothic", size)
    except Exception:
        try:
            return pygame.font.SysFont("맑은 고딕", size)
        except Exception:
            return pygame.font.Font(None, size)


# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.health = 3  # 플레이어 체력
        self.double_bullet = False
        self.bomb_bullet = False
        # 충돌 정확도 향상을 위해 마스크 추가
        try:
            self.mask = pygame.mask.from_surface(self.image)
        except Exception:
            self.mask = None

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def reduce_health(self):
        self.health -= 1
        if self.health <= 0:
            self.kill()

    def reset_powerups(self):
        self.double_bullet = False
        self.bomb_bullet = False


# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([BULLET_WIDTH, BULLET_HEIGHT])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        # 마스크 추가
        try:
            self.mask = pygame.mask.from_surface(self.image)
        except Exception:
            self.mask = None

    def update(self):
        self.rect.y -= BULLET_SPEED
        if self.rect.bottom < 0:
            self.kill()


# Bomb class
class Bomb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([BULLET_WIDTH * 2, BULLET_HEIGHT * 2])
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        # 정확한 충돌을 위해 마스크 추가
        try:
            self.mask = pygame.mask.from_surface(self.image)
        except Exception:
            self.mask = None

    def update(self):
        self.rect.y -= BULLET_SPEED
        if self.rect.bottom < 0:
            self.kill()

    def explode(self):
        explosion_radius = 40  # 폭발 반경
        global enemies_killed  # 전역 변수 사용
        for enemy in list(enemies):
            dx = self.rect.centerx - enemy.rect.centerx
            dy = self.rect.centery - enemy.rect.centery
            distance = math.hypot(dx, dy)
            if distance <= explosion_radius:
                enemy.kill()
                enemies_killed += 1


# Replace Enemy class & add Formation support (갤러그식 편대)
class Formation:
    def __init__(self, x, y, cols, rows, h_spacing=70, v_spacing=60, pattern=None):
        self.x = x
        self.y = y
        self.cols = cols
        self.rows = rows
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing
        self.dir = 1  # 1: 오른쪽, -1: 왼쪽
        self.speed = 1.2
        self.drop_amount = 20
        self.members = []
        self.pattern = pattern or []  # optional type pattern

    def add_member(self, enemy, col, row):
        enemy.formation = self
        enemy.offset_x = col * self.h_spacing
        enemy.offset_y = row * self.v_spacing
        self.members.append(enemy)

    def update(self):
        # 경계에 닿으면 방향 전환 (아래로 드롭하지 않음 — 적은 내려오지 않고 좌/우 이동만)
        left = min([m.offset_x for m in self.members], default=0) + self.x
        right = max([m.offset_x + m.rect.width for m in self.members], default=0) + self.x
        if right >= SCREEN_WIDTH - 10 and self.dir == 1:
            self.dir = -1
            # self.y += self.drop_amount  # 제거: 더 이상 아래로 떨어지지 않음
        elif left <= 10 and self.dir == -1:
            self.dir = 1
            # self.y += self.drop_amount  # 제거
        self.x += self.dir * self.speed

        # 적용: 멤버들의 실제 좌표를 formation 기준으로 설정
        for m in list(self.members):  # list()로 안전하게 순회
            m.rect.x = int(self.x + getattr(m, "offset_x", 0))
            m.rect.y = int(self.y + getattr(m, "offset_y", 0))

    def remove_member(self, enemy):
        try:
            self.members.remove(enemy)
        except ValueError:
            pass

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type="weak", formation=None, offset_x=0, offset_y=0):
        super().__init__()
        self.enemy_type = enemy_type

        # 타입별 이미지/크기/색/체력 설정 (이미지 누락으로 인한 오류 해결)
        if enemy_type == "weak":
            if weak_enemy_img:
                scale = random.uniform(0.6, 1.0)
                w = int(weak_enemy_img.get_width() * scale)
                h = int(weak_enemy_img.get_height() * scale)
                self.image = pygame.transform.smoothscale(weak_enemy_img, (w, h))
            else:
                w = random.randint(28, 36)
                h = random.randint(28, 36)
                color = (200, 80, 80)
                self.image = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.ellipse(self.image, color, self.image.get_rect())
            self.health = 1
            self.value = 10

        elif enemy_type == "strong":
            w = random.randint(50, 70)
            h = random.randint(40, 60)
            color = (120, 40, 200)
            self.image = pygame.Surface((w, h), pygame.SRCALPHA)
            # 강한 적 모양: 장방형+뿔 스타일
            pygame.draw.polygon(self.image, color, [(w//2, 0), (w-1, h//3), (w-1, h-1), (0, h-1), (0, h//3)])
            self.health = 3
            self.value = 50

        else:  # mid / mixed
            w = random.randint(36, 50)
            h = random.randint(30, 44)
            color = (220, 160, 60)
            self.image = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(self.image, color, self.image.get_rect(), border_radius=6)
            # 약간 장식 추가
            pygame.draw.rect(self.image, (180, 120, 40), (w//6, h//3, w*2//3, h//6))
            self.health = 2
            self.value = 25

        # rect / 초기 위치 설정
        self.rect = self.image.get_rect()
        self.formation = None
        self.offset_x = offset_x
        self.offset_y = offset_y

        if formation is None:
            self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
            self.rect.y = random.randint(-140, -40)
            self.speed = ENEMY_SPEED + random.uniform(-0.4, 0.8)
        else:
            self.formation = formation
            self.rect.x = int(formation.x + offset_x)
            self.rect.y = int(formation.y + offset_y)
            self.speed = 0
            formation.add_member(self, offset_x // formation.h_spacing if formation.h_spacing else 0,
                                 offset_y // formation.v_spacing if formation.v_spacing else 0)

        # 마스크(정밀 충돌용)
        try:
            self.mask = pygame.mask.from_surface(self.image)
        except Exception:
            self.mask = None

        # 적 발사 타이머 (간격을 늘려서 발사 빈도 감소)
        self.shoot_interval = random.randint(2000, 4000)   # 이전보다 길게
        self.next_shot_time = pygame.time.get_ticks() + random.randint(800, self.shoot_interval)

    def update(self):
        if self.formation is None:
            self.rect.y += self.speed
            if self.rect.top > SCREEN_HEIGHT:
                self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
                self.rect.y = random.randint(-140, -40)
                self.speed = ENEMY_SPEED + random.uniform(-0.4, 0.8)

        # 발사 처리: 확률 검사 추가, 총알 속도 조절
        try:
            now = pygame.time.get_ticks()
            if now >= getattr(self, "next_shot_time", 0):
                if random.random() <= ENEMY_SHOOT_PROB:
                    if "player" in globals() and player and getattr(player, "rect", None):
                        bx = self.rect.centerx
                        by = self.rect.bottom
                        tx = player.rect.centerx
                        ty = player.rect.centery
                        spd = random.uniform(ENEMY_BULLET_MIN_SPEED, ENEMY_BULLET_MAX_SPEED)
                        eb = EnemyBullet(bx, by, tx, ty, speed=spd)
                        all_sprites.add(eb)
                        enemy_bullets.add(eb)
                # 다음 발사 시간 설정 (간격도 랜덤화)
                self.next_shot_time = now + random.randint(1200, max(2000, self.shoot_interval))
        except Exception:
            pass

    def kill(self):
        if self.formation:
            self.formation.remove_member(self)
        super().kill()

# formations 리스트 (글로벌)
formations = []

def create_formation(cols=6, rows=3, start_x=None, start_y=60, pattern=None):
    if start_x is None:
        start_x = (SCREEN_WIDTH - (cols-1)*70) // 2
    f = Formation(start_x, start_y, cols, rows, h_spacing=70, v_spacing=60, pattern=pattern)
    for r in range(rows):
        for c in range(cols):
            # 패턴에 따라 적 타입을 지정할 수 있음
            if pattern and r < len(pattern) and c < len(pattern[r]):
                etype = pattern[r][c]
            else:
                # 중앙은 강한 적 배치 예시
                if r == 0 and c in (cols//2 - 1, cols//2):
                    etype = "strong"
                elif r == rows-1 and random.random() < 0.6:
                    etype = "weak"
                else:
                    etype = random.choice(["weak", "mid"])
            offset_x = c * f.h_spacing
            offset_y = r * f.v_spacing
            e = Enemy(enemy_type=etype, formation=f, offset_x=offset_x, offset_y=offset_y)
            all_sprites.add(e)
            enemies.add(e)
    formations.append(f)
    return f

def create_individual_enemy():
    e = Enemy(enemy_type=random.choice(["weak", "mid"]), formation=None)
    all_sprites.add(e)
    enemies.add(e)

# 초기 편대 생성
def create_initial_formations():
    formations.clear()
    # 중앙 대형을 작게: cols/rows 축소하여 적 수 줄임
    create_formation(cols=5, rows=2, start_y=40)
    # 좌/우 보조 편대는 하나로 줄이거나 제거
    create_formation(cols=3, rows=1, start_x=60, start_y=-40)
    # 오른쪽 편대는 선택적으로 주석처리 가능
    # create_formation(cols=3, rows=1, start_x=SCREEN_WIDTH - 60 - (3-1)*70, start_y=-40)


# Initialize player
player = Player()

# Sprite groups
all_sprites = pygame.sprite.Group()
all_sprites.add(player)

bullets = pygame.sprite.Group()
bombs = pygame.sprite.Group()
enemies = pygame.sprite.Group()
powerups = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()


# Create enemies
def create_enemies(num_enemies):
    for _ in range(num_enemies):
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)


# Replace the earlier single create_enemies call with formation initialization
create_initial_formations()


# Function to create power-ups
def create_powerup(x, y):
    power_type = random.choice(["double_bullet", "bomb_bullet"])
    powerup = PowerUp(x, y, power_type)
    all_sprites.add(powerup)
    powerups.add(powerup)


# Function to display health (한국어)
def display_health(health):
    font = get_korean_font(30)
    text = font.render(f"체력: {health}", True, WHITE)
    screen.blit(text, (10, 10))


# Function to display kills (한국어)
def display_kills(kills):
    font = get_korean_font(30)
    text = font.render(f"처치: {kills}", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH - 140, 10))


# Function to display game over message (한국어)
def display_game_over_text():
    font = get_korean_font(74)
    text = font.render("게임 오버", True, RED)
    screen.blit(
        text,
        (
            SCREEN_WIDTH // 2 - text.get_width() // 2,
            SCREEN_HEIGHT // 2 - text.get_height() // 2 - 60,
        ),
    )


# Function to display round message (한국어)
def display_round_message(round_num):
    font = get_korean_font(74)
    text = font.render(f"라운드 {round_num}", True, WHITE)
    screen.blit(
        text,
        (
            SCREEN_WIDTH // 2 - text.get_width() // 2,
            SCREEN_HEIGHT // 2 - text.get_height() // 2,
        ),
    )
    pygame.display.flip()
    pygame.time.wait(2000)  # 2초 대기


# 시작 메뉴 표시 및 시작 버튼 처리 (설명 버튼 추가)
def show_start_menu():
    menu_running = True
    start_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 30, 200, 60)
    info_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 40, 200, 50)
    title_font = get_korean_font(80)
    btn_font = get_korean_font(36)

    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button.collidepoint(event.pos):
                    return  # 시작
                if info_button.collidepoint(event.pos):
                    show_instructions()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return

        screen.fill(BLACK)
        screen.blit(background_img, (0, 0))

        # 타이틀
        title_text = title_font.render("슈팅 게임", True, WHITE)
        screen.blit(
            title_text,
            (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 3 - 80),
        )

        # 시작 버튼
        pygame.draw.rect(screen, GREEN, start_button)
        btn_text = btn_font.render("시작하기", True, BLACK)
        screen.blit(
            btn_text,
            (
                SCREEN_WIDTH // 2 - btn_text.get_width() // 2,
                SCREEN_HEIGHT // 2 - btn_text.get_height() // 2,
            ),
        )

        # 설명 버튼
        pygame.draw.rect(screen, BLUE, info_button)
        info_text = get_korean_font(24).render("게임 설명", True, BLACK)
        screen.blit(
            info_text,
            (
                SCREEN_WIDTH // 2 - info_text.get_width() // 2,
                SCREEN_HEIGHT // 2 + 40 + (50 - info_text.get_height()) // 2,
            ),
        )

        pygame.display.flip()
        pygame.time.Clock().tick(60)


# 게임 설명 화면
def show_instructions():
    showing = True
    font_title = get_korean_font(48)
    font = get_korean_font(24)
    lines = [
        "게임 설명",
        "",
        "조작:",
        "- 좌/우 화살표: 이동",
        "- 스페이스: 발사 (파워업: 폭탄/연발)",
        "",
        "목표: 적을 많이 처치하여 라운드를 진행하세요.",
        "아이템을 획득하면 무기가 강화됩니다.",
        "",
        "버튼이나 아무 키를 눌러 돌아가세요.",
    ]

    while showing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                showing = False

        screen.fill(BLACK)
        screen.blit(background_img, (0, 0))

        y = 80
        for i, line in enumerate(lines):
            if i == 0:
                text = font_title.render(line, True, WHITE)
            else:
                text = font.render(line, True, WHITE)
            screen.blit(text, (50, y))
            y += text.get_height() + 10

        pygame.display.flip()
        pygame.time.Clock().tick(60)


# 게임 리셋 함수 (다시하기)
def reset_game():
    global all_sprites, bullets, bombs, enemies, powerups, player, enemies_killed, round_num, ENEMY_SPEED
    # 그룹 비우기
    all_sprites.empty()
    bullets.empty()
    bombs.empty()
    enemies.empty()
    powerups.empty()

    # 플레이어 재생성 및 그룹에 추가
    player = Player()
    all_sprites.add(player)

    # 새로운 그룹 객체 할당 (참고: 기존 참조 재할당)
    bullets = pygame.sprite.Group()
    bombs = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()

    # 초기값 복원
    enemies_killed = 0
    round_num = 1
    ENEMY_SPEED = INITIAL_ENEMY_SPEED

    # 편대 스타일로 초기화하도록 수정
    create_initial_formations()


# 게임 오버 메뉴 (다시하기 / 종료)
def show_game_over_menu():
    font_btn = get_korean_font(36)
    restart_button = pygame.Rect(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 + 10, 120, 50)
    quit_button = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 + 10, 120, 50)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if restart_button.collidepoint(event.pos):
                    reset_game()
                    return True
                if quit_button.collidepoint(event.pos):
                    return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # R키로 다시하기
                    reset_game()
                    return True
                if event.key == pygame.K_q:  # Q로 종료
                    return False

        screen.fill(BLACK)
        screen.blit(background_img, (0, 0))
        display_game_over_text()

        # 다시하기 버튼
        pygame.draw.rect(screen, GREEN, restart_button)
        rt = font_btn.render("다시하기 (R)", True, BLACK)
        screen.blit(rt, (restart_button.x + (restart_button.width - rt.get_width()) // 2, restart_button.y + 10))

        # 종료 버튼
        pygame.draw.rect(screen, RED, quit_button)
        qt = font_btn.render("종료 (Q)", True, BLACK)
        screen.blit(qt, (quit_button.x + (quit_button.width - qt.get_width()) // 2, quit_button.y + 10))

        pygame.display.flip()
        clock.tick(60)


# PowerUp class (새로 추가)
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type):
        super().__init__()
        self.image = pygame.Surface([20, 20], pygame.SRCALPHA)
        if power_type == "double_bullet":
            pygame.draw.circle(self.image, GREEN, (10, 10), 10)
        else:
            pygame.draw.circle(self.image, BLUE, (10, 10), 10)
        self.rect = self.image.get_rect(center=(x, y))
        self.power_type = power_type

    def update(self):
        self.rect.y += 2
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# EnemyBullet class (적 총알 클래스 새로 추가)
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, speed=4):
        super().__init__()
        self.image = pygame.Surface((6, 10), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 200, 0), self.image.get_rect())
        self.rect = self.image.get_rect(center=(x, y))
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy) or 1
        self.vx = dx / dist * speed
        self.vy = dy / dist * speed
        try:
            self.mask = pygame.mask.from_surface(self.image)
        except Exception:
            self.mask = None

    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        # 화면 밖으로 나가면 제거
        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
            self.kill()


# Main game loop
running = True
clock = pygame.time.Clock()
round_num = 1
enemies_killed = 0
enemies_per_round = 50

# 시작 메뉴 실행
show_start_menu()

display_round_message(round_num)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if player.bomb_bullet:
                    bomb = Bomb(player.rect.centerx, player.rect.top)
                    all_sprites.add(bomb)
                    bombs.add(bomb)
                else:
                    bullet = Bullet(player.rect.centerx, player.rect.top)
                    all_sprites.add(bullet)
                    bullets.add(bullet)
                    if player.double_bullet:
                        bullet = Bullet(player.rect.centerx - 20, player.rect.top)
                        all_sprites.add(bullet)
                        bullets.add(bullet)

    # Update
    all_sprites.update()
    # formations 업데이트 (편대 전체 이동 처리)
    for f in list(formations):
        f.update()

    # Check for bullet-enemy collisions (정밀 충돌)
    hits = pygame.sprite.groupcollide(bullets, enemies, True, False, pygame.sprite.collide_mask)
    for bullet, hit_enemies in hits.items():
        for enemy in hit_enemies:
            # enemy가 health 속성을 가지고 있어야 함 (Enemy에서 설정됨)
            enemy.health -= 1
            if enemy.health <= 0:
                enemy.kill()
                enemies_killed += 1
                if random.random() < 0.12:
                    create_powerup(enemy.rect.centerx, enemy.rect.centery)
                if enemies_killed < enemies_per_round:
                    create_individual_enemy()

    # Check for bomb-enemy collisions
    bomb_hits = pygame.sprite.groupcollide(bombs, enemies, True, False, pygame.sprite.collide_mask)
    for bomb in bomb_hits:
        # 폭발 범위 내 적은 체력 감소
        explosion_radius = 40
        for enemy in list(enemies):
            dx = bomb.rect.centerx - enemy.rect.centerx
            dy = bomb.rect.centery - enemy.rect.centery
            distance = math.hypot(dx, dy)
            if distance <= explosion_radius:
                enemy.health -= 2
                if enemy.health <= 0:
                    enemy.kill()
                    enemies_killed += 1
                    if random.random() < 0.12:
                        create_powerup(enemy.rect.centerx, enemy.rect.centery)
        if enemies_killed >= enemies_per_round:
            round_num += 1
            enemies_killed = 0
            ENEMY_SPEED += 1
            create_enemies(10)
            display_round_message(round_num)
        else:
            while len(enemies) < 10:
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)

    # Check for player-enemy collisions
    player_hits = pygame.sprite.spritecollide(player, enemies, True, pygame.sprite.collide_mask)
    for hit in player_hits:
        player.reduce_health()
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)
        if player.health <= 0:
            # 게임 오버 메뉴 호출: 다시하기면 리셋 후 계속, 아니면 종료
            restart = show_game_over_menu()
            if not restart:
                running = False
            # if restart is True, reset_game() already called inside menu
            break

    # Check for player-powerup collisions
    powerup_hits = pygame.sprite.spritecollide(player, powerups, True)
    for hit in powerup_hits:
        player.reset_powerups()
        if hit.power_type == "double_bullet":
            player.double_bullet = True
        elif hit.power_type == "bomb_bullet":
            player.bomb_bullet = True

    # 적 총알이 플레이어에 맞는지 검사
    enemy_hits = pygame.sprite.spritecollide(player, enemy_bullets, True, pygame.sprite.collide_mask)
    for hit in enemy_hits:
        player.reduce_health()
        if player.health <= 0:
            restart = show_game_over_menu()
            if not restart:
                running = False
            break

    # Draw / render
    screen.fill(BLACK)

    # 배경 스크롤: 위로 점점 올라가게 (bg_y 감소)
    bg_y -= BG_SCROLL_SPEED
    if bg_y <= -SCREEN_HEIGHT:
        bg_y = 0
    # 두 장을 이어서 그려 루프 처리
    screen.blit(background_img, (0, bg_y))
    screen.blit(background_img, (0, bg_y + SCREEN_HEIGHT))

    all_sprites.draw(screen)
    display_health(player.health)
    display_kills(enemies_killed)

    # Flip the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

# 게임 종료 처리
display_game_over_text()
pygame.display.flip()
pygame.time.wait(2000)
pygame.quit()