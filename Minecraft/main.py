import pygame
import sys
import time
import random
import pickle
from pygame import mixer
import time

# constants
WIDTH, HEIGHT = 1000, 800
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SKY_BLUE = (135, 206, 235)
MAX_FALL_DISTANCE = 1000
BLOCK_HEALTH = 100
DAY_COLOR = (135, 206, 235)  
NIGHT_COLOR = (20, 20, 50)    
is_day = True  

HOTBAR_SLOTS = 9  
SLOT_SIZE = 40    
HOTBAR_WIDTH = HOTBAR_SLOTS * SLOT_SIZE
HOTBAR_HEIGHT = SLOT_SIZE
HOTBAR_MARGIN = 10  
SELECTED_COLOR = (255, 255, 0)  

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("FatalCraft")

mixer.init()
font = pygame.font.SysFont('Arial', 20)
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-5, -1)
        self.lifetime = random.randint(20, 40)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.lifetime -= 1
        return self.lifetime > 0
        
    def draw(self, screen, camera):
        pygame.draw.circle(screen, self.color, 
                         (int(self.x - camera.camera.x), int(self.y - camera.camera.y)), 
                         self.size)

class World:
    def __init__(self):
        self.blocks = []
        self.chunks = {}  
        self.particles = []
        
    def add_block(self, block):
        self.blocks.append(block)
        chunk_x = block.rect.x // (16*50)  
        chunk_y = block.rect.y // (16*50)
        if (chunk_x, chunk_y) not in self.chunks:
            self.chunks[(chunk_x, chunk_y)] = []
        self.chunks[(chunk_x, chunk_y)].append(block)
        
    def get_nearby_blocks(self, position, radius):
        nearby = []
        chunk_radius = radius // (16*50) + 1
        center_chunk_x = position[0] // (16*50)
        center_chunk_y = position[1] // (16*50)
        
        for x in range(center_chunk_x - chunk_radius, center_chunk_x + chunk_radius + 1):
            for y in range(center_chunk_y - chunk_radius, center_chunk_y + chunk_radius + 1):
                if (x, y) in self.chunks:
                    nearby.extend(self.chunks[(x, y)])
        return nearby
    
    def add_particles(self, particles):
        self.particles.extend(particles)
    
    def update_particles(self):
        self.particles = [p for p in self.particles if p.update()]
    
    def draw_particles(self, screen, camera):
        for particle in self.particles:
            particle.draw(screen, camera)
    
    def save(self, filename="world.dat"):
        with open(filename, 'wb') as f:
            pickle.dump([(block.x, block.y, block.__class__.__name__) for block in self.blocks], f)
    
    def load(self, filename="world.dat"):
        try:
            with open(filename, 'rb') as f:
                blocks_data = pickle.load(f)
                self.blocks = []
                self.chunks = {}
                for x, y, block_type in blocks_data:
                    if block_type == "Grassblock":
                        self.add_block(Grassblock(x, y))
                    elif block_type == "Dirtblock":
                        self.add_block(Dirtblock(x, y))
                    elif block_type == "Stoneblock":
                        self.add_block(Stoneblock(x, y))
                    elif block_type == "Wood":
                        self.add_block(Wood(x, y))
                    elif block_type == "Leaves":
                        self.add_block(Leaves(x, y))
                    elif block_type == "IronOre":
                        self.add_block(IronOre(x, y))
                    elif block_type == "Coal":
                        self.add_block(Coal(x, y))
                    elif block_type == "Diamond":
                        self.add_block(Diamond(x, y))

        except FileNotFoundError:
            print("No saved world found - generating new one")
            self.generate_world()
    
    def generate_world(self):
        bedrock_depth = HEIGHT + (50 * 50)
        for x in range(-WIDTH, WIDTH*20, 50):
            self.add_block(Bedrock(x, bedrock_depth))

        for x in range(-WIDTH, WIDTH*20, 50):
            self.add_block(Grassblock(x, HEIGHT - 50))
            self.add_block(Dirtblock(x, HEIGHT))
            self.add_block(Dirtblock(x, HEIGHT + 50))

            for y in range(HEIGHT + 100, HEIGHT + (50 * 50), 50):
                depth = y - HEIGHT  
                
                if random.random() < 0.05:  
                    if depth > 800 and random.random() < 0.3:
                        self.add_block(Diamond(x, y))
                    elif depth > 500 and random.random() < 0.5: 
                        self.add_block(IronOre(x, y))
                    else: 
                        self.add_block(Coal(x, y))
                else:
                    self.add_block(Stoneblock(x, y))
            
            if x % 200 == 0 and random.random() < 0.35:
                is_surface = True
                for block in self.blocks:
                    if block.rect.x == x and block.rect.y == HEIGHT - 50 and isinstance(block, Grassblock):
                        self.generate_tree(x, HEIGHT - 100)
                        break

        
    def generate_tree(self, x, y):
        
        tree = Tree(x, y, self)
        tree.generate()

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
    
    def apply(self, entity):
        return entity.rect.move(-self.camera.x, -self.camera.y)
    
    def update(self, target):
        x = target.rect.centerx - self.width // 2
        y = target.rect.centery - self.height // 2
        self.camera = pygame.Rect(x, y, self.width, self.height)

