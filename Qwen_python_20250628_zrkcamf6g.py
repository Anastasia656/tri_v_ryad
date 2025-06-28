import pygame
import random
import os
import json

# Константы
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
CELL_SIZE = WIDTH // COLS
FPS = 60
ANIMATION_SPEED = 10

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Пути
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
RECORDS_FILE = "records.json"

# Элементы и бустеры
ELEMENT_IMAGES = {
    '🔴': "red.png",
    '🔵': "blue.png",
    '🟢': "green.png",
    '🟡': "yellow.png",
    '🟣': "purple.png"
}
BOOSTER_IMAGES = {
    'hammer': "hammer.png",
    'bomb': "bomb.png",
    'swap': "swap.png",
    'rainbow': "rainbow.png"
}

# Уровни
levels = [
    {'goals': {'🔴': 30}, 'max_moves': 20},
    {'goals': {'🟢': 40}, 'max_moves': 25},
    {'goals': {'🔵': 50}, 'max_moves': 30},
    {'goals': {'🟡': 60}, 'max_moves': 35},
    {'goals': {'🔴': 20, '🔵': 20, '🟢': 20, '🟡': 20, '🟣': 20}, 'max_moves': 40},
    {'goals': {'🟣': 40, '🟢': 40}, 'max_moves': 30},
    {'goals': {'🔴': 30, '🟡': 30}, 'max_moves': 25}
]

# Достижения
achievements = [
    {"name": "Начинающий", "desc": "Соберите 100 очков", "condition": lambda: score >= 100, "reward": {"hammer": 1}, "unlocked": False},
    {"name": "Комбо", "desc": "Удалите 50 элементов за игру", "condition": lambda: total_removed >= 50, "reward": {"bomb": 1}, "unlocked": False},
    {"name": "Экономия ходов", "desc": "Завершите уровень за 5 ходов", "condition": lambda: max_moves - current_moves >= 5, "reward": {"swap": 1}, "unlocked": False}
]

# Инициализация
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3 в ряд")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# Переменные
board = []
score = 0
total_removed = 0
selected = None
current_level = 0
current_moves = 0
max_moves = 0
goals = {}
progress = {}
state = "menu"  # menu, select_level, game, game_over, goal_reached

# Бустеры
boosters = {
    'hammer': 1,
    'bomb': 1,
    'swap': 1,
    'rainbow': 1
}
selected_booster = None

# Уведомления о достижениях
achievement_notification = None
notification_time = 0
NOTIFICATION_DURATION = 2000  # мс

# Класс кнопки
class Button:
    def __init__(self, text, x, y, w, h, color, hover_color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = pygame.font.SysFont(None, 36)
    
    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, color, self.rect)
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)

