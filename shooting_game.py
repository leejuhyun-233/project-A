import pygame
import random

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
ENEMY_SPEED = 3

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shooting Game")

# Load player image
player_img = pygame.image.load("fighter.png")
player_img = pygame.transform.scale(player_img, (PLAYER_WIDTH, PLAYER_HEIGHT))

# Load background image
background_img = pygame.image.load("background.jpg")

# Load background music if mixer is initialized
if pygame.mixer:
    pygame.mixer.music.load("background_music.mp3")
    pygame.mixer.music.play(-1)  # Play the music in a loop


# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.health = 3  # Player health
        self.double_bullet = False
        self.bomb_bullet = False

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

    def update(self):
        self.rect.y -= BULLET_SPEED
        if self.rect.bottom < 0:
            self.kill()

    def explode(self):
        explosion_radius = 40  # 폭발 반경을 40으로 줄임
        global enemies_killed  # 전역 변수 사용
        for enemy in enemies:
            if pygame.sprite.collide_circle_ratio(explosion_radius / self.rect.width)(
                self, enemy
            ):
                enemy.kill()
                enemies_killed += 1  # 적 처치 시 킬 수 증가


# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([ENEMY_WIDTH, ENEMY_HEIGHT])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - ENEMY_WIDTH)
        self.rect.y = random.randint(-100, -40)

    def update(self):
        self.rect.y += ENEMY_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.x = random.randint(0, SCREEN_WIDTH - ENEMY_WIDTH)
            self.rect.y = random.randint(-100, -40)


# Power-up class
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type):
        super().__init__()
        self.image = pygame.Surface([20, 20])
        if power_type == "double_bullet":
            self.image.fill(GREEN)
        elif power_type == "bomb_bullet":
            self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.power_type = power_type

    def update(self):
        self.rect.y += 2
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# Initialize player
player = Player()

# Sprite groups
all_sprites = pygame.sprite.Group()
all_sprites.add(player)

bullets = pygame.sprite.Group()
bombs = pygame.sprite.Group()
enemies = pygame.sprite.Group()
powerups = pygame.sprite.Group()


# Create enemies
def create_enemies(num_enemies):
    for _ in range(num_enemies):
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)


create_enemies(10)


# Function to create power-ups
def create_powerup(x, y):
    power_type = random.choice(["double_bullet", "bomb_bullet"])
    powerup = PowerUp(x, y, power_type)
    all_sprites.add(powerup)
    powerups.add(powerup)


# Function to display health
def display_health(health):
    font = pygame.font.Font(None, 36)
    text = font.render(f"Health: {health}", True, WHITE)
    screen.blit(text, (10, 10))


# Function to display kills
def display_kills(kills):
    font = pygame.font.Font(None, 36)
    text = font.render(f"Kills: {kills}", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH - 100, 10))


# Function to display game over message
def display_game_over():
    font = pygame.font.Font(None, 74)
    text = font.render("Game Over", True, RED)
    screen.blit(
        text,
        (
            SCREEN_WIDTH // 2 - text.get_width() // 2,
            SCREEN_HEIGHT // 2 - text.get_height() // 2,
        ),
    )


# Function to display round message
def display_round_message(round_num):
    font = pygame.font.Font(None, 74)
    text = font.render(f"Round {round_num}", True, WHITE)
    screen.blit(
        text,
        (
            SCREEN_WIDTH // 2 - text.get_width() // 2,
            SCREEN_HEIGHT // 2 - text.get_height() // 2,
        ),
    )
    pygame.display.flip()
    pygame.time.wait(2000)  # Wait for 2 seconds


# Main game loop
running = True
clock = pygame.time.Clock()
round_num = 1
enemies_killed = 0
enemies_per_round = 50

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

    # Check for bullet-enemy collisions
    hits = pygame.sprite.groupcollide(bullets, enemies, True, True)
    for hit in hits:
        enemies_killed += 1
        if random.random() < 0.1:  # 10% 확률로 아이템 생성
            create_powerup(hit.rect.centerx, hit.rect.centery)
        if enemies_killed >= enemies_per_round:
            round_num += 1
            enemies_killed = 0
            ENEMY_SPEED += 1  # Increase enemy speed for next round
            create_enemies(10)  # Create initial enemies for the new round
            display_round_message(round_num)
        else:
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)

    # Check for bomb-enemy collisions
    bomb_hits = pygame.sprite.groupcollide(bombs, enemies, True, False)
    for bomb in bomb_hits:
        bomb.explode()  # 폭발 효과 적용
        if enemies_killed >= enemies_per_round:
            round_num += 1
            enemies_killed = 0
            ENEMY_SPEED += 1  # Increase enemy speed for next round
            create_enemies(10)  # Create initial enemies for the new round
            display_round_message(round_num)
        else:
            while len(enemies) < 10:  # 적의 수를 유지
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)

    # Check for player-enemy collisions
    player_hits = pygame.sprite.spritecollide(player, enemies, True)
    for hit in player_hits:
        player.reduce_health()
        if player.health <= 0:
            running = False
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)

    # Check for player-powerup collisions
    powerup_hits = pygame.sprite.spritecollide(player, powerups, True)
    for hit in powerup_hits:
        player.reset_powerups()  # Reset power-ups before applying new one
        if hit.power_type == "double_bullet":
            player.double_bullet = True
        elif hit.power_type == "bomb_bullet":
            player.bomb_bullet = True

    # Draw / render
    screen.fill(BLACK)
    screen.blit(background_img, (0, 0))
    all_sprites.draw(screen)
    display_health(player.health)
    display_kills(enemies_killed)

    # Flip the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

display_game_over()
pygame.display.flip()
pygame.time.wait(2000)

pygame.quit()
