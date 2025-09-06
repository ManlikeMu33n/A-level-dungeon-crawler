import pygame
from sys import exit
from random import choice
import pygame_gui
import pygame_gui.ui_manager
from SaveLoadManager import SaveLoadSystem
from shopbase import ShopDatabase



pygame.init()
pygame.mixer.init()



all_enemies = pygame.sprite.Group() 
difficulty_multiplier = 2   
projectiles = pygame.sprite.Group()  
obstacles = pygame.sprite.Group()      
coins = []  # holds positions of killed enemies to make a coin in their place
coin_sound_effect  = pygame.mixer.Sound("coin_pickup_sound.ogg")
money = 0



black = (0, 0, 0)
white = (255, 255, 255)
blue = (0, 0, 255)
green = (0, 255, 0)
red = (255, 0, 0)
orange = (255, 165, 0)
yellow = (255, 255, 0)
silver = (192, 192, 192)
grey = (128, 128, 128)
pink = (255, 192, 203)


screen_width = 1000
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
screen_colour = white

pygame.display.set_caption("[Insert Name]")

class Room:
    def __init__(self, width, height, background, name = str, is_save_room=False):
        self.width = width
        self.height = height
        self.background = background
        self.name = name
        self.is_save_room = is_save_room
        self.enemies = [] if not is_save_room else []  # save room has no enemies: value if condition else value

    def spawn_enemies(self):
        for enemy in self.enemies:
            enemy.draw(camera)  # Draw them on the screen

    def add_enemy(self, enemy):
        self.enemies.append(enemy)

    def to_dict(self):      # Convert the room to a dictionary for saving as pygame.surface is not serializable
        return {
            "width": self.width,
            "height": self.height,
            "background_color": self.background,  # Save the color instead of the Surface
            "name": self.name,
            "is_save_room": self.is_save_room,
            "enemies": [
                {
                    "x": enemy.rect.x,
                    "y": enemy.rect.y,
                    "health": enemy.health,
                    "room_pos": getattr(enemy, "room_pos", None),  # For ChasingEnemy
                }
                for enemy in self.enemies
            ],
        }
    
    @staticmethod
    def from_dict(data):  # Convert the dictionary back to a Room object
        room = Room(
            data["width"],
            data["height"],
            data["background_color"],  # Restore the color
            data["name"],
            data["is_save_room"],
        )
        for enemy_data in data["enemies"]:
            if enemy_data["room_pos"] is not None:
                enemy = ChasingEnemy(
                    enemy_data["x"], enemy_data["y"], enemy_data["room_pos"]
                )
            else:
                enemy = Enemy(enemy_data["x"], enemy_data["y"])
            enemy.health = enemy_data["health"]
            room.add_enemy(enemy)
        return room


# Initial save room
Firstroom = Room(1100, 900, white, "Saferoom", is_save_room = True)

savelist = [Firstroom]
pointer = 0
current_room = savelist[pointer]
last_save_room = 0



class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        try:
            return entity.rect.move(self.camera.topleft)
        except:
            return camera.apply_position(entity)

    def apply_position(self, pos):
        """Apply camera offset to the given start position."""
        adjusted_x = pos[0] + self.camera.x
        adjusted_y = pos[1] + self.camera.y
        return (adjusted_x, adjusted_y)
    


    def update(self, target, room_width, room_height):
        # Center the camera on the player
        x = -target.rect.centerx + screen_width // 2
        y = -target.rect.centery + screen_height // 2

        # Keep the camera within the bounds of the room
        x = min(0, max(-(room_width - screen_width), x))
        y = min(0, max(-(room_height - screen_height), y))

        # Update the camera rect
        self.camera = pygame.Rect(x, y, self.width, self.height)