# Кнопки
start_button = Button("Начать", WIDTH//2 - 100, HEIGHT//2 - 50, 200, 50, (0, 150, 255), (0, 100, 200))
exit_button = Button("Выход", WIDTH//2 - 100, HEIGHT//2 + 20, 200, 50, (200, 50, 50), (150, 30, 30))
level_buttons = [Button(f"Уровень {i+1}", WIDTH//2 - 100, 100 + i*60, 200, 50, (100, 200, 100), (80, 150, 80)) for i in range(len(levels))]

# Загрузка изображений
def load_image(path, size=None):
    try:
        img = pygame.image.load(os.path.join(ASSETS_DIR, path))
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except:
        img = pygame.Surface(size or (CELL_SIZE, CELL_SIZE))
        img.fill((255, 255, 255))
        return img

# Фон
background_img = load_image("background.jpg", (WIDTH, HEIGHT))

# Элементы
element_images = {key: load_image(path, (CELL_SIZE - 10, CELL_SIZE - 10)) 
                  for key, path in ELEMENT_IMAGES.items()}

# Бустеры
booster_images = {key: load_image(path, (CELL_SIZE, CELL_SIZE)) 
                  for key, path in BOOSTER_IMAGES.items()}

# Функции
def create_board():
    return [[random.choice(list(ELEMENT_IMAGES.keys())) for _ in range(COLS)] for _ in range(ROWS)]

def draw_board(board):
    for row in range(ROWS):
        for col in range(COLS):
            element = board[row][col]
            if element != ' ':  # Используем пробел вместо '⚪'
                img = element_images[element]
                x = col * CELL_SIZE + 5
                y = row * CELL_SIZE + 5
                screen.blit(img, (x, y))
    if selected:
        row, col = selected
        pygame.draw.rect(screen, (255, 255, 0), (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE), 3)

def find_matches(board):
    matches = set()
    for row in range(ROWS):
        for col in range(COLS - 2):
            if board[row][col] == board[row][col+1] == board[row][col+2]:
                for i in range(3): matches.add((row, col+i))
    for col in range(COLS):
        for row in range(ROWS - 2):
            if board[row][col] == board[row+1][col] == board[row+2][col]:
                for i in range(3): matches.add((row+i, col))
    return matches

def remove_matches(board, matches):
    global score, total_removed
    for row, col in matches:
        board[row][col] = ' '
    score += len(matches) * 10
    total_removed += len(matches)

def update_progress(matches):
    for row, col in matches:
        color = board[row][col]
        if color in progress:
            progress[color] += 1

def fade_out_animation(board, matches):
    fade_steps = 10
    for step in range(fade_steps):
        alpha = int(255 * (1 - step / fade_steps))
        screen.blit(background_img, (0, 0))
        draw_board(board)
        for row, col in matches:
            element = board[row][col]
            if element == ' ': continue
            img = element_images[element].copy()
            img.set_alpha(alpha)
            x = col * CELL_SIZE + 5
            y = row * CELL_SIZE + 5
            screen.blit(img, (x, y))
        pygame.display.flip()
        pygame.time.wait(30)

def fade_in_animation(board, new_cells):
    fade_steps = 10
    for step in range(fade_steps + 1):
        alpha = int(255 * (step / fade_steps))
        screen.blit(background_img, (0, 0))
        draw_board(board)
        for row, col in new_cells:
            img = element_images[board[row][col]].copy()
            img.set_alpha(alpha)
            x = col * CELL_SIZE + 5
            y = row * CELL_SIZE + 5
            screen.blit(img, (x, y))
        pygame.display.flip()
        pygame.time.wait(30)

def drop_elements(board):
    movements = []
    new_cells = []
    for col in range(COLS):
        empty = []
        for row in reversed(range(ROWS)):
            if board[row][col] == ' ':
                empty.append(row)
            elif empty:
                src_row = row
                dst_row = empty.pop(0)
                movements.append(((src_row, col), (dst_row, col), board[src_row][col]))
                board[dst_row][col] = board[src_row][col]
                board[src_row][col] = ' '
        for row in empty:
            board[row][col] = random.choice(list(ELEMENT_IMAGES.keys()))
            new_cells.append((row, col))
    return movements, new_cells

def animate_drop(movements):
    for step in range(CELL_SIZE + 1, 0, -ANIMATION_SPEED):
        screen.blit(background_img, (0, 0))
        draw_board(board)
        for (src_row, src_col), (dst_row, dst_col), element in movements:
            x = src_col * CELL_SIZE + 5
            y = src_row * CELL_SIZE + step
            screen.blit(element_images[element], (x, y))
        draw_interface()
        pygame.display.flip()
        pygame.time.wait(10)

def is_valid_move(pos1, pos2):
    r1, c1 = pos1
    r2, c2 = pos2
    return abs(r1 - r2) + abs(c1 - c2) == 1

def swap_cells(board, pos1, pos2):
    r1, c1 = pos1
    r2, c2 = pos2
    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]

def has_moves(board):
    for row in range(ROWS):
        for col in range(COLS):
            if col < COLS - 1:
                temp = [row[:] for row in board]
                temp[row][col], temp[row][col+1] = temp[row][col+1], temp[row][col]
                if find_matches(temp): return True
            if row < ROWS - 1:
                temp = [row[:] for row in board]
                temp[row][col], temp[row+1][col] = temp[row+1][col], temp[row][col]
                if find_matches(temp): return True
    return False

def check_goals():
    for color in goals:
        if progress.get(color, 0) < goals[color]: return False
    return True

def draw_interface():
    x = 10
    y = 10
    score_text = font.render(f"Счёт: {score}", True, WHITE)
    screen.blit(score_text, (x, y))
    y += 40
    moves_text = font.render(f"Ходы: {max_moves - current_moves}/{max_moves}", True, WHITE)
    screen.blit(moves_text, (x, y))
    y += 40
    for color in goals:
        goal_text = font.render(f"{color}: {progress[color]}/{goals[color]}", True, WHITE)
        screen.blit(goal_text, (x, y))
        y += 40
    y = 10
    for booster in boosters:
        img = booster_images[booster]
        rect = img.get_rect(topleft=(10, y + 200))
        screen.blit(img, rect)
        count_text = font.render(f"x{boosters[booster]}", True, WHITE)
        screen.blit(count_text, (x + 40, y + 210))
        if selected_booster == booster:
            pygame.draw.rect(screen, (255, 255, 0), rect, 3)
        y += CELL_SIZE + 10
    if achievement_notification and pygame.time.get_ticks() - notification_time < NOTIFICATION_DURATION:
        text = font.render(f"Достижение: {achievement_notification}", True, (0, 255, 0))
        pygame.draw.rect(screen, (30, 30, 30), (WIDTH // 2 - 200, 10, 400, 40))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 15))

def check_achievements():
    global achievement_notification, notification_time
    for ach in achievements:
        if ach["unlocked"]: continue
        if ach["condition"]():
            ach["unlocked"] = True
            reward = ach["reward"]
            for booster in reward:
                boosters[booster] += reward[booster]
            achievement_notification = ach["name"]
            notification_time = pygame.time.get_ticks()

def load_records():
    if os.path.exists(RECORDS_FILE):
        try:
            with open(RECORDS_FILE, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    for i in range(len(levels)):
        key = f"level_{i}"
        if key not in data or not isinstance(data[key], dict):
            data[key] = {"unlocked": True, "best_score": 0}
    for ach in achievements:
        key = f"achievement_{ach['name']}"
        if key in data:
            ach["unlocked"] = data[key]
        else:
            ach["unlocked"] = False
    return data

def save_records(records):
    for i in range(len(levels)):
        key = f"level_{i}"
        if key not in records or not isinstance(records[key], dict):
            records[key] = {"unlocked": True, "best_score": 0}
    for ach in achievements:
        key = f"achievement_{ach['name']}"
        records[key] = ach["unlocked"]
    with open(RECORDS_FILE, 'w') as f:
        json.dump(records, f, indent=4)

def select_level_screen():
    screen.blit(background_img, (0, 0))
    for btn in level_buttons:
        btn.draw(screen)
    exit_button.draw(screen)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            for i, btn in enumerate(level_buttons):
                if btn.is_clicked(event):
                    if records[f"level_{i}"]["unlocked"]:
                        return i
            if exit_button.is_clicked(event):
                return "menu"
        pygame.display.flip()

def goal_reached_screen():
    screen.fill(BLACK)
    text = font.render("Цель достигнута!", True, WHITE)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
    exit_button.draw(screen)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            if exit_button.is_clicked(event):
                return "menu"
        pygame.display.flip()

def game_over_screen():
    screen.fill(BLACK)
    text = font.render("Игра окончена!", True, WHITE)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
    exit_button.draw(screen)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            if exit_button.is_clicked(event):
                return "menu"
        pygame.display.flip()

def main_menu():
    screen.blit(background_img, (0, 0))
    start_button.draw(screen)
    exit_button.draw(screen)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            if start_button.is_clicked(event):
                return "select_level"
            if exit_button.is_clicked(event):
                return "exit"
        pygame.display.flip()

def use_booster(board, booster, pos):
    global selected_booster, selected
    row, col = pos
    if booster == 'hammer' and boosters[booster] > 0:
        board[row][col] = ' '
        boosters[booster] -= 1
    elif booster == 'bomb' and boosters[booster] > 0:
        for r in range(max(0, row-1), min(ROWS, row+2)):
            for c in range(max(0, col-1), min(COLS, col+2)):
                board[r][c] = ' '
        boosters[booster] -= 1
    elif booster == 'swap' and boosters[booster] > 0:
        if selected_booster == 'swap':
            if selected:
                swap_cells(board, selected, (row, col))
                selected_booster = None
                selected = None
            else:
                selected = (row, col)
        else:
            selected_booster = 'swap'
            selected = (row, col)
        return
    elif booster == 'rainbow' and boosters[booster] > 0:
        target_color = board[row][col]
        for r in range(ROWS):
            for c in range(COLS):
                if board[r][c] == target_color:
                    board[r][c] = ' '
        boosters[booster] -= 1
    
    while True:
        matches = find_matches(board)
        if not matches: break
        update_progress(matches)
        fade_out_animation(board, matches)
        remove_matches(board, matches)
        movements, new_cells = drop_elements(board)
        animate_drop(movements)
        fade_in_animation(board, new_cells)

def init_level(level_index):
    global board, score, current_moves, max_moves, goals, progress, boosters
    level = levels[level_index]
    board = create_board()
    score = 0
    current_moves = 0
    max_moves = level['max_moves']
    goals = level['goals']
    progress = {color: 0 for color in goals}
    boosters = {
        'hammer': 1,
        'bomb': 1,
        'swap': 1,
        'rainbow': 1
    }

def main():
    global state, current_level, selected_booster, current_moves
    records = load_records()
    running = True
    while running:
        if state == "menu":
            choice = main_menu()
            if choice == "select_level": 
                state = "select_level"
            elif choice == "exit": 
                break
        elif state == "select_level":
            result = select_level_screen()
            if result == "menu": 
                state = "menu"
            elif result == "exit": 
                running = False
            else:
                current_level = result
                init_level(current_level)
                state = "game"
        elif state == "game":
            clock.tick(FPS)
            screen.blit(background_img, (0, 0))
            draw_board(board)
            draw_interface()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x_click, y_click = event.pos
                    booster_rects = []
                    y = 10
                    for booster in boosters:
                        rect = booster_images[booster].get_rect(topleft=(10, y + 200))
                        booster_rects.append((booster, rect))
                        y += CELL_SIZE + 10
                    clicked_booster = None
                    for booster, rect in booster_rects:
                        if rect.collidepoint(x_click, y_click):
                            clicked_booster = booster
                            break
                    if clicked_booster:
                        selected_booster = clicked_booster
                    else:
                        col = x_click // CELL_SIZE
                        row = y_click // CELL_SIZE
                        if selected_booster:
                            use_booster(board, selected_booster, (row, col))
                            selected_booster = None
                            check_achievements()
                        else:
                            if selected:
                                if is_valid_move(selected, (row, col)):
                                    current_moves += 1
                                    swap_cells(board, selected, (row, col))
                                    matches = find_matches(board)
                                    if not matches:
                                        swap_cells(board, (row, col), selected)
                                        current_moves -= 1
                                    else:
                                        while True:
                                            matches = find_matches(board)
                                            if not matches: break
                                            update_progress(matches)
                                            fade_out_animation(board, matches)
                                            remove_matches(board, matches)
                                            movements, new_cells = drop_elements(board)
                                            animate_drop(movements)
                                            fade_in_animation(board, new_cells)
                                    selected = None
                                else:
                                    selected = (row, col)
                            else:
                                selected = (row, col)
            if check_goals():
                records[f"level_{current_level}"]["best_score"] = max(records[f"level_{current_level}"]["best_score"], score)
                save_records(records)
                state = "goal_reached"
            elif current_moves >= max_moves:
                state = "game_over"
            elif not has_moves(board):
                state = "game_over"
            pygame.display.flip()
        elif state == "game_over":
            result = game_over_screen()
            if result == "menu": 
                state = "menu"
            elif result == "exit": 
                running = False
        elif state == "goal_reached":
            result = goal_reached_screen()
            if result == "menu": 
                state = "menu"
            elif result == "exit": 
                running = False
    pygame.quit()

if __name__ == "__main__":
    main()