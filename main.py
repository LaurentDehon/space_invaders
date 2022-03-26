import sys
import pygame
import os
import random
from pygame import mixer


pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
WIDTH, HEIGHT = 1000, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Space Invaders')

explosion_1_fx = pygame.mixer.Sound(os.path.join('Assets', 'explosion_1.wav'))
explosion_1_fx.set_volume(0.25)
explosion_2_fx = pygame.mixer.Sound(os.path.join('Assets', 'explosion_2.wav'))
explosion_2_fx.set_volume(0.25)
laser_fx = pygame.mixer.Sound(os.path.join('Assets', 'laser.wav'))
laser_fx.set_volume(0.25)

FONT20 = pygame.font.SysFont('Calibri', 20, 'bold')
FONT30 = pygame.font.SysFont('Calibri', 30, 'bold')
FONT40 = pygame.font.SysFont('Calibri', 40, 'bold')

BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join('Assets', 'space.png')), (WIDTH, HEIGHT))

RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)

FPS = 60
PLAYER_SPEED = 8
INVADER_FIRE_COOLDOWN = 1000
INVADER_MAX_LASERS = 5
INVADER_LASER_SPEED = 10
last_invader_shot = pygame.time.get_ticks()
COUNTDOWN = 5
last_count = pygame.time.get_ticks()
game_over = 0  # 0: no game over / 1: player has won / -1: player has lost
level = 1
message = 'GET READY!'

ROWS = 4
COLUMNS = 10

highest_score = 0
try:
    with open('score.txt', 'r') as f:
        highest_score = f.read()
except FileNotFoundError:
    with open('score.txt', 'w') as f:
        f.write(str(highest_score))


class Player(pygame.sprite.Sprite):

    def __init__(self, x, y, health):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(pygame.image.load(os.path.join('Assets', 'spaceship_player.png')), (50, 60))
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.mask = None
        self.health = health
        self.health_left = health
        self.score = 0

    def update(self):
        global game_over
        game_over = 0
        # move spaceship
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT] and self.rect.left > 5:
            self.rect.x -= PLAYER_SPEED
        if key[pygame.K_RIGHT] and self.rect.right < WIDTH - 5:
            self.rect.x += PLAYER_SPEED
        if key[pygame.K_UP] and self.rect.top > 500:
            self.rect.y -= PLAYER_SPEED
        if key[pygame.K_DOWN] and self.rect.centery < HEIGHT - 50:
            self.rect.y += PLAYER_SPEED

        # shoot
        if key[pygame.K_SPACE] and len(player_lasers_group) == 0 and COUNTDOWN == 0:
            laser_fx.play()
            laser = PlayerLaser(self.rect.centerx, self.rect.top)
            player_lasers_group.add(laser)

        # update mask
        self.mask = pygame.mask.from_surface(self.image)

        # draw health bar
        pygame.draw.rect(WIN, RED, (self.rect.x, (self.rect.bottom + 10), self.rect.width, 5))
        if self.health_left > 0:
            pygame.draw.rect(WIN, GREEN, (self.rect.x, (self.rect.bottom + 10),
                                          int(self.rect.width * (self.health_left / self.health)), 5))
        elif self.health_left <= 0:
            explosion = Explosion(self.rect.centerx, self.rect.centery, 3)
            explosions_group.add(explosion)
            self.kill()
            game_over = -1
        return game_over


class PlayerLaser(pygame.sprite.Sprite):

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(pygame.image.load(os.path.join('Assets', 'beam_blue.png')), (15, 30))
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
        self.rect.y -= 15
        if self.rect.bottom < 0:
            self.kill()
        if pygame.sprite.spritecollide(self, invaders_group, True, pygame.sprite.collide_mask):
            self.kill()
            explosion_1_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
            explosions_group.add(explosion)
        if pygame.sprite.spritecollide(self, invaders_lasers_group, True, pygame.sprite.collide_mask):
            self.kill()
            explosion_1_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
            explosions_group.add(explosion)


class Invader(pygame.sprite.Sprite):

    def __init__(self, x, y, i):
        pygame.sprite.Sprite.__init__(self)
        self.value = i * 10
        self.image = pygame.transform.scale(
            pygame.image.load(os.path.join('Assets', f'spaceship_invader_{i}.png')), (60, 60))
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.mask = None
        self.move_direction = 1

    def update(self):
        global game_over
        self.rect.x += self.move_direction
        print(f"{self.rect.x} / {self.move_direction}")
        if self.rect.right > WIDTH - 10 or self.rect.left < 10:
            for i in invaders_group:
                i.move_direction *= -1
                i.rect.y += 10
        # if len(invaders_group) == 10:
        #     for i in invaders_group:
        #         i.move_direction = self.move_direction * 2
        # elif len(invaders_group) == 5:
        #     for i in invaders_group:
        #         i.move_direction = self.move_direction * 2
        # elif len(invaders_group) == 2:
        #     for i in invaders_group:
        #         i.move_direction = self.move_direction * 2

        # update mask
        self.mask = pygame.mask.from_surface(self.image)

    def __del__(self):
        player.score += self.value


class InvaderLaser(pygame.sprite.Sprite):

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(pygame.image.load(os.path.join('Assets', 'beam_red.png')), (15, 30))
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
        self.rect.y += INVADER_LASER_SPEED
        if self.rect.top > HEIGHT:
            self.kill()
        if pygame.sprite.spritecollide(self, player_group, False, pygame.sprite.collide_mask):
            player.health_left -= 1
            self.kill()
            explosion_2_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 1)
            explosions_group.add(explosion)