camera = Camera(3000, 2600)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, room_pos, width=30, height=30, color=red, health=100, max_health = 100, speed=10, strength = 5, inventory_space = 5):
        super().__init__()
        self.surface = pygame.Surface((width, height))
        self.surface.fill(color)
        self.rect = self.surface.get_rect(topleft=(x, y))
        self.health = health
        self.__max_health = max_health
        self.speed = speed
        self.strength = strength
        self.inventory_space = inventory_space
        self.room_pos = room_pos

    # Getter for max_health
    def get_max_health(self):
        return self.__max_health

    # Setter for max_health
    def set_max_health(self, value):
        if value > 0:  # Ensure max_health is always positive
            self.__max_health = value
        else:
            raise ValueError("max_health must be greater than 0")



    def move(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.rect.top > limit_up:
            self.rect.y -= self.speed
        if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.rect.bottom < limit_down:
            self.rect.y += self.speed
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.rect.left > limit_left:
            self.rect.x -= self.speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.rect.right < limit_right:
            self.rect.x += self.speed

    def respawn(self):
   
        self.health = self.get_max_health() 

        while current_room.is_save_room == False:   # They wont respawn at the latest save room they accessed unless they save the game  
            pastroom()

        self.rect.x = 20  
        self.rect.y = screen_height // 2 


    def draw(self):
        screen.blit(self.surface, camera.apply(self))

    def draw_health_bar(self):
        bar_width = self.get_max_health()
        bar_height = 20
        bar_x = 10
        bar_y = 10

        health_ratio = self.health / self.get_max_health()
        current_bar_width = int(bar_width * health_ratio)

        pygame.draw.rect(screen, (128, 128, 128), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, current_bar_width, bar_height))
        pygame.draw.rect(screen, black, (bar_x, bar_y, bar_width, bar_height), 2)

    
    def draw_inventory(self):
        inventory_x = 10  # Starting x position for inventory
        inventory_y = 40  # below the health bar
        box_width = 50     # Width of inventory box
        box_height = 50    # Height of inventory box
        spacing = 20       # Space between boxes
        font = pygame.font.Font(None, 30)

        for i in range(self.inventory_space):
            box_x = inventory_x + (box_width + spacing) * i
            pygame.draw.rect(screen, (128, 128, 128), (box_x, inventory_y, box_width, box_height))
            pygame.draw.rect(screen, black, (box_x, inventory_y, box_width, box_height), 2)  # border
            screen.blit(font.render(f"{i+1}", False, black), (box_x, inventory_y))


    def attack(self, target_pos):
        projectile = Projectile(self.rect.center, target_pos)
        projectiles.add(projectile)





class Projectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.surface = pygame.Surface((10, 10))
        self.surface.fill((128, 0, 128))  # Purple
        self.rect = self.surface.get_rect(center = start_pos)
        
        self.direction = pygame.math.Vector2(target_pos) - pygame.math.Vector2(camera.apply(start_pos))
        
        try:
            self.direction = self.direction.normalize() * 20 # Set speed
        except:
            self.direction = (pygame.math.Vector2(1,1)).normalize() * 20

    def update(self):
        self.rect.move_ip(self.direction)

        if not (0 < self.rect.x < current_room.width and 0 < self.rect.y < current_room.height):
            self.kill()  # Remove if it goes out of bounds of the room its in

class Zone(pygame.sprite.Sprite):
    def __init__(self, x, y, width=10, height=100):
        super().__init__()
        self.surface = pygame.Surface((width, height))
        self.rect = self.surface.get_rect(topleft=(x, y))

    def draw(self):
        screen.blit(self.surface, camera.apply(self))

