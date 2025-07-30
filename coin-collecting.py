import pygame
import random
import sys
from typing import List, Tuple

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
main_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Coin Collector")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GOLD = (255, 215, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# Fonts
NORMAL_FONT = pygame.font.Font(None, 40)
GAME_OVER_FONT = pygame.font.Font(None, 80)
TITLE_FONT = pygame.font.Font(None, 100)

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
SETTINGS = 3


class Player:
    def __init__(self):
        self.width = 50
        self.height = 50
        self.reset_position()
        self.speed = 10
        self.color = BLUE
        self.shield = False
        self.shield_time = 0
        self.speed_boost = False
        self.speed_boost_time = 0

    def reset_position(self):
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - self.height - 10

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))

        if self.shield:
            shield_radius = self.width // 2 + 10
            pygame.draw.circle(surface, CYAN,
                               (self.x + self.width // 2, self.y + self.height // 2),
                               shield_radius, 2)

        if self.speed_boost:
            pygame.draw.rect(surface, ORANGE, (self.x - 5, self.y - 5,
                                               self.width + 10, self.height + 10), 2)

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        speed_multiplier = 1.5 if self.speed_boost else 1

        if keys[pygame.K_LEFT] and self.x > 0:
            self.x -= int(self.speed * speed_multiplier)
        if keys[pygame.K_RIGHT] and self.x < SCREEN_WIDTH - self.width:
            self.x += int(self.speed * speed_multiplier)

        current_time = pygame.time.get_ticks()
        if self.shield and current_time - self.shield_time > 5000:
            self.shield = False
        if self.speed_boost and current_time - self.speed_boost_time > 5000:
            self.speed_boost = False


class Obstacle:
    def __init__(self):
        self.width = random.randint(100, 200)
        self.height = 20
        self.reset_position()
        self.speed = 5
        self.color = RED

    def reset_position(self):
        self.x = random.randint(0, SCREEN_WIDTH - self.width)
        self.y = -self.height

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))

    def update(self) -> None:
        self.y += self.speed

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_HEIGHT

    def respawn(self) -> None:
        self.width = random.randint(100, 200)
        self.reset_position()
        self.speed += 0.3


class Coin:
    def __init__(self):
        self.radius = 15
        self.reset_position()
        self.speed = 4
        self.color = GOLD
        self.collected = False
        self.animation_frame = 0
        self.value = 1

    def reset_position(self):
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.y = -self.radius

    def draw(self, surface: pygame.Surface) -> None:
        pulse_offset = int(2 * abs(pygame.math.Vector2(1, self.animation_frame * 0.1).x))
        pulse_radius = self.radius + pulse_offset
        pygame.draw.circle(surface, self.color, (self.x, self.y), pulse_radius)
        pygame.draw.circle(surface, BLACK, (self.x, self.y), pulse_radius, 1)

    def update(self) -> None:
        self.y += self.speed
        self.animation_frame += 1

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_HEIGHT

    def respawn(self) -> None:
        self.reset_position()
        self.speed += 0.2
        self.collected = False
        if random.random() < 0.1:
            self.color = PURPLE
            self.value = 5
        else:
            self.color = GOLD
            self.value = 1


