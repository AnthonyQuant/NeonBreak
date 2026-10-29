"""Main Game controller with custom Orbitron/Rajdhani typography, synthwave visual hierarchy, audio settings, energy-continuous sub-stepping, strict multiball cap enforcement, 1-click launch, active trajectory guide in Classic Mode, and SQLite persistence."""

import json
import math
import os
import random
import sys
import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_FPS, TITLE,
    COLOR_BG, COLOR_SURFACE, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT,
    COLOR_NEON_CYAN, COLOR_ELECTRIC_PURPLE, COLOR_HOT_PINK, COLOR_SUNSET_ORANGE,
    COLOR_GRID_LINE, COLOR_HORIZON_SUN, COLOR_SUN_GLOW,
    DATA_DIR, BALL_SPEED, FONT_HEADING_PATH, FONT_BODY_PATH
)
from src.paddle import Paddle
from src.ball import Ball
from src.brick import Brick, BrickType
from src.powerups import PowerUp, PowerUpType, Laser
from src.particles import ParticleManager
from src.sounds import SoundManager
from src.database import DatabaseManager
from src.states import GameState, GameMode


def load_game_font(primary_path: str, size: int, fallback_name: str = "Segoe UI", bold: bool = False, italic: bool = False) -> pygame.font.Font:
    """Helper to safely load custom TTF font files with fallback to system fonts."""
    if os.path.exists(primary_path):
        try:
            return pygame.font.Font(primary_path, size)
        except Exception:
            pass
    return pygame.font.SysFont(fallback_name, size, bold=bold, italic=italic)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Neon Theme Custom Typography
        self.title_font = load_game_font(FONT_HEADING_PATH, 42, bold=True, italic=True)
        self.header_font = load_game_font(FONT_HEADING_PATH, 28, bold=True)
        self.font = load_game_font(FONT_BODY_PATH, 22, bold=True)
        self.sub_font = load_game_font(FONT_BODY_PATH, 16)

        # Managers
        self.particles = ParticleManager()
        self.sounds = SoundManager()
        self.db = DatabaseManager()

        # Progression & Mode tracking
        self.state = GameState.TITLE
        self.mode = GameMode.CLASSIC
        self.score = 0
        self.lives = 3
        self.level = 1
        self.max_levels = 3
        self.score_multiplier = 1.0
        self.show_trajectory = True
        self.score_saved = False
        self.session_bricks_destroyed = 0

        # Combo Streak Tracking
        self.combo_streak = 0

        # Camera Screen Shake Tracking
        self.shake_duration = 0.0
        self.shake_intensity = 0.0
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0

        self.level_data = self._load_levels_from_json()

        self.paddle = Paddle()
        self.balls: list[Ball] = []
        self.bricks: list[Brick] = []
        self.powerups: list[PowerUp] = []
        self.lasers: list[Laser] = []

        self.slow_motion_timer = 0.0

    def trigger_screen_shake(self, duration: float = 0.15, intensity: float = 4.0):
        self.shake_duration = max(self.shake_duration, duration)
        self.shake_intensity = max(self.shake_intensity, intensity)

    def _load_levels_from_json(self) -> list[dict]:
        json_path = os.path.join(DATA_DIR, "levels.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.max_levels = len(data)
                    return data
            except Exception as e:
                print(f"Warning: Failed to load levels.json ({e}). Falling back to default layout.")

        return []

    def _build_level_grid(self, level_num: int) -> list[Brick]:
        bricks = []
        idx = level_num - 1

        if self.level_data and 0 <= idx < len(self.level_data):
            ldata = self.level_data[idx]
            grid = ldata.get("grid", [])
            cols = ldata.get("cols", 9)
            brick_w = ldata.get("brick_width", 80.0)
            brick_h = ldata.get("brick_height", 24.0)
            padding = ldata.get("padding", 10.0)
            start_x = (SCREEN_WIDTH - (cols * (brick_w + padding) - padding)) / 2.0
            start_y = 90.0

            symbol_map = {
                "S": BrickType.STANDARD,
                "A": BrickType.ARMORED,
                "E": BrickType.EXPLOSIVE,
                "M": BrickType.MOVING,
                "U": BrickType.UNBREAKABLE
            }

            for r, row_str in enumerate(grid):
                tokens = row_str.strip().split()
                for c, token in enumerate(tokens):
                    if token in symbol_map:
                        bx = start_x + c * (brick_w + padding)
                        by = start_y + r * (brick_h + padding)
                        b_type = symbol_map[token]

                        if b_type == BrickType.MOVING:
                            # Calculate dedicated patrol bounds based on adjacent empty slots (.)
                            c_left = c
                            while c_left > 0 and tokens[c_left - 1] not in symbol_map:
                                c_left -= 1

                            c_right = c
                            while c_right < len(tokens) - 1 and tokens[c_right + 1] not in symbol_map:
                                c_right += 1

                            min_x = start_x + c_left * (brick_w + padding)
                            max_x = start_x + c_right * (brick_w + padding) + brick_w
                            move_range = (min_x, max_x)
                        else:
                            move_range = (0.0, 0.0)

                        bricks.append(Brick(bx, by, brick_w, brick_h, brick_type=b_type, move_range=move_range))

            return bricks

        cols, rows = 9, 4
        brick_w, brick_h, padding = 80.0, 24.0, 10.0
        start_x = (SCREEN_WIDTH - (cols * (brick_w + padding) - padding)) / 2.0
        start_y = 90.0
        for r in range(rows):
            for c in range(cols):
                bx = start_x + c * (brick_w + padding)
                by = start_y + r * (brick_h + padding)
                bricks.append(Brick(bx, by, brick_w, brick_h, brick_type=BrickType.STANDARD))

        return bricks

    def select_mode_and_start(self, mode: GameMode):
        self.mode = mode
        if self.mode == GameMode.CLASSIC:
            self.lives = 3
            self.score_multiplier = 1.0
            self.show_trajectory = True
        elif self.mode == GameMode.PRECISION:
            self.lives = 1
            self.score_multiplier = 1.5
            self.show_trajectory = False

        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.score_saved = False
        self.session_bricks_destroyed = 0
        self.combo_streak = 0
        if self.mode == GameMode.CLASSIC:
            self.lives = 3
        elif self.mode == GameMode.PRECISION:
            self.lives = 1
        self.level = 1
        self.load_level(self.level)

    def load_level(self, level_num: int):
        self.level = level_num
        self.bricks = self._build_level_grid(self.level)
        self.powerups.clear()
        self.lasers.clear()
        self.slow_motion_timer = 0.0
        self.reset_round()
        self.state = GameState.READY

    def reset_round(self):
        self.paddle = Paddle()
        primary_ball = Ball()

        speed_multiplier = 1.0 + (self.level - 1) * 0.10
        base_angle = math.radians(-75)
        primary_ball.set_angle(base_angle, BALL_SPEED * speed_multiplier)

        self.balls = [primary_ball]
        self.powerups.clear()
        self.lasers.clear()
        self.slow_motion_timer = 0.0
        self.combo_streak = 0
        self._mount_ball_to_paddle()

    def _mount_ball_to_paddle(self):
        if self.balls:
            self.balls[0].x = self.paddle.rect.centerx
            self.balls[0].y = self.paddle.rect.top - self.balls[0].radius

    def run(self):
        while self.is_running:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            dt = min(dt, 0.05)

            self._handle_events()
            self._update(dt)
            self._render()

        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t and self.mode == GameMode.CLASSIC:
                    self.show_trajectory = not self.show_trajectory

                if self.state == GameState.TITLE:
                    if event.key == pygame.K_SPACE:
                        self.select_mode_and_start(GameMode.CLASSIC)
                    elif event.key == pygame.K_1:
                        self.state = GameState.MODE_SELECT
                    elif event.key in (pygame.K_h, pygame.K_2):
                        self.state = GameState.HIGH_SCORES
                    elif event.key in (pygame.K_s, pygame.K_o, pygame.K_3):
                        self.state = GameState.SETTINGS

                elif self.state == GameState.MODE_SELECT:
                    if event.key in (pygame.K_1, pygame.K_c, pygame.K_SPACE):
                        self.select_mode_and_start(GameMode.CLASSIC)
                    elif event.key in (pygame.K_2, pygame.K_p):
                        self.select_mode_and_start(GameMode.PRECISION)
                    elif event.key in (pygame.K_h, pygame.K_ESCAPE):
                        self.state = GameState.TITLE
                    elif event.key in (pygame.K_o, pygame.K_s):
                        self.state = GameState.SETTINGS

                elif self.state == GameState.HIGH_SCORES:
                    if event.key in (pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN):
                        self.state = GameState.TITLE

                elif self.state == GameState.SETTINGS:
                    if event.key in (pygame.K_UP, pygame.K_RIGHT):
                        self.sounds.set_volume(self.sounds.volume + 0.10)
                        self.sounds.play("brick")
                    elif event.key in (pygame.K_DOWN, pygame.K_LEFT):
                        self.sounds.set_volume(self.sounds.volume - 0.10)
                        self.sounds.play("brick")
                    elif event.key == pygame.K_m:
                        self.sounds.toggle_mute()
                    elif event.key in (pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN):
                        self.state = GameState.TITLE

                elif self.state == GameState.READY:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_RETURN:
                        self.state = GameState.TITLE

                elif self.state == GameState.PLAYING:
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        self.state = GameState.PAUSED
                    elif event.key == pygame.K_RETURN:
                        self.state = GameState.TITLE

                elif self.state == GameState.PAUSED:
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_RETURN:
                        self.state = GameState.TITLE

                elif self.state == GameState.LEVEL_CLEAR:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if self.level < self.max_levels:
                            self.load_level(self.level + 1)
                        else:
                            self.state = GameState.MODE_SELECT

                elif self.state == GameState.GAME_OVER:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                        self.state = GameState.MODE_SELECT

    def get_combo_multiplier(self) -> float:
        if self.combo_streak <= 1:
            return 1.0
        return min(5.0, 1.0 + (self.combo_streak - 1) * 0.5)

    def _add_score(self, points: int, x: float | None = None, y: float | None = None):
        combo_mult = self.get_combo_multiplier()
        total_mult = self.score_multiplier * combo_mult
        pts_earned = int(points * total_mult)
        self.score += pts_earned

        if x is not None and y is not None:
            if combo_mult > 1.0:
                txt = f"+{pts_earned} (x{combo_mult:.1f})"
                color = COLOR_SUNSET_ORANGE
            else:
                txt = f"+{pts_earned}"
                color = COLOR_NEON_CYAN
            self.particles.spawn_floating_text(x, y, txt, color=color)

    def _try_spawn_powerup(self, brick: Brick):
        if random.random() < 0.30:
            ptype = random.choice(list(PowerUpType))
            self.powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery, ptype))

    def _get_brick_color(self, brick: Brick) -> tuple[int, int, int]:
        if brick.brick_type == BrickType.STANDARD:
            return COLOR_NEON_CYAN
        elif brick.brick_type == BrickType.ARMORED:
            return COLOR_ELECTRIC_PURPLE
        elif brick.brick_type == BrickType.EXPLOSIVE:
            return COLOR_HOT_PINK
        elif brick.brick_type == BrickType.MOVING:
            return COLOR_SUNSET_ORANGE
        return (108, 112, 134)

    def _on_brick_destroyed(self, brick: Brick):
        self.session_bricks_destroyed += 1

    def _trigger_explosion(self, origin_brick: Brick):
        self.sounds.play("explosion")
        self.trigger_screen_shake(duration=0.30, intensity=8.0)
        blast_area = origin_brick.rect.inflate(80.0, 60.0)

        for b in self.bricks:
            if not b.is_destroyed and not b.is_unbreakable and b != origin_brick:
                if blast_area.colliderect(b.rect):
                    self.particles.spawn_burst(b.rect.centerx, b.rect.centery, self._get_brick_color(b), count=16)
                    is_destroyed = b.hit()
                    self.combo_streak += 1
                    pts = 150 if is_destroyed else 50
                    self._add_score(pts, b.rect.centerx, b.rect.centery)
                    if is_destroyed:
                        self._on_brick_destroyed(b)
                        self._try_spawn_powerup(b)
                        if b.brick_type == BrickType.EXPLOSIVE:
                            self._trigger_explosion(b)

    def _spawn_multiball(self):
        """Spawns split ball vectors while strictly enforcing an 8-ball active cap limit."""
        max_active_balls = 8
        capacity = max_active_balls - len(self.balls)
        if capacity <= 0:
            return

        new_balls = []
        for b in list(self.balls):
            if len(new_balls) >= capacity:
                break

            current_angle = math.atan2(b.vy, b.vx)
            speed = b.speed

            # Add left split ball
            b_left = Ball()
            b_left.x, b_left.y = b.x, b.y
            b_left.set_angle(current_angle - math.radians(30), speed)
            new_balls.append(b_left)

            # Add right split ball if capacity allows
            if len(new_balls) < capacity:
                b_right = Ball()
                b_right.x, b_right.y = b.x, b.y
                b_right.set_angle(current_angle + math.radians(30), speed)
                new_balls.append(b_right)

        self.balls.extend(new_balls)

    def _save_final_score(self):
        if not self.score_saved:
            mode_str = "Classic" if self.mode == GameMode.CLASSIC else "Precision"
            self.db.save_score(mode_str, self.score, self.level)
            if self.session_bricks_destroyed > 0:
                self.db.add_bricks_destroyed(self.session_bricks_destroyed)
                self.session_bricks_destroyed = 0
            self.score_saved = True

    def _update(self, dt: float):
        if self.shake_duration > 0:
            self.shake_duration -= dt
            if self.shake_duration <= 0:
                self.shake_duration = 0.0
                self.shake_intensity = 0.0
                self.shake_offset_x = 0.0
                self.shake_offset_y = 0.0
            else:
                self.shake_offset_x = random.uniform(-self.shake_intensity, self.shake_intensity)
                self.shake_offset_y = random.uniform(-self.shake_intensity, self.shake_intensity)
        else:
            self.shake_offset_x = 0.0
            self.shake_offset_y = 0.0

        if self.state in (GameState.TITLE, GameState.MODE_SELECT, GameState.HIGH_SCORES, GameState.SETTINGS, GameState.PAUSED, GameState.GAME_OVER, GameState.LEVEL_CLEAR):
            return

        self.paddle.update(dt)
        self.particles.update(dt)

        if self.slow_motion_timer > 0:
            self.slow_motion_timer -= dt

        keys = pygame.key.get_pressed()
        if self.state == GameState.PLAYING and self.paddle.has_laser:
            if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]:
                new_shots = self.paddle.shoot_lasers()
                if new_shots:
                    self.sounds.play("laser")
                    self.lasers.extend(new_shots)

        for brick in self.bricks:
            brick.update(dt)

        if self.state == GameState.READY:
            self._mount_ball_to_paddle()
            return

        if self.state == GameState.PLAYING:
            ball_dt = dt * 0.60 if self.slow_motion_timer > 0 else dt

            for laser in self.lasers:
                laser.update(dt)
                if not laser.is_offscreen:
                    for b in self.bricks:
                        if not b.is_destroyed and laser.rect.colliderect(b.rect):
                            laser.is_offscreen = True
                            if not b.is_unbreakable:
                                self.combo_streak += 1
                                self.sounds.play("brick")
                                self.trigger_screen_shake(duration=0.10, intensity=2.0)
                                self.particles.spawn_burst(laser.x, laser.y, self._get_brick_color(b), count=6)
                                is_destroyed = b.hit()
                                pts = 150 if is_destroyed else 50
                                self._add_score(pts, laser.x, laser.y)
                                if is_destroyed:
                                    self._on_brick_destroyed(b)
                                    self._try_spawn_powerup(b)
                                    if b.brick_type == BrickType.EXPLOSIVE:
                                        self._trigger_explosion(b)
                            break

            self.lasers = [l for l in self.lasers if not l.is_offscreen]

            for p in self.powerups:
                p.update(dt)
                if not p.is_collected and not p.is_offscreen:
                    if p.rect.colliderect(self.paddle.rect):
                        p.is_collected = True
                        self.trigger_screen_shake(duration=0.12, intensity=3.0)
                        self.particles.spawn_burst(p.x, p.y, COLOR_SUNSET_ORANGE, count=10)

                        if p.power_type == PowerUpType.WIDE_PADDLE:
                            self.sounds.play("powerup_wide")
                            self.paddle.apply_wide_paddle(10.0)
                        elif p.power_type == PowerUpType.SLOW_MOTION:
                            self.sounds.play("powerup_slow")
                            self.slow_motion_timer = 8.0
                        elif p.power_type == PowerUpType.MULTIBALL:
                            self.sounds.play("powerup_multi")
                            self._spawn_multiball()
                        elif p.power_type == PowerUpType.LASER_PADDLE:
                            self.sounds.play("powerup_laser")
                            self.paddle.apply_laser_paddle(10.0)

            self.powerups = [p for p in self.powerups if not p.is_collected and not p.is_offscreen]

            for ball in self.balls:
                sub_steps = ball.get_substep_count(ball_dt)
                sub_dt = ball_dt / sub_steps

                ball.trail_positions.append((ball.x, ball.y))
                if len(ball.trail_positions) > 8:
                    ball.trail_positions.pop(0)

                # Track targets hit in this frame to prevent duplicate multi-hitting
                hit_targets_this_frame = set()

                for _ in range(sub_steps):
                    ball.update_step(sub_dt)

                    if "paddle" not in hit_targets_this_frame:
                        if ball.resolve_paddle_collision(self.paddle.rect):
                            hit_targets_this_frame.add("paddle")
                            self.combo_streak = 0
                            self.sounds.play("paddle")
                            self.trigger_screen_shake(duration=0.08, intensity=1.5)
                            self.particles.spawn_burst(ball.x, self.paddle.rect.top, COLOR_NEON_CYAN, count=6, speed_max=120.0)

                    for brick in self.bricks:
                        if not brick.is_destroyed and id(brick) not in hit_targets_this_frame:
                            if ball.resolve_box_collision(brick.rect):
                                hit_targets_this_frame.add(id(brick))
                                if not brick.is_unbreakable:
                                    self.combo_streak += 1
                                self.sounds.play("brick")
                                self.trigger_screen_shake(duration=0.10, intensity=2.5)
                                self.particles.spawn_burst(ball.x, ball.y, self._get_brick_color(brick), count=10)
                                is_destroyed = brick.hit()
                                if not brick.is_unbreakable:
                                    pts = 150 if is_destroyed else 50
                                    self._add_score(pts, ball.x, ball.y)

                                if is_destroyed:
                                    self._on_brick_destroyed(brick)
                                    self._try_spawn_powerup(brick)
                                    if brick.brick_type == BrickType.EXPLOSIVE:
                                        self._trigger_explosion(brick)

            self.balls = [b for b in self.balls if b.y - b.radius < SCREEN_HEIGHT]

            if len(self.balls) == 0:
                self.combo_streak = 0
                self.lives -= 1
                self.trigger_screen_shake(duration=0.25, intensity=6.0)
                if self.lives > 0:
                    self.sounds.play("life_lost")
                    self.reset_round()
                    self.state = GameState.READY
                else:
                    self.sounds.play("game_over")
                    self._save_final_score()
                    self.state = GameState.GAME_OVER
                return

            if all(b.is_destroyed for b in self.bricks if not b.is_unbreakable):
                if self.state != GameState.LEVEL_CLEAR:
                    self.state = GameState.LEVEL_CLEAR
                    if self.level < self.max_levels:
                        self.sounds.play("level_clear")
                    else:
                        self.sounds.play("game_complete")
                        self._save_final_score()

    def _draw_synthwave_background(self, surface: pygame.Surface):
        """Draws a low-contrast procedural synthwave grid and horizon elements."""
        surface.fill(COLOR_BG)

        horizon_y = 480

        # 1. Subtle Synthwave Sun on Horizon
        sun_radius = 50
        sun_center = (SCREEN_WIDTH // 2, horizon_y)

        glow_surf = pygame.Surface((sun_radius * 2 + 30, sun_radius * 2 + 30), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*COLOR_SUN_GLOW, 50), (sun_radius + 15, sun_radius + 15), sun_radius + 15)
        surface.blit(glow_surf, (sun_center[0] - sun_radius - 15, sun_center[1] - sun_radius - 15))

        sun_surf = pygame.Surface((sun_radius * 2, sun_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(sun_surf, (*COLOR_HORIZON_SUN, 160), (sun_radius, sun_radius), sun_radius)
        for line_y in range(12, sun_radius * 2, 8):
            line_height = max(1, int((line_y / (sun_radius * 2)) * 3))
            pygame.draw.rect(sun_surf, (0, 0, 0, 0), (0, line_y, sun_radius * 2, line_height))

        surface.blit(sun_surf, (sun_center[0] - sun_radius, sun_center[1] - sun_radius))

        # 2. Horizon Line
        pygame.draw.line(surface, COLOR_GRID_LINE, (0, horizon_y), (SCREEN_WIDTH, horizon_y), 1)

        # 3. Receding Perspective Grid Lines
        vanishing_x = SCREEN_WIDTH // 2
        num_v_lines = 16
        for i in range(-num_v_lines // 2, num_v_lines // 2 + 1):
            bottom_x = vanishing_x + i * 85
            pygame.draw.line(surface, COLOR_GRID_LINE, (vanishing_x + i * 6, horizon_y), (bottom_x, SCREEN_HEIGHT), 1)

        y = float(horizon_y)
        spacing = 4.0
        while y < SCREEN_HEIGHT:
            pygame.draw.line(surface, COLOR_GRID_LINE, (0, int(y)), (SCREEN_WIDTH, int(y)), 1)
            y += spacing
            spacing *= 1.25

    def _draw_trajectory_line(self, surface: pygame.Surface):
        if self.balls and self.show_trajectory:
            points = self.balls[0].get_predicted_trajectory(self.bricks, self.paddle.rect)
            if len(points) > 1:
                for i in range(0, len(points) - 1, 3):
                    start_p = points[i]
                    end_p = points[min(i + 1, len(points) - 1)]
                    pygame.draw.line(surface, (255, 45, 149, 120), start_p, end_p, 2)

    def _draw_heart(self, surface: pygame.Surface, x: float, y: float, size: float = 7.0, color=COLOR_HOT_PINK):
        top_left_circle = (int(x - size / 2), int(y))
        top_right_circle = (int(x + size / 2), int(y))
        pygame.draw.circle(surface, color, top_left_circle, int(size / 2))
        pygame.draw.circle(surface, color, top_right_circle, int(size / 2))
        polygon_points = [
            (x - size, y + size * 0.2),
            (x + size, y + size * 0.2),
            (x, y + size * 1.3)
        ]
        pygame.draw.polygon(surface, color, polygon_points)

    def _render_hud(self, surface: pygame.Surface):
        score_txt = self.font.render(f"SCORE: {self.score}", True, COLOR_TEXT)
        level_txt = self.font.render(f"LEVEL: {self.level}/{self.max_levels}", True, COLOR_TEXT)
        mode_label = "CLASSIC" if self.mode == GameMode.CLASSIC else "PRECISION (1.5x)"
        mode_txt = self.sub_font.render(f"MODE: {mode_label}", True, COLOR_TEXT_DIM)

        surface.blit(score_txt, (20, 15))
        surface.blit(mode_txt, (20, 42))
        surface.blit(level_txt, (SCREEN_WIDTH - 150, 15))

        lives_label = self.font.render("LIVES:", True, COLOR_HOT_PINK)
        surface.blit(lives_label, (SCREEN_WIDTH // 2 - 60, 15))

        start_x = SCREEN_WIDTH // 2 + 15
        for i in range(self.lives):
            self._draw_heart(surface, start_x + i * 22, 26)

        badge_x = 220
        badge_y = 42

        combo_mult = self.get_combo_multiplier()
        if combo_mult > 1.0:
            c_txt = self.sub_font.render(f"COMBO: x{combo_mult:.1f}", True, COLOR_SUNSET_ORANGE)
            surface.blit(c_txt, (badge_x, badge_y))
            badge_x += 110

        if self.paddle.is_wide:
            w_txt = self.sub_font.render(f"WIDE: {int(self.paddle.wide_timer)}s", True, COLOR_NEON_CYAN)
            surface.blit(w_txt, (badge_x, badge_y))
            badge_x += 100

        if self.paddle.has_laser:
            l_txt = self.sub_font.render(f"LASER: {int(self.paddle.laser_timer)}s", True, COLOR_HOT_PINK)
            surface.blit(l_txt, (badge_x, badge_y))
            badge_x += 100

        if self.slow_motion_timer > 0:
            s_txt = self.sub_font.render(f"SLOW: {int(self.slow_motion_timer)}s", True, COLOR_ELECTRIC_PURPLE)
            surface.blit(s_txt, (badge_x, badge_y))

    def _render_title_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 15, 46, 220))
        self.screen.blit(overlay, (0, 0))

        # Title & Sub-tagline
        t_surf = self.title_font.render("NEONBREAK", True, COLOR_ELECTRIC_PURPLE)
        t_rect = t_surf.get_rect(center=(SCREEN_WIDTH // 2, 130))
        self.screen.blit(t_surf, t_rect)

        sub_tag = self.sub_font.render("BREAK • BOUNCE • CONQUER", True, COLOR_NEON_CYAN)
        s_rect = sub_tag.get_rect(center=(SCREEN_WIDTH // 2, 175))
        self.screen.blit(sub_tag, s_rect)

        # Styled Selection Cards
        card_w, card_h = 440, 56
        cards = [
            ("[SPACE] QUICK START", "Launch Classic Mode Directly", COLOR_NEON_CYAN, 240),
            ("[1] MODE SELECT", "Choose Classic or Precision Mode", COLOR_ELECTRIC_PURPLE, 315),
            ("[2] HIGH SCORES", "View Leaderboards & Lifetime Stats", COLOR_HOT_PINK, 390),
            ("[3] AUDIO SETTINGS", "Configure Volume & Sound Controls", COLOR_SUNSET_ORANGE, 465),
        ]

        for title, desc, color, y_pos in cards:
            c_rect = pygame.Rect(SCREEN_WIDTH // 2 - card_w // 2, y_pos, card_w, card_h)
            pygame.draw.rect(self.screen, COLOR_SURFACE, c_rect, border_radius=8)
            pygame.draw.rect(self.screen, color, c_rect, 2, border_radius=8)

            t_txt = self.font.render(title, True, color)
            d_txt = self.sub_font.render(desc, True, COLOR_TEXT)
            self.screen.blit(t_txt, (c_rect.x + 20, c_rect.y + 8))
            self.screen.blit(d_txt, (c_rect.x + 20, c_rect.y + 32))

        # Footer Prompts
        prompt = self.sub_font.render("Press SPACE for Quick Start | Press 1, 2, or 3 to Navigate", True, COLOR_TEXT_DIM)
        p_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, 545))
        self.screen.blit(prompt, p_rect)

    def _render_mode_select(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 15, 46, 235))
        self.screen.blit(overlay, (0, 0))

        t_surf = self.header_font.render("SELECT GAME MODE", True, COLOR_ELECTRIC_PURPLE)
        t_rect = t_surf.get_rect(center=(SCREEN_WIDTH // 2, 140))
        self.screen.blit(t_surf, t_rect)

        c_title = self.font.render("[1] CLASSIC MODE", True, COLOR_NEON_CYAN)
        c_desc = self.sub_font.render("• 3 Lives  • Directional Preview (T key)  • Standard Scoring", True, COLOR_TEXT)
        self.screen.blit(c_title, (SCREEN_WIDTH // 2 - 200, 230))
        self.screen.blit(c_desc, (SCREEN_WIDTH // 2 - 200, 260))

        p_title = self.font.render("[2] PRECISION MODE", True, COLOR_HOT_PINK)
        p_desc = self.sub_font.render("• 1 Life Only  • Directional Preview Off  • 1.5x Multiplier", True, COLOR_TEXT)
        self.screen.blit(p_title, (SCREEN_WIDTH // 2 - 200, 330))
        self.screen.blit(p_desc, (SCREEN_WIDTH // 2 - 200, 360))

        h_info = self.sub_font.render("Press [H] High Scores | Press [S] Audio Settings", True, COLOR_TEXT_DIM)
        self.screen.blit(h_info, (SCREEN_WIDTH // 2 - 180, 430))

        prompt = self.sub_font.render("Press 1 for Classic | Press 2 for Precision", True, COLOR_SUNSET_ORANGE)
        p_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, 510))
        self.screen.blit(prompt, p_rect)

    def _render_settings(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 15, 46, 240))
        self.screen.blit(overlay, (0, 0))

        t_surf = self.header_font.render("AUDIO SETTINGS", True, COLOR_ELECTRIC_PURPLE)
        t_rect = t_surf.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(t_surf, t_rect)

        vol_pct = int(self.sounds.volume * 100)
        v_title = self.font.render(f"MASTER VOLUME: {vol_pct}%", True, COLOR_TEXT)
        self.screen.blit(v_title, (SCREEN_WIDTH // 2 - 160, 210))

        bar_x = SCREEN_WIDTH // 2 - 160
        bar_y = 250
        bar_w = 320
        bar_h = 24
        pygame.draw.rect(self.screen, COLOR_SURFACE, (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        fill_w = int(bar_w * self.sounds.volume)
        if fill_w > 0:
            pygame.draw.rect(self.screen, COLOR_NEON_CYAN, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
        pygame.draw.rect(self.screen, COLOR_ELECTRIC_PURPLE, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)

        mute_str = "MUTED" if self.sounds.muted else "ACTIVE"
        mute_color = COLOR_HOT_PINK if self.sounds.muted else COLOR_NEON_CYAN
        m_txt = self.font.render(f"SOUND MUTE: [{mute_str}]", True, mute_color)
        self.screen.blit(m_txt, (SCREEN_WIDTH // 2 - 160, 310))

        i1 = self.sub_font.render("Use LEFT / RIGHT or UP / DOWN to adjust Volume", True, COLOR_TEXT)
        i2 = self.sub_font.render("Press [M] to Toggle Mute", True, COLOR_TEXT)
        self.screen.blit(i1, (SCREEN_WIDTH // 2 - 180, 380))
        self.screen.blit(i2, (SCREEN_WIDTH // 2 - 180, 410))

        prompt = self.sub_font.render("Press SPACE or ESC to Return", True, COLOR_TEXT_DIM)
        p_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, 510))
        self.screen.blit(prompt, p_rect)

    def _render_high_scores(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 15, 46, 240))
        self.screen.blit(overlay, (0, 0))

        t_surf = self.header_font.render("HIGH SCORES", True, COLOR_ELECTRIC_PURPLE)
        t_rect = t_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(t_surf, t_rect)

        total_bricks = self.db.get_bricks_destroyed()
        stat_txt = self.sub_font.render(f"Total Bricks Destroyed: {total_bricks:,}", True, COLOR_SUNSET_ORANGE)
        s_rect = stat_txt.get_rect(center=(SCREEN_WIDTH // 2, 130))
        self.screen.blit(stat_txt, s_rect)

        cl_title = self.font.render("CLASSIC MODE TOP 5", True, COLOR_NEON_CYAN)
        self.screen.blit(cl_title, (80, 180))
        classic_scores = self.db.get_top_scores("Classic", limit=5)
        if not classic_scores:
            empty_txt = self.sub_font.render("No records set yet", True, (147, 153, 178))
            self.screen.blit(empty_txt, (80, 215))
        else:
            for i, (sc, lvl, dt_str) in enumerate(classic_scores):
                entry = f"{i+1}. {sc:,} pts (Lvl {lvl}) - {dt_str}"
                txt = self.sub_font.render(entry, True, COLOR_TEXT)
                self.screen.blit(txt, (80, 215 + i * 28))

        pr_title = self.font.render("PRECISION MODE TOP 5", True, COLOR_HOT_PINK)
        self.screen.blit(pr_title, (460, 180))
        precision_scores = self.db.get_top_scores("Precision", limit=5)
        if not precision_scores:
            empty_txt = self.sub_font.render("No records set yet", True, (147, 153, 178))
            self.screen.blit(empty_txt, (460, 215))
        else:
            for i, (sc, lvl, dt_str) in enumerate(precision_scores):
                entry = f"{i+1}. {sc:,} pts (Lvl {lvl}) - {dt_str}"
                txt = self.sub_font.render(entry, True, COLOR_TEXT)
                self.screen.blit(txt, (460, 215 + i * 28))

        prompt = self.sub_font.render("Press SPACE or ESC to Return", True, COLOR_TEXT_DIM)
        p_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, 530))
        self.screen.blit(prompt, p_rect)

    def _render_overlay(self, title: str, subtitle: str, title_color=COLOR_TEXT):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 15, 46, 210))
        self.screen.blit(overlay, (0, 0))

        t_surf = self.header_font.render(title, True, title_color)
        t_rect = t_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(t_surf, t_rect)

        s_surf = self.sub_font.render(subtitle, True, COLOR_TEXT)
        s_rect = s_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(s_surf, s_rect)

    def _render(self):
        self._draw_synthwave_background(self.game_surface)

        # Draw trajectory guide in Classic Mode when enabled (both READY and PLAYING)
        if self.show_trajectory and self.mode == GameMode.CLASSIC and self.state in (GameState.READY, GameState.PLAYING):
            self._draw_trajectory_line(self.game_surface)

        for brick in self.bricks:
            brick.draw(self.game_surface)

        for p in self.powerups:
            p.draw(self.game_surface)

        for laser in self.lasers:
            laser.draw(self.game_surface)

        self.particles.draw(self.game_surface)
        self.paddle.draw(self.game_surface)

        for ball in self.balls:
            ball.draw(self.game_surface)

        self._render_hud(self.game_surface)

        self.screen.fill((5, 8, 25))
        self.screen.blit(self.game_surface, (int(self.shake_offset_x), int(self.shake_offset_y)))

        if self.state == GameState.TITLE:
            self._render_title_screen()

        elif self.state == GameState.MODE_SELECT:
            self._render_mode_select()

        elif self.state == GameState.HIGH_SCORES:
            self._render_high_scores()

        elif self.state == GameState.SETTINGS:
            self._render_settings()

        elif self.state == GameState.READY:
            launch_txt = self.sub_font.render("Press SPACE to Launch Ball | Press ENTER for Main Menu", True, COLOR_TEXT_DIM)
            l_rect = launch_txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(launch_txt, l_rect)

        elif self.state == GameState.PAUSED:
            self._render_overlay("PAUSED", "Press P or ESC to Resume | Press ENTER for Main Menu", COLOR_NEON_CYAN)

        elif self.state == GameState.LEVEL_CLEAR:
            if self.level < self.max_levels:
                self._render_overlay(f"LEVEL {self.level} CLEAR!", "Press SPACE for Next Level", COLOR_ELECTRIC_PURPLE)
            else:
                self._render_overlay("CONGRATULATIONS!", f"All Levels Complete! Final Score: {self.score}", COLOR_SUNSET_ORANGE)

        elif self.state == GameState.GAME_OVER:
            self._render_overlay("GAME OVER", f"Final Score: {self.score} | Press SPACE or R to Restart", COLOR_HOT_PINK)

        pygame.display.flip()