player = Player(20, screen_height // 2, 0)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, health=100, width = 30, height = 30, speed = 8, color=black, strength = 10):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.base_health = health
        self.speed = speed
        self.health = health
        self.strength = strength

    def scale_stats(self, room_number):
        # Scale health and speed based on the room number
        self.health = self.base_health + 10 * room_number  # +10 health per room
        self.strength += 1 * room_number  #  +1 dmg wper room


    def draw(self, camera):
        screen.blit(self.image, camera.apply(self))

    def follow(self, obstacles, enemies_in_room):
        old_x, old_y = self.rect.x, self.rect.y
        dx = self.speed if player.rect.x > self.rect.x else -self.speed if player.rect.x < self.rect.x else 0
        dy = self.speed if player.rect.y > self.rect.y else -self.speed if player.rect.y < self.rect.y else 0

        self.rect.x += dx
        if pygame.sprite.spritecollideany(self, obstacles) or any(e for e in enemies_in_room if e != self and self.rect.colliderect(e.rect)):
            self.rect.x = old_x

        self.rect.y += dy
        if pygame.sprite.spritecollideany(self, obstacles) or any(e for e in enemies_in_room if e != self and self.rect.colliderect(e.rect)):
            self.rect.y = old_y

        # Check for collision with player only if the enemy is near
        if self.rect.colliderect(player.rect):
            player.health -= self.strength / 60  # Apply damage only if colliding



class ChasingEnemy(Enemy):
    def __init__(self, x, y, room_pos, health=100, width=30, height=30, speed=4, color=pink, strength=5):
        super().__init__(x, y, health, width, height, speed, color, strength)  # Adjust speed and strength
        self.room_pos = room_pos

    def follow(self, obstacles, enemies_in_room):
        if self.room_pos == player.room_pos:
            # Follow the player normally
            
            old_x, old_y = self.rect.x, self.rect.y
            dx = self.speed if player.rect.x > self.rect.x else -self.speed if player.rect.x < self.rect.x else 0
            dy = self.speed if player.rect.y > self.rect.y else -self.speed if player.rect.y < self.rect.y else 0

            self.rect.x += dx
            if pygame.sprite.spritecollideany(self, obstacles) or any(e for e in enemies_in_room if e != self and self.rect.colliderect(e.rect)):
                self.rect.x = old_x

            self.rect.y += dy
            if pygame.sprite.spritecollideany(self, obstacles) or any(e for e in enemies_in_room if e != self and self.rect.colliderect(e.rect)):
                self.rect.y = old_y

            # Damage player on collision
            if self.rect.colliderect(player.rect):
                player.health -= self.strength  # Adjust damage application

        elif self.room_pos < player.room_pos:
            # Move towards the next room
            if self.rect.x < (savelist[self.room_pos].width - self.rect.width):
                self.rect.x += self.speed
            elif self.rect.y < zone2.rect.y:
                self.rect.y += self.speed
            else:
                self.transfer_enemy(savelist[self.room_pos], savelist[self.room_pos + 1])
                self.room_pos += 1  # Increment room position after transfer


        elif self.room_pos > player.room_pos:
            # Move towards the previous room
            if self.rect.x > (zone1.rect.x + zone1.rect.width):
                self.rect.x -= self.speed
            elif self.rect.y < zone1.rect.y:
                self.rect.y += self.speed
            else:
                self.transfer_enemy(savelist[self.room_pos], savelist[self.room_pos - 1])
                self.room_pos -= 1  # Decrement room position after transfer

    def transfer_enemy(self, from_room, to_room):
        # Remove the enemy from the current room
        if self in from_room.enemies:
            from_room.enemies.remove(self)
            all_enemies.remove(self)  # Remove from the global enemy group if needed
        
        # Add the enemy to the target room
        to_room.add_enemy(self)
        self.room_pos = savelist.index(to_room)  # Update the room position of the enemy





limit_up = 0
limit_down = Firstroom.height - player.rect.y
limit_left = 0
limit_right = Firstroom.width - player.rect.x

zone1 = Zone(0, screen_height // 2)
zone2 = Zone(current_room.width - 20, screen_height // 2)

obstacles.add(zone1, zone2)

def create_new_room():
    global savelist, limit_right, limit_down, last_save_room
    width = choice([1100, 1500, 2000])
    height = choice([900, 1200, 1600])
    background = choice([green, blue, yellow, orange])
    new_room_name = f"Room {len(savelist) + 1}"

    is_save_room = (len(savelist)) % 5 == 0
    
    new_room = Room(width, height, background, new_room_name, is_save_room)
    
    if not is_save_room:  # Only add enemies if it's not a save room
        num_enemies = choice([1, 2, 3])
        for i in range(num_enemies):
            enemy_x = choice(range(100, width - 100))
            enemy_y = choice(range(100, height - 100))

            # Spawn ChasingEnemy only if the room number is beyond 10
            #if len(savelist) > 10 and choice([True, False]):  # Randomly choose enemy type
            #    new_enemy = ChasingEnemy(enemy_x, enemy_y, pointer)
    
            #else:a
            new_enemy = Enemy(enemy_x, enemy_y)  # Regular enemy

            new_enemy.scale_stats(len(savelist))
            new_room.add_enemy(new_enemy)
            all_enemies.add(new_enemy)
    else:
        last_save_room = pointer
        
    return new_room



def nextroom():
    global pointer, screen_colour, current_room, camera, limit_right, limit_down, coins
    # Check for ChasingEnemies before moving to the next room
    enemies_to_transfer = [enemy for enemy in current_room.enemies if isinstance(enemy, ChasingEnemy)]

    if pointer < len(savelist) - 1:
        pointer += 1
    else:
        new_room = create_new_room()
        savelist.append(new_room)
        pointer = len(savelist) - 1
        coins.append([])
        
    current_room = savelist[pointer]
    player.rect.x = 20
    player.rect.y = screen_height // 2
    limit_right = current_room.width
    limit_down = current_room.height
    zone2.rect.x = current_room.width - 20
    screen_colour = current_room.background


    # Transfer ChasingEnemies to the new room
    for enemy in enemies_to_transfer:
        enemy.transfer_enemy(current_room, current_room)  # Use the transfer method to move to the new room

    current_room.spawn_enemies()

def pastroom():
    global pointer, screen_colour, current_room, camera, limit_right, limit_down

    if pointer > 0:
        pointer -= 1


    current_room = savelist[pointer]
    player.rect.x = current_room.width - player.rect.width - 30
    player.rect.y = screen_height // 2

    limit_right = current_room.width
    limit_down = current_room.height
    zone2.rect.x = current_room.width - 20
    screen_colour = current_room.background
    current_room.spawn_enemies()

background = pygame.Surface((screen_width, screen_height))
background.fill(grey)
manager = pygame_gui.UIManager((screen_width, screen_height))

open_menu = pygame_gui.elements.UIButton(relative_rect = pygame.Rect((screen_width - 100, 0), (100, 50)),
                                                text = 'Menu',
                                                manager = manager)

close_skills_menu = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((screen_width - 100, 0), (100, 50)),
                                                  text = 'Exit',
                                                  manager = manager)
close_skills_menu.hide()

# Save Button
save_button = pygame_gui.elements.UIButton(relative_rect = pygame.Rect((10, 100), (100, 50)),
                                            text = 'Save',
                                            manager = manager)
save_button.hide()  # Initially hide the save button




pause = False

skill_points = 0
font = pygame.font.Font(None, 20)




class skill_tree:
    def __init__(self, manager):
        self.manager = manager
        self.skills = {   # name: data, status
            "strength": {"pos": (300, 50)},
            "speed": {"pos": (500, 50)}, 
            "health": {"pos": (700, 50)},
        }


        self.buttons = {}
        self.create_skill_buttons()

    def create_skill_buttons(self):
        for name, data in self.skills.items():
            button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(data["pos"], (100, 50)),
                                                   text=name,
                                                   manager=self.manager)
            self.buttons[name] = button

    def visibility(self):
        if skilltree_button_pressed:
            for name, button in self.buttons.items():
                button.show()
        else:
            for name, button in self.buttons.items():
                button.hide()



skill_screen = skill_tree(manager)
skilltree_button_pressed = False



shop_on = False
shop_background = pygame.Surface((screen_width, screen_height//2))
shop_background.fill(grey)
shop_buttons = []
shopkeeper_image = pygame.image.load("paintsprite.png").convert()
shopkeeper_rect = shopkeeper_image.get_rect(center = (current_room.width // 2, 50))
open_shop_button = pygame_gui.elements.UIButton(relative_rect = pygame.Rect((screen_width // 2 , 0), (100, 50)),
                                                   text = "Shop",
                                                   manager = manager)
close_shop_button = pygame_gui.elements.UIButton(relative_rect = pygame.Rect((screen_width // 2 , 0), (100, 50)),
                                                   text = "Close",
                                                   manager = manager)

open_shop_button.hide()
close_shop_button.hide()


db = ShopDatabase("shop.db")
db.add_item('AOE blast', 10.0, "coin.png")
db.add_item('Sword', 15.0, "coin.png")
db.add_item('Immunity shield', 50.0, "coin.png")


def open_shop(db):
    global shop_buttons  # Keep track of buttons for cleanup

    # Clear any existing buttons
    
    shop_buttons = []  # Reset the list of buttons

    # Code to display the shop and interact with items
    items = db.fetch_items()  # Fetch items from the database

    for index, item in enumerate(items):
        item_id, name, cost = item

        # Print item details to the console


        # Create a button for each item
        button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((100 + index * 300, screen_height//2 + 50), (200, 50)),  # Position buttons with spacing
            text=f"{name} - Cost: {cost}",
            manager=manager
        )  

        shop_buttons.append((name, button, cost)) # Add button to the list for later reference and name and cost solid

    # Blit the shop background
    screen.blit(shop_background, (0, screen_height // 2))


coin_image = pygame.image.load("coin.png").convert()
coin_rect = coin_image.get_rect()




obstacles.add(zone1, zone2)

clock = pygame.time.Clock()


saveloadmanager = SaveLoadSystem(".save", "save_data")  # Save manager



(
    player_x, player_y, player_health, player_max_health, player_speed, player_strength, player_room_pos, player_inventory_space,
    pointer, last_save_room, money, skill_points, pause, skilltree_button_pressed, shop_on,
    coins
) = saveloadmanager.load_game_data(
    [
        "player_x", "player_y", "player_health", "player_max_health", "player_speed", "player_strength", "player_room_pos", "player_inventory_space",
        "pointer", "last_save_room", "money", "skill_points", "pause", "skilltree_button_pressed", "shop_on",
        "coins"
    ],
    [
        20, screen_height // 2, 100, 100, 10, 5, 0, 5,  # Default player data
        0, 0, 0, 0, False, False, False,  # Default game state
        [[]]  # Default room list and coins
    ]
)# [saved values to be loaded], [default values]

# Load room data
savelist_data = saveloadmanager.load_game_data(["savelist"], [[Firstroom.to_dict()]])
savelist = [Room.from_dict(room_data) for room_data in savelist_data]

# Restore player data
player.rect.x = player_x
player.rect.y = player_y
player.health = player_health
player.set_max_health(player_max_health)
player.speed = player_speed
player.strength = player_strength
player.room_pos = player_room_pos
player.inventory_space = player_inventory_space

# Restore game state
pointer = pointer
last_save_room = last_save_room
money = money
skill_points = skill_points
pause = pause
skilltree_button_pressed = skilltree_button_pressed
shop_on = shop_on

# Restore room data
savelist = savelist
current_room = savelist[pointer]

# Restore coins
coins = coins


while True:
    try:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                db.close()
                exit()


            if event.type == pygame_gui.UI_BUTTON_PRESSED: 
                if event.ui_element == open_menu:
                    pause = True
                    skilltree_button_pressed = True
                    open_menu.hide()
                    close_skills_menu.show()
                elif event.ui_element == close_skills_menu:
                    pause = False
                    skilltree_button_pressed = False
                    close_skills_menu.hide()
                    open_menu.show()



                elif event.ui_element == skill_screen.buttons["strength"]:
                    if skill_points >= 1:
                        player.strength += 1
                        skill_points -= 1
                elif event.ui_element == skill_screen.buttons["speed"]:
                    if skill_points >= 1:
                        player.speed += 0.2
                        skill_points -= 1
                elif event.ui_element == skill_screen.buttons["health"]:
                    if skill_points >= 1:
                        player.set_max_health(player.get_max_health() + 10)
                        player.health += 10
                        skill_points -= 1
    
                elif event.ui_element == open_shop_button:
                    open_shop(db)
                    pause = True
                    shop_on = True
                    skilltree_button_pressed = False
                    skill_screen.visibility()
                    open_shop_button.hide()
                    close_shop_button.show()

                elif event.ui_element == close_shop_button:
                    pause = False
                    shop_on = False
                    close_shop_button.hide()
                    for name, button, cost in shop_buttons:
                        button.hide()
                elif event.ui_element == save_button:
                    # Save player data
                    saveloadmanager.save_game_data(
                        [player.rect.x, player.rect.y, player.health, player.get_max_health(), player.speed, player.strength, player.room_pos, player.inventory_space],
                        ["player_x", "player_y", "player_health", "player_max_health", "player_speed", "player_strength", "player_room_pos", "player_inventory_space"]
                    )
                
                    # Save game state
                    saveloadmanager.save_game_data(
                        [pointer, last_save_room, money, skill_points, pause, skilltree_button_pressed, shop_on],
                        ["pointer", "last_save_room", "money", "skill_points", "pause", "skilltree_button_pressed", "shop_on"]
                    )
                
                    # Save room data
                    saveloadmanager.save_game_data(
                        [[room.to_dict() for room in savelist]],  # Convert each Room to a dictionary
                        ["savelist"]
                    )
                
                    # Save coins
                    saveloadmanager.save_game_data(
                        [coins],
                        ["coins"]
                    )
                
                    print("Game saved successfully!")
            
                for name, button, cost in shop_buttons:
                    if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == button:
                        if name == "AOE blast" and (money >= int(cost)):
                            money -= int(cost)
                            print(f"Bought {name}")

                        elif name == "Sword" and (money >= int(cost)):
                            money -= int(cost)   
                            print(f"Bought {name}")
                        
                        elif name == "Immunity shield" and (money >= int(cost)):
                            money -= int(cost)
                            print(f"Bought {name}")

                        else:
                            print("You brokie")

                    money_text = font.render("Coins: " + str(money), False, black)
                    screen.blit(money_text, (screen_width - 100, 80))

                            
            manager.process_events(event)

        skill_screen.visibility()
        if player.health <= 0:  # Check if player is dead
            player.respawn() 

        if not pause:
            player.move()

            for enemy in current_room.enemies:
                enemy.follow(obstacles, current_room.enemies)

            # Update all ChasingEnemies in the global group
            for enemy in all_enemies:
                if isinstance(enemy, ChasingEnemy):  # Ensure we only call follow on ChasingEnemies
                    enemy.follow(obstacles, current_room.enemies)

            # Detect mouse click for attacking
            if pygame.mouse.get_pressed()[0] and current_room.is_save_room == False:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                player.attack(mouse_pos)


            # Update projectiles
            projectiles.update()

            screen.fill(current_room.background)

            if current_room.is_save_room:
                save_button.show()
                player.health = player.get_max_health()

                screen.blit(shopkeeper_image, camera.apply(shopkeeper_rect.topleft))
                if shopkeeper_rect.colliderect(player.rect):
                    open_shop_button.show()

                else:
                    open_shop_button.hide()


            else:
                save_button.hide()


            zone1.draw()
            zone2.draw()
            
            player.draw()
            current_room.spawn_enemies()

            for projectile in projectiles:
                screen.blit(projectile.surface, camera.apply(projectile))
                for enemy in current_room.enemies:
                    if pygame.sprite.collide_rect(enemy, projectile):
                        enemy.health -= player.strength
                        print(f"enemy hit Enemy health: {enemy.health}")
                        projectile.kill()  # Remove the projectile
                        if enemy.health <= 0:
                            coin_position = (enemy.rect.x, enemy.rect.y)
                            if coin_position not in coins[pointer - 1]:
                                coins[pointer - 1].append(coin_position)

                            current_room.enemies.remove(enemy)  # Remove the enemy if health is 0 or less
                            skill_points += 1
                            print("enemy killed")

            try:
                coins_to_remove = []
                for i in coins[pointer - 1]:
                    screen.blit(coin_image, camera.apply((i)))
                    coin_rect = pygame.Rect(i[0], i[1], coin_image.get_width(), coin_image.get_height())
                    if player.rect.colliderect(coin_rect):
                        coins_to_remove.append(i)
                        money += 1
                        coin_sound_effect.play()




    # Remove collected coins after checking for collisions
                for coin in coins_to_remove:
                    coins[pointer - 1].remove(coin)

            except:
                pass


            player.draw_health_bar()
            player.draw_inventory()

        elif skilltree_button_pressed:
                screen.blit(background, (0, 0))
                skill_screen.manager.draw_ui(screen)
                strength_text = font.render(str(player.strength), False, red)
                screen.blit(strength_text, (350, 100))
                speed_text = font.render(str(round(player.speed, 1)), False, blue)
                screen.blit(speed_text, (550, 100))
                health_text = font.render(str(player.get_max_health()), False, green)
                screen.blit(health_text, (750, 100))



        skill_points_text = font.render("skill points: " + str(skill_points), False, black)
        screen.blit(skill_points_text, (screen_width - 100, 50))
        money_text = font.render("Coins: " + str(money), False, black)
        screen.blit(money_text, (screen_width - 100, 80))


        if (player.rect.x + player.rect.width >= zone2.rect.x 
            and player.rect.y + player.rect.height >= zone2.rect.y 
            and player.rect.y <= zone2.rect.y + zone2.rect.height):

            for projectile in projectiles:
                projectile.kill()
            player.room_pos += 1

            nextroom()
            print(current_room.name)

        if pointer > 0 and (player.rect.x <= zone1.rect.x + zone1.rect.width
                            and player.rect.y + player.rect.height >= zone1.rect.y
                            and player.rect.y <= zone1.rect.y + zone1.rect.height):
            
            for projectile in projectiles:
                projectile.kill()
            player.room_pos -=1
            pastroom()


        # Show or hide the save button based on the current room


        camera.update(player, current_room.width, current_room.height)
        manager.update(clock.tick(60) / 1000)
        manager.draw_ui(screen)
        pygame.display.flip()

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        exit()