class Block:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 50, 50)
        self.image = self.load_img()

    def draw_health_bar(self, screen, camera):
        if self.health < self.max_health:
            bar_width = 50
            health_pct = self.health / self.max_health
            bar_x = self.rect.x - camera.camera.x
            bar_y = self.rect.y - camera.camera.y - 10

            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, 5))

            health_width = int(bar_width * health_pct)
            health_color = (0, 255, 0) if health_pct > 0.6 else (255, 255, 0) if health_pct > 0.3 else (255, 0, 0)
            pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, 5))
            
    def draw(self, screen, camera):
        screen.blit(self.image, (self.rect.x - camera.camera.x, self.rect.y - camera.camera.y))

class Grassblock(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 50
    
    def load_img(self):
        try:
            grass_block = pygame.image.load("textures/grass.png").convert_alpha()
            return pygame.transform.scale(grass_block, (50, 50))
        except pygame.error as er:
            print(f"Error loading grass block: {er}")
            placeholder = pygame.Surface((50, 50))
            placeholder.fill((0, 255, 0))  
            return placeholder

class Dirtblock(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 50
    def load_img(self):
        try:
            dirt_block = pygame.image.load("textures/dirt.png").convert_alpha()
            return pygame.transform.scale(dirt_block, (50, 50))
        except pygame.error as er:
            print(f"Error loading dirt block: {er}")
            placeholder = pygame.Surface((50, 50))
            placeholder.fill((139, 69, 19))  
            return placeholder

class Stoneblock(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 125
    def load_img(self):
        try:
            stone_block = pygame.image.load("textures/stone.png").convert_alpha()
            return pygame.transform.scale(stone_block, (50, 50))
        except pygame.error as er:
            print(f"Error loading stone block: {er}")
            placeholder = pygame.Surface((50, 50))
            placeholder.fill((128, 128, 128))  
            return placeholder

class IronOre(Block):
    def __init__(self,x, y):
        super().__init__(x, y)
        self.health = 150
    def load_img(self):
        try:
            iron = pygame.image.load("textures/iron.png").convert_alpha()
            return pygame.transform.scale(iron, (50, 50))
        except pygame.error as er:
            print(f"error loading iron block: {er}")
            placeholder = pygame.surface((50, 50))
            placeholder.fill((74, 75, 76))
            return placeholder
        
class Coal(Block):
    def __init__(self,x, y):
        super().__init__(x, y)
        self.health = 110
    def load_img(self):
        try:
            coal = pygame.image.load("textures/coal.png").convert_alpha()
            return pygame.transform.scale(coal, (50, 50))
        except pygame.error as er:
            print(f"error loading iron block: {er}")
            placeholder = pygame.surface((50, 50))
            placeholder.fill((54, 69, 79))
            return placeholder
        
class Diamond(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 150
    def load_img(self):
        try:
            diamond = pygame.image.load("textures/diamond.png").convert_alpha()
            return pygame.transform.scale(diamond, (50, 50))
        except pygame.error as er:
            print(f"error loading diamond: {er}")
            placeholder = pygame.surface((50, 50))
            placeholder.fill(SKY_BLUE)

class Bedrock(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = float('inf')
    def load_img(self):
        try:
            bedrock = pygame.image.load("textures/bedrock.png").convert_alpha()
            return pygame.transform.scale(bedrock, (50, 50))
        except pygame.error as er:
            print(f"error loading bedrock: {er}")
            placeholder = pygame.Surface((50, 50))
            placeholder.fill((0, 0, 0))
            return placeholder
class Wood(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 100
    
    def load_img(self):
        try:
            wood = pygame.image.load("textures/wood.png").convert_alpha()
            return pygame.transform.scale(wood, (50, 50))
        except pygame.error as er:
            print(f"Error loading wood block: {er}")
            placeholder = pygame.Surface((50, 50))
            placeholder.fill((161, 102, 47))
            return placeholder

class Leaves(Block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 5
    
    def load_img(self):
        try:
            leaf = pygame.image.load("textures/leaves.png").convert_alpha()
            return pygame.transform.scale(leaf, (50, 50))
        except pygame.error as er:
            print(f"Error loading leaf block: {er}")
            placeholder = pygame.Surface((50, 50))
            placeholder.fill((74, 124, 89))
            return placeholder
class Tree:
    def __init__(self, x, y, world):
        self.x = x
        self.y = y
        self.world = world
        self.height = random.randint(4, 7)
        self.height = random.randint(4, 7)
        if random.random() < 0.2:
            self.height += random.randint(1, 2) 
        
    def generate(self):
        for i in range(self.height):
            self.world.add_block(Wood(self.x, self.y - (i * 50)))

        leaves_width = 3  
        leaves_start = 1  
        
        for layer in range(leaves_start, self.height - 1): 
            y_pos = self.y - (layer * 50)

            for i in range(-(leaves_width//2), (leaves_width//2) + 1):
                if random.random() > 0.2:  
                    self.world.add_block(Leaves(self.x + (i * 50), y_pos))

        top_y = self.y - ((self.height - 1) * 50)
        for i in range(-1, 2):
            self.world.add_block(Leaves(self.x + (i * 50), top_y))

        if random.random() > 0.7:
            self.world.add_block(Leaves(self.x, top_y - 50))


class Player:
    def __init__(self):
        self.world_pos = [500, HEIGHT - 200]
        self.original_image = self.load_img()
        self.image = self.original_image 
        self.jump_power = -20
        self.can_jump = True
        self.gravity = 0
        self.rect = pygame.Rect(self.world_pos[0], self.world_pos[1], 50, 150)
        self.on_ground = False
        self.speed = 5
        self.facing_right = True
        self.health = 10
        self.max_health = 10
        self.damage_frames = 0
        self.damage_delay = 30
        self.selected_slot = 0
        self.inventory = {i: {"type": None, "count": 0} for i in range(9)}
        self.mining_block = None
        self.mining_progress = 0
        self.mining_speed = 1  
        self.max_mine_distance = 250
        self.max_safe_fall = 25 
        self.fall_damage = 0  
                
    def load_img(self): 
        try:
            steve_img = pygame.image.load("textures/steve.png").convert_alpha()
            return pygame.transform.scale(steve_img, (50, 150))  
        except pygame.error as e:
            print(f"Error loading image: {e}")
            placeholder = pygame.Surface((50, 150))
            placeholder.fill((255, 0, 0))  
            return placeholder
    def update(self, ground_blocks):
        self.world_pos[1] += self.gravity
        self.gravity += 0.8

        self.on_ground = False
        self.rect.x = self.world_pos[0]
        self.rect.y = self.world_pos[1]

        for block in ground_blocks:
            if self.rect.colliderect(block.rect) and self.gravity >= 0 and self.rect.bottom > block.rect.top:
                if self.gravity > self.max_safe_fall:
                    self.health -= (self.gravity - self.max_safe_fall) * 0.2
                self.on_ground = True
                self.can_jump = True  
                self.gravity = 0
                self.rect.bottom = block.rect.top
                self.world_pos[1] = self.rect.y  
                break
            elif self.gravity < 0 and self.rect.top < block.rect.bottom and self.rect.colliderect(block.rect):
                self.gravity = 0
                self.rect.top = block.rect.bottom
                self.world_pos[1] = self.rect.y  
                break
player = Player()

class Zombie:
    def __init__(self):
        self.world_pos = [random.randint(1, 999), HEIGHT - 200]
        self.original_img = self.load_img()
        self.image = self.original_img
        self.gravity = 0
        self.rect = pygame.Rect(self.world_pos[0], self.world_pos[1], 50, 150)
        self.speed = 1.5
        self.health = 10
        self.max_health = 10
        self.max_safe_fall = 25
        self.damage = 0.01
        self.attack_cooldown = 0
        self.attack_delay = 1000 
        self.facing_right = True 
        self.knockback = 0 
        self.knockback_resistance = 0.8  
        self.knockback_direction = 1

    def load_img(self):
        try:
            zombie_img = pygame.image.load("textures/zombie.png").convert_alpha()
            return pygame.transform.scale(zombie_img, (50, 150))
        except pygame.error as er:
            print(f"Error loading image: {er}")
            placeholder = pygame.Surface((50, 150))
            placeholder.fill((0, 255, 0))  
            return placeholder
    def update(self, ground_blocks):
        self.world_pos[1] += self.gravity
        self.gravity += 0.8
        self.on_ground = False
        self.rect.x = self.world_pos[0]
        self.rect.y = self.world_pos[1]
        player_pos = player.world_pos
        if self.knockback > 0:
            self.world_pos[0] += self.knockback_direction * self.knockback
            self.knockback *= self.knockback_resistance  
            if self.knockback < 0.5:  
                self.knockback = 0

        if self.knockback <= 0:
            if self.world_pos[0] < player_pos[0]:  
                if not self.facing_right:
                    self.facing_right = True
                    self.image = self.original_img  
                self.world_pos[0] += self.speed
            else:  
                if self.facing_right:
                    self.facing_right = False
                    self.image = pygame.transform.flip(self.original_img, True, False)        
            if self.world_pos[0] < player_pos[0]:
                self.world_pos[0] += self.speed
            else:
                self.world_pos[0] -= self.speed
            if self.attack_cooldown > 0:
                self.attack_cooldown -= 1
            if self.rect.colliderect(player.rect):
                player.health -= self.damage
                self.attack_cooldown = self.attack_delay
                if self.world_pos[0] < player_pos[0]:
                    self.world_pos[0] += self.speed
                else:
                    self.world_pos[0] -= self.speed

        for block in ground_blocks:
            if self.rect.colliderect(block.rect) and self.gravity >= 0 and self.rect.bottom > block.rect.top:
                if self.gravity > self.max_safe_fall:
                    self.health -= (self.gravity - self.max_safe_fall) * 0.2
                self.on_ground = True
                self.can_jump = True  
                self.gravity = 0
                self.rect.bottom = block.rect.top
                self.world_pos[1] = self.rect.y  
                break
            elif self.gravity < 0 and self.rect.top < block.rect.bottom and self.rect.colliderect(block.rect):
                self.gravity = 0
                self.rect.top = block.rect.bottom
                self.world_pos[1] = self.rect.y  
                break
    
    def take_damage(self, amount):
        self.health -= amount
        self.knockback_direction = 1 if player.world_pos[1] < self.rect.x else -1
        self.knockback = 15  
        self.hit_cooldown = 10
        return self.health <= 0 

def draw_hotbar(screen, player):
    hotbar_x = (WIDTH - HOTBAR_WIDTH) // 2
    hotbar_y = HEIGHT - HOTBAR_HEIGHT - HOTBAR_MARGIN
    
    pygame.draw.rect(screen, (50, 50, 50), 
                    (hotbar_x - 2, hotbar_y - 2, 
                     HOTBAR_WIDTH + 4, HOTBAR_HEIGHT + 4))
    pygame.draw.rect(screen, (150, 150, 150), 
                    (hotbar_x, hotbar_y, HOTBAR_WIDTH, HOTBAR_HEIGHT))
    
    for slot in range(HOTBAR_SLOTS):
        slot_x = hotbar_x + slot * SLOT_SIZE
        slot_rect = pygame.Rect(slot_x, hotbar_y, SLOT_SIZE, SLOT_SIZE)
        
        pygame.draw.rect(screen, (100, 100, 100), slot_rect, 2)
        
        item = player.inventory[slot]
        if item["type"]:
            # Create a temporary block to get its image
            temp_block = None
            if item["type"] == "dirt":
                temp_block = Dirtblock(0, 0)
            elif item["type"] == "stone":
                temp_block = Stoneblock(0, 0)
            elif item["type"] == "grass":
                temp_block = Grassblock(0, 0)
            elif item["type"] == "wood":
                temp_block = Wood(0, 0)
            elif item["type"] == "leaves":
                temp_block = Leaves(0, 0)
            elif item["type"] == "ironore":
                temp_block = IronOre(0, 0)
            elif item["type"] == "coal":
                temp_block = Coal(0, 0)
            elif item["type"] == "diamond":
                temp_block = Diamond(0, 0)
            
            if temp_block:
                # Scale down the image to fit the slot
                scaled_img = pygame.transform.scale(temp_block.image, (SLOT_SIZE - 10, SLOT_SIZE - 10))
                screen.blit(scaled_img, (slot_x + 5, hotbar_y + 5))
            
            font = pygame.font.SysFont(None, 20)
            count_text = font.render(str(item["count"]), True, WHITE)
            screen.blit(count_text, (slot_x + SLOT_SIZE - 15, hotbar_y + SLOT_SIZE - 20))
    
    selection_x = hotbar_x + player.selected_slot * SLOT_SIZE
    pygame.draw.rect(screen, SELECTED_COLOR, 
                    (selection_x - 2, hotbar_y - 2, 
                     SLOT_SIZE + 4, SLOT_SIZE + 4), 2)

def draw_health_bar(screen, player):
    health_width = 200
    health_height = 20
    health_x = 320
    health_y = 725

    pygame.draw.rect(screen, (50, 50, 50), (health_x, health_y, health_width, health_height))
    health_level = max(0, (player.health / player.max_health) * health_width)
    pygame.draw.rect(screen, (255, 0, 0), (health_x, health_y, health_level, health_height))
    # border
    pygame.draw.rect(screen, WHITE, (health_x, health_y, health_width, health_height), 2)

    font = pygame.font.SysFont(None, 24)
    health_text = font.render(f"Health: {player.health:.1f}/{player.max_health}", True, WHITE)
    screen.blit(health_text, (health_x + health_height, health_y))
zombies = []  
last_spawn_time = 0
spawn_interval = 300  
max_zombies = 5 
world = World()
world.load()  
camera = Camera(WIDTH, HEIGHT)

try:
    mine_sound = mixer.Sound("sounds/mine.wav")
    place_sound = mixer.Sound("sounds/place.wav")
    jump_sound = mixer.Sound("sounds/jump.wav")
    hurt_sound = mixer.Sound("sounds/hurt.wav")
except:
    print("Could not load sounds")
    mine_sound = mixer.Sound(buffer=bytearray(100))
    place_sound = mixer.Sound(buffer=bytearray(100))
    jump_sound = mixer.Sound(buffer=bytearray(100))
    hurt_sound = mixer.Sound(buffer=bytearray(100))

running = True
clock = pygame.time.Clock()

while running:

    mouse_wheel_up = False
    mouse_wheel_down = False
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            world.save()
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w) and player.on_ground:
                player.gravity = player.jump_power
                player.on_ground = False
                player.can_jump = False
                jump_sound.play()
            
            if pygame.K_1 <= event.key <= pygame.K_9:
                player.selected_slot = event.key - pygame.K_1
            elif event.key == pygame.K_LEFTBRACKET:  
                player.selected_slot = (player.selected_slot - 1) % HOTBAR_SLOTS
            elif event.key == pygame.K_RIGHTBRACKET:  
                player.selected_slot = (player.selected_slot + 1) % HOTBAR_SLOTS
            
            if event.key == pygame.K_ESCAPE:
                world.save()
                running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            world_mouse_pos = (mouse_pos[0] + camera.camera.x,
                            mouse_pos[1] + camera.camera.y)
            
            for zombie in zombies[:]:
                if zombie.rect.collidepoint(world_mouse_pos):
                    if zombie.take_damage(1): 
                        zombies.remove(zombie)
                    break


    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player.world_pos[0] -= player.speed
        player.image = pygame.transform.flip(player.original_image, True, False)
        player.facing_right = False
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player.world_pos[0] += player.speed
        player.image = player.original_image
        player.facing_right = True

    # void damage
    if player.world_pos[1] > HEIGHT * 4:
        player.damage_frames += 1
        if player.damage_frames >= player.damage_delay:
            player.health -= 0.5
            player.damage_frames = 0
            hurt_sound.play()
    else:
        player.damage_frames = 0 
    
    if player.health <= 0:
        screen.fill(BLACK)
        font = pygame.font.SysFont(None, 72)
        text = font.render("GET WRECKED LOL", True, (255, 0, 0))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
        pygame.display.flip()
        time.sleep(2)
        running = False
    if pygame.time.get_ticks() % 1200000 < 600000: 
        is_day = True
    else:
        is_day = False
    current_time = pygame.time.get_ticks()

    if not is_day and current_time - last_spawn_time > spawn_interval and len(zombies) < max_zombies:
        zombies.append(Zombie())
        last_spawn_time = current_time

    if is_day and zombies:
        zombies.clear()
    
    
    # mining/placing blocks
    mouse_buttons = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    world_x = mouse_pos[0] + camera.camera.x
    world_y = mouse_pos[1] + camera.camera.y

    if mouse_buttons[0]:  
        for block in nearby_blocks[:]:
            if isinstance(block, Bedrock):
                continue
            block_rect = pygame.Rect(block.rect.x - camera.camera.x, 
                                    block.rect.y - camera.camera.y,
                                    block.rect.width, block.rect.height)
            
    if mouse_buttons[0]:  
        for block in nearby_blocks[:]:
            block_rect = pygame.Rect(block.rect.x - camera.camera.x, 
                                    block.rect.y - camera.camera.y,
                                    block.rect.width, block.rect.height)
            
            if block_rect.collidepoint(mouse_pos) and \
            pygame.math.Vector2(block.rect.center).distance_to(pygame.math.Vector2(player.rect.center)) <= player.max_mine_distance:

                if isinstance(block, Bedrock):
                    pygame.draw.rect(screen, (255, 0, 0), 
                                    (block_rect.x, block_rect.y - 10, 
                                    block_rect.width, 5))
                    break

                if block != player.mining_block:
                    player.mining_block = block
                    player.mining_progress = 0
                block_max_health = getattr(block, 'health', BLOCK_HEALTH)

                player.mining_progress += player.mining_speed
                progress_pct = min(player.mining_progress / block_max_health, 1.0)
                

                pygame.draw.rect(screen, (255, 255, 255), 
                                (block_rect.x, block_rect.y - 10, 
                                block_rect.width * progress_pct, 5))

                if player.mining_progress >= block_max_health:
                    item_type = None
                    if isinstance(block, Dirtblock):
                        item_type = "dirt"
                        color = (139, 69, 19)
                    elif isinstance(block, Stoneblock):
                        item_type = "stone"
                        color = (128, 128, 128)
                    elif isinstance(block, Grassblock):
                        item_type = "grass"
                        color = (0, 255, 0)
                    elif isinstance(block, Wood):
                        item_type = "wood"
                        color = (160, 82, 45)
                    elif isinstance(block, Leaves):
                        item_type = "leaves"
                        color = (0, 200, 0)
                    elif isinstance(block, IronOre):
                        item_type = "ironore"
                        color = (100, 100, 110)
                    elif isinstance(block, Coal):
                        item_type = "coal"
                        color = (54, 69, 79)
                    elif isinstance(block, Diamond):
                        item_type = "diamond"
                        color = SKY_BLUE

                    particles = [Particle(
                        block.rect.centerx + random.randint(-20, 20),
                        block.rect.centery + random.randint(-20, 20),
                        color
                    ) for _ in range(15)]
                    world.add_particles(particles)
                    
                    added = False
                    for slot in range(HOTBAR_SLOTS):
                        if player.inventory[slot]["type"] == item_type:
                            player.inventory[slot]["count"] += 1
                            added = True
                            break
                    
                    if not added:
                        for slot in range(HOTBAR_SLOTS):
                            if player.inventory[slot]["type"] is None:
                                player.inventory[slot]["type"] = item_type
                                player.inventory[slot]["count"] = 1
                                added = True
                                break
                    

                    world.blocks.remove(block)
                    chunk_x = block.rect.x // (16*50)
                    chunk_y = block.rect.y // (16*50)
                    if (chunk_x, chunk_y) in world.chunks:
                        world.chunks[(chunk_x, chunk_y)].remove(block)
                    
                    mine_sound.play()
                    player.mining_block = None
                    player.mining_progress = 0
                break
        else:
            player.mining_block = None
            player.mining_progress = 0
    if mouse_buttons[2]:
        selected_item = player.inventory[player.selected_slot]
        if selected_item["type"] and selected_item["count"] > 0:
            grid_x = (world_x // 50) * 50
            grid_y = (world_y // 50) * 50

            occupied = False
            temp_rect = pygame.Rect(grid_x, grid_y, 50, 50)
            for block in nearby_blocks:
                if block.rect.colliderect(temp_rect):
                    occupied = True
                    break

            has_support = False
            for dx, dy in [(0, 50), (0, -50), (50, 0), (-50, 0)]:
                temp_rect = pygame.Rect(grid_x + dx, grid_y + dy, 50, 50)
                for block in nearby_blocks:
                    if block.rect.colliderect(temp_rect):
                        has_support = True
                        break
                if has_support:
                    break

            if (not player.rect.colliderect(temp_rect) and not occupied and 
                (has_support or grid_y >= HEIGHT - 50)):
                if selected_item["type"] == "dirt":
                    world.add_block(Dirtblock(grid_x, grid_y))
                elif selected_item["type"] == "stone":
                    world.add_block(Stoneblock(grid_x, grid_y))
                elif selected_item["type"] == "grass":
                    world.add_block(Grassblock(grid_x, grid_y))
                elif selected_item["type"] == "wood":
                    world.add_block(Wood(grid_x, grid_y))   
                elif selected_item["type"] == "leaves":
                    world.add_block(Leaves(grid_x, grid_y))   
                elif selected_item["type"] == "ironore":
                    world.add_block(IronOre(grid_x, grid_y))                 
                elif selected_item["type"] == "coal":
                    world.add_block(Coal(grid_x, grid_y)) 
                elif selected_item["type"] == "diamond":
                    world.add_block(Diamond(grid_x, grid_y)) 

                selected_item["count"] -= 1
                if selected_item["count"] <= 0:
                    selected_item["type"] = None
                
                place_sound.play()
    nearby_blocks = world.get_nearby_blocks((player.rect.x, player.rect.y), 1000)
    player.update(nearby_blocks)
    camera.update(player)
    world.update_particles()

    screen.fill(DAY_COLOR if is_day else NIGHT_COLOR)

    for block in nearby_blocks:
        if (block.rect.right > camera.camera.left and 
            block.rect.left < camera.camera.right and
            block.rect.bottom > camera.camera.top and
            block.rect.top < camera.camera.bottom):
            block.draw(screen, camera)

    world.draw_particles(screen, camera)

    screen.blit(
        player.image,
        (player.rect.x - camera.camera.x, player.rect.y - camera.camera.y)
    )
    for zombie in zombies:
        zombie.update(nearby_blocks)
        screen.blit(zombie.image, (zombie.rect.x - camera.camera.x, zombie.rect.y - camera.camera.y))
        
    draw_hotbar(screen, player)
    draw_health_bar(screen, player)

    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (255, 0, 0))
    screen.blit(fps_text, (10, 10))
    
    if player.mining_block:
        block_rect = pygame.Rect(
            player.mining_block.rect.x - camera.camera.x,
            player.mining_block.rect.y - camera.camera.y,
            player.mining_block.rect.width,
            player.mining_block.rect.height
        )
        progress_pct = min(player.mining_progress / BLOCK_HEALTH, 1.0)
        pygame.draw.rect(screen, (255, 255, 255), 
                        (block_rect.x, block_rect.y - 10, 
                         block_rect.width * progress_pct, 5))
    
    pygame.display.flip()
    clock.tick(60)

sys.exit(0)
