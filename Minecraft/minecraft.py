import pygame
import sys

# Constants
WIDTH, HEIGHT = 1000, 800
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Yearn for the Mines")

class Grassblock:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = self.load_img()
        self.rect = pygame.Rect(x, y, 50, 50)

    def load_img(self):
        try:
            grass_block = pygame.image.load("textures/grass.png").convert_alpha()
            grass_block = pygame.transform.scale(grass_block, (50, 50))

            return grass_block
        
        except pygame.error as er:
            print(f"Error. Couldn't load grass block. some random error: {er}")
            placeholder = pygame.Surface((50, 50))
            placeholder.fill((0, 255, 0))  
            return placeholder
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))


class Player:
    def __init__(self):
        self.pos = [500, 400]
        self.original_image = self.load_img()
        self.jump_power = -20 
        self.image = self.original_image 
        self.gravity = 0
        self.rect = pygame.Rect(500, 400, 50, 150)
        self.on_ground = False
        self.speed = 5
    
    def load_img(self): 

        try:
            steve_img = pygame.image.load("textures/steve.png").convert_alpha()
            steve_img = pygame.transform.scale(steve_img, (50, 150))  
            return steve_img
        except pygame.error as e:
            print(f"Error loading image: {e}")
           
            placeholder = pygame.Surface((50, 150))
            placeholder.fill((255, 0, 0))  
            return placeholder
    def update(self, ground_blocks):
        self.rect.x = self.pos[0] 
        self.rect.y = self.pos[1]
        
        self.pos[1] += self.gravity
        self.gravity += 1

        on_ground = False
        for block in ground_blocks:
            if self.rect.colliderect(block.rect):

                if self.gravity > 0 and self.rect.bottom > block.rect.top:
                    self.pos[1] = block.rect.top - self.rect.height
                    self.rect.bottom = block.rect.top
                    self.gravity = 0
                    on_ground = True

                elif self.gravity < 0 and self.rect.top < block.rect.bottom:
                    self.pos[1] = block.rect.bottom
                    self.rect.top = block.rect.bottom
                    self.gravity = 0
                

        if not on_ground and self.gravity == 0:
            self.gravity = 0.8
 
player = Player() 

ground_blocks = []
for x in range(0, WIDTH, 50):
    for y in range(HEIGHT - 100, HEIGHT, 50):
        ground_blocks.append(Grassblock(x, y))

running = True
clock = pygame.time.Clock()  

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.gravity = player.jump_power
        
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.pos[0] -= player.speed
        player.image = pygame.transform.flip(player.original_image, True, False)

    if keys[pygame.K_RIGHT]:
        player.pos[0] += player.speed
        player.image = player.original_image

    player.update(ground_blocks)
    screen.fill(BLACK)
    
    screen.blit(player.image, player.pos)
    

    for block in ground_blocks:
        block.draw(screen)
    
    pygame.display.flip()
    clock.tick(70)  

pygame.quit()
sys.exit()