class Explosion(pygame.sprite.Sprite):

    def __init__(self, x, y, size):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for i in range(1, 6):
            img = pygame.image.load(os.path.join('Assets', f'exp{i}.png'))
            if size == 1:
                img = pygame.transform.scale(img, (20, 20))
            if size == 2:
                img = pygame.transform.scale(img, (40, 40))
            if size == 3:
                img = pygame.transform.scale(img, (160, 160))
            self.images.append(img)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.counter = 0

    def update(self):
        explosion_speed = 3
        self.counter += 1
        if self.counter >= explosion_speed and self.index < len(self.images) - 1:
            self.counter = 0
            self.index += 1
            self.image = self.images[self.index]
        if self.index >= len(self.images) - 1 and self.counter >= explosion_speed:
            self.kill()


def draw_background():
    WIN.blit(BG_IMG, (0, 0))


def draw_text(text, font, text_col, x, y):
    text = font.render(text, True, text_col)
    text_rect = text.get_rect(center=(x, y))
    WIN.blit(text, text_rect)


def draw_score(text, font, text_col, x, y):
    text = font.render(text, True, text_col)
    WIN.blit(text, (x, y))


player_group = pygame.sprite.Group()
player_lasers_group = pygame.sprite.Group()
invaders_group = pygame.sprite.Group()
invaders_lasers_group = pygame.sprite.Group()
explosions_group = pygame.sprite.Group()


def create_invaders():
    for row in range(ROWS):
        for i in range(COLUMNS):
            number = random.randint(1, 25)
            if number < 11:
                invader = Invader(140 + i * 80, 120 + row * 70, 1)
            elif number < 17:
                invader = Invader(140 + i * 80, 120 + row * 70, 2)
            elif number < 21:
                invader = Invader(140 + i * 80, 120 + row * 70, 3)
            elif number < 24:
                invader = Invader(140 + i * 80, 120 + row * 70, 4)
            else:
                invader = Invader(140 + i * 80, 120 + row * 70, 5)
            invaders_group.add(invader)


create_invaders()

player = Player(WIDTH // 2, HEIGHT - 50, 3)
player_group.add(player)


def next_level():
    global INVADER_FIRE_COOLDOWN
    global INVADER_MAX_LASERS
    global INVADER_LASER_SPEED
    global COUNTDOWN
    INVADER_FIRE_COOLDOWN *= 0.95
    INVADER_MAX_LASERS *= 1.05
    INVADER_LASER_SPEED *= 1.05
    COUNTDOWN = 5
    for _ in invaders_group:
        _.kill()
    for _ in invaders_lasers_group:
        _.kill()
    for _ in player_lasers_group:
        _.kill()
    create_invaders()
    player.health_left = 3
    player.rect.centerx = WIDTH // 2
    player.rect.centery = HEIGHT - 50


def main():
    global COUNTDOWN
    global game_over
    global level
    global highest_score
    global message
    global player
    clock = pygame.time.Clock()
    run = True
    while run:

        clock.tick(FPS)
        draw_background()
        draw_score(f'Score : {player.score}', FONT20, WHITE, 20, 20)
        draw_text(f'Level {level}', FONT20, WHITE, WIDTH / 2, 30)
        draw_score(f'Highest score : {highest_score}', FONT20, WHITE, 20, 50)

        if COUNTDOWN == 0:
            # create invaders lasers
            global last_invader_shot
            now = pygame.time.get_ticks()
            if now - last_invader_shot > INVADER_FIRE_COOLDOWN and len(invaders_lasers_group) < INVADER_MAX_LASERS \
                    and len(invaders_group) > 0:
                attacking_invader = random.choice(invaders_group.sprites())
                invader_laser = InvaderLaser(attacking_invader.rect.centerx, attacking_invader.rect.bottom)
                invaders_lasers_group.add(invader_laser)
                last_invader_shot = now

            if len(invaders_group) == 0:
                if len(invaders_lasers_group) == 0:
                    next_level()
                    level += 1
                    message = f'LEVEL {level}'
                    main()

            if game_over == 0:
                # update player
                game_over = player.update()

                # update sprites groups
                player_lasers_group.update()
                invaders_group.update()
                invaders_lasers_group.update()
            else:
                if game_over == -1:
                    message = 'GAME OVER'
                    draw_text(message, FONT40, WHITE, int(WIDTH / 2), int(HEIGHT / 2))

        if COUNTDOWN > 0:
            global last_count
            draw_text(message, FONT40, WHITE, int(WIDTH / 2), int(HEIGHT / 2))
            draw_text(str(COUNTDOWN), FONT40, WHITE, int(WIDTH / 2), int(HEIGHT / 2 + 50))
            count_timer = pygame.time.get_ticks()
            if count_timer - last_count > 1000:
                COUNTDOWN -= 1
                last_count = count_timer

        # update explosions groups
        explosions_group.update()

        # draw sprites groups
        player_group.draw(WIN)
        player_lasers_group.draw(WIN)
        invaders_group.draw(WIN)
        invaders_lasers_group.draw(WIN)
        explosions_group.draw(WIN)

        # events handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if player.score > int(highest_score):
                    with open('score.txt', 'w') as file:
                        file.write(str(player.score))
                run = False

        # update display
        pygame.display.update()

    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    main()