class PowerUp:
    def __init__(self):
        self.width = 30
        self.height = 30
        self.reset_position()
        self.speed = 3
        self.type = random.choice(["shield", "speed_boost", "extra_life"])
        self.collected = False
        self.set_color()

    def reset_position(self):
        self.x = random.randint(0, SCREEN_WIDTH - self.width)
        self.y = -self.height

    def set_color(self):
        self.color = {
            "shield": CYAN,
            "speed_boost": ORANGE,
            "extra_life": GREEN
        }[self.type]

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))

        if self.type == "shield":
            pygame.draw.circle(surface, WHITE, (self.x + self.width // 2, self.y + self.height // 2), 10, 2)
        elif self.type == "speed_boost":
            pygame.draw.line(surface, WHITE, (self.x + 5, self.y + self.height // 2),
                             (self.x + self.width - 5, self.y + self.height // 2), 3)
            pygame.draw.polygon(surface, WHITE, [
                (self.x + self.width - 5, self.y + self.height // 2),
                (self.x + self.width - 15, self.y + self.height // 2 - 5),
                (self.x + self.width - 15, self.y + self.height // 2 + 5)
            ])
        else:
            pygame.draw.polygon(surface, WHITE, [
                (self.x + self.width // 2, self.y + 5),
                (self.x + 5, self.y + self.height - 5),
                (self.x + self.width - 5, self.y + self.height - 5)
            ])

    def update(self) -> None:
        self.y += self.speed

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_HEIGHT

    def respawn(self) -> None:
        self.reset_position()
        self.type = random.choice(["shield", "speed_boost", "extra_life"])
        self.collected = False
        self.set_color()


class Particle:
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        self.speed_x = random.uniform(-2, 2)
        self.speed_y = random.uniform(-5, -1)
        self.lifetime = random.randint(20, 40)

    def update(self) -> None:
        self.x += self.speed_x
        self.y += self.speed_y
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

    def is_dead(self) -> bool:
        return self.lifetime <= 0


class Game:
    def __init__(self):
        self.state = MENU
        self.player = Player()
        self.obstacles: List[Obstacle] = []
        self.coins: List[Coin] = []
        self.power_ups: List[PowerUp] = []
        self.particles: List[Particle] = []
        self.score = 0
        self.high_score = self.load_high_score()
        self.level = 1
        self.lives = 1
        self.dark_mode = True
        self.clock = pygame.time.Clock()
        self.reset_game_objects()

    @staticmethod
    def load_high_score() -> int:
        try:
            with open("highscore.txt", "r", encoding="utf-8") as f:
                return int(f.read())
        except (FileNotFoundError, ValueError):
            return 0

    def save_high_score(self) -> None:
        with open("highscore.txt", "w", encoding="utf-8") as f:
            f.write(str(self.high_score))

    def reset_game_objects(self):
        self.obstacles = [Obstacle() for _ in range(min(3 + self.level // 2, 5))]
        self.coins = [Coin() for _ in range(min(2 + self.level // 3, 5))]
        self.power_ups = []
        self.particles = []

    def spawn_power_up(self) -> None:
        if random.random() < 0.05 and len(self.power_ups) < 2:
            self.power_ups.append(PowerUp())

    def check_collisions(self) -> None:
        # Check coin collisions
        for coin in self.coins:
            if (self.player.x < coin.x + coin.radius and
                    self.player.x + self.player.width > coin.x - coin.radius and
                    self.player.y < coin.y + coin.radius and
                    self.player.y + self.player.height > coin.y - coin.radius and
                    not coin.collected):
                self.handle_coin_collection(coin)

        # Check power-up collisions
        for power_up in self.power_ups[:]:
            if (self.player.x < power_up.x + power_up.width and
                    self.player.x + self.player.width > power_up.x and
                    self.player.y < power_up.y + power_up.height and
                    self.player.y + self.player.height > power_up.y and
                    not power_up.collected):
                self.handle_powerup_collection(power_up)

        # Check obstacle collisions
        for obstacle in self.obstacles:
            if (self.player.x < obstacle.x + obstacle.width and
                    self.player.x + self.player.width > obstacle.x and
                    self.player.y < obstacle.y + obstacle.height and
                    self.player.y + self.player.height > obstacle.y):
                self.handle_obstacle_collision(obstacle)

    def handle_coin_collection(self, coin: Coin) -> None:
        coin.collected = True
        self.score += coin.value

        for _ in range(20):
            self.particles.append(Particle(coin.x, coin.y, coin.color))

        coin.respawn()

        if self.score // 10 > self.level - 1:
            self.level_up()

    def handle_powerup_collection(self, power_up: PowerUp) -> None:
        power_up.collected = True

        if power_up.type == "shield":
            self.player.shield = True
            self.player.shield_time = pygame.time.get_ticks()
        elif power_up.type == "speed_boost":
            self.player.speed_boost = True
            self.player.speed_boost_time = pygame.time.get_ticks()
        elif power_up.type == "extra_life":
            self.lives += 1

        self.power_ups.remove(power_up)

    def handle_obstacle_collision(self, obstacle: Obstacle) -> None:
        if self.player.shield:
            self.player.shield = False
            obstacle.respawn()

            for _ in range(30):
                self.particles.append(Particle(
                    self.player.x + self.player.width // 2,
                    self.player.y + self.player.height // 2,
                    CYAN
                ))
        else:
            self.lives -= 1
            obstacle.respawn()

            if self.lives <= 0:
                self.game_over()
            else:
                for _ in range(30):
                    self.particles.append(Particle(
                        self.player.x + self.player.width // 2,
                        self.player.y + self.player.height // 2,
                        RED
                    ))

    def level_up(self) -> None:
        self.level += 1
        self.reset_game_objects()

    def game_over(self) -> None:
        self.state = GAME_OVER
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def reset_game(self) -> None:
        self.player = Player()
        self.score = 0
        self.level = 1
        self.lives = 1
        self.reset_game_objects()

    def update(self) -> None:
        if self.state == PLAYING:
            keys = pygame.key.get_pressed()
            self.player.update(keys)

            for obstacle in self.obstacles:
                obstacle.update()
                if obstacle.is_off_screen():
                    obstacle.respawn()

            for coin in self.coins:
                coin.update()
                if coin.is_off_screen():
                    coin.respawn()

            for power_up in self.power_ups[:]:
                power_up.update()
                if power_up.is_off_screen():
                    self.power_ups.remove(power_up)

            self.spawn_power_up()

            for particle in self.particles[:]:
                particle.update()
                if particle.is_dead():
                    self.particles.remove(particle)

            self.check_collisions()

    def draw(self) -> None:
        if self.dark_mode:
            main_screen.fill(BLACK)
        else:
            main_screen.fill(WHITE)

        if self.state == MENU:
            self.draw_menu()
        elif self.state == PLAYING:
            self.draw_game()
        elif self.state == GAME_OVER:
            self.draw_game_over()
        elif self.state == SETTINGS:
            self.draw_settings()

        pygame.display.update()

    def draw_menu(self) -> None:
        title_text = TITLE_FONT.render("COIN COLLECTOR", True, GOLD)
        main_screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))

        play_text = NORMAL_FONT.render("1. Play Game", True, WHITE if self.dark_mode else BLACK)
        settings_text = NORMAL_FONT.render("2. Settings", True, WHITE if self.dark_mode else BLACK)
        quit_text = NORMAL_FONT.render("3. Quit", True, WHITE if self.dark_mode else BLACK)

        main_screen.blit(play_text, (SCREEN_WIDTH // 2 - play_text.get_width() // 2, 350))
        main_screen.blit(settings_text, (SCREEN_WIDTH // 2 - settings_text.get_width() // 2, 400))
        main_screen.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, 450))

        hs_text = NORMAL_FONT.render(f"High Score: {self.high_score}", True, GREEN)
        main_screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 500))

    def draw_game(self) -> None:
        self.player.draw(main_screen)

        for obstacle in self.obstacles:
            obstacle.draw(main_screen)

        for coin in self.coins:
            if not coin.collected:
                coin.draw(main_screen)

        for power_up in self.power_ups:
            power_up.draw(main_screen)

        for particle in self.particles:
            particle.draw(main_screen)

        score_text = NORMAL_FONT.render(f"Score: {self.score}", True, WHITE if self.dark_mode else BLACK)
        level_text = NORMAL_FONT.render(f"Level: {self.level}", True, WHITE if self.dark_mode else BLACK)
        lives_text = NORMAL_FONT.render(f"Lives: {self.lives}", True, WHITE if self.dark_mode else BLACK)

        main_screen.blit(score_text, (10, 10))
        main_screen.blit(level_text, (10, 50))
        main_screen.blit(lives_text, (10, 90))

        if self.player.shield:
            shield_text = NORMAL_FONT.render("SHIELD", True, CYAN)
            main_screen.blit(shield_text, (SCREEN_WIDTH - shield_text.get_width() - 10, 10))

        if self.player.speed_boost:
            speed_text = NORMAL_FONT.render("SPEED BOOST", True, ORANGE)
            main_screen.blit(speed_text, (SCREEN_WIDTH - speed_text.get_width() - 10, 50))

    def draw_game_over(self) -> None:
        game_over_text = GAME_OVER_FONT.render("GAME OVER", True, RED)
        main_screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 200))

        score_text = NORMAL_FONT.render(f"Score: {self.score}", True, WHITE if self.dark_mode else BLACK)
        main_screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 300))

        hs_text = NORMAL_FONT.render(f"High Score: {self.high_score}", True, GREEN)
        main_screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 350))

        restart_text = NORMAL_FONT.render("Press ENTER to return to menu", True, WHITE if self.dark_mode else BLACK)
        main_screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 450))

    def draw_settings(self) -> None:
        title_text = TITLE_FONT.render("SETTINGS", True, GOLD)
        main_screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))

        theme_text = NORMAL_FONT.render("1. Theme: Dark/Light", True, WHITE if self.dark_mode else BLACK)
        theme_status = NORMAL_FONT.render(f"(Currently: {'Dark' if self.dark_mode else 'Light'})",
                                          True, GREEN if self.dark_mode else BLUE)
        main_screen.blit(theme_text, (SCREEN_WIDTH // 2 - theme_text.get_width() // 2, 300))
        main_screen.blit(theme_status, (SCREEN_WIDTH // 2 - theme_status.get_width() // 2, 340))

        back_text = NORMAL_FONT.render("Press ESC to return to menu", True, WHITE if self.dark_mode else BLACK)
        main_screen.blit(back_text, (SCREEN_WIDTH // 2 - back_text.get_width() // 2, 650))

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self.state == MENU:
                    if event.key == pygame.K_1:
                        self.state = PLAYING
                        self.reset_game()
                    elif event.key == pygame.K_2:
                        self.state = SETTINGS
                    elif event.key == pygame.K_3:
                        return False

                elif self.state == GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self.state = MENU

                elif self.state == SETTINGS:
                    if event.key == pygame.K_1:
                        self.dark_mode = not self.dark_mode
                    elif event.key == pygame.K_ESCAPE:
                        self.state = MENU

        return True

    def run(self) -> None:
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()