import socket
import pygame
import json
import time

# Initialize Pygame
pygame.init()

# Constants
SERVER_ADDRESS = ('localhost', 12345)  # 修改為與 server.py 相同的端口
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 560
FPS = 30
IMAGE_PATH = 'imgs/'

MAP_IMAGES = [
    pygame.image.load(IMAGE_PATH + 'map1.png'),
    pygame.image.load(IMAGE_PATH + 'map2.png')
]

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Plant Player")

# Load images
sunflower_image = pygame.image.load('imgs/sunflower.png')
peashooter_image = pygame.image.load('imgs/peashooter.png')
zombie_image = pygame.image.load('imgs/zombie.png')
peabullet_image = pygame.image.load('imgs/peabullet.png')

class Zombie:
    def __init__(self, x, y):
        self.image = zombie_image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.hp = 100
        self.live = True

def send_plant_placement(x, y, plant_type):
    try:
        message = {
            'action': 'place_plant',
            'position': (x, y),
            'plant_type': plant_type
        }
        client_socket.sendall(json.dumps(message).encode('utf-8'))
    except (ConnectionAbortedError, ConnectionResetError) as e:
        print(f"連線錯誤: {e}")
        return False
    return True

def reconnect():
    global client_socket
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(SERVER_ADDRESS)
            client_socket.send("plant".encode())
            print("重新連線成功！")
            return True
        except ConnectionRefusedError:
            attempt += 1
            print(f"重新連線失敗 ({attempt}/{max_attempts})")
            time.sleep(2)
    return False

# 修改 draw_map 函數
def draw_map(screen):
    for y in range(1, 7):  # 從1開始，跳過第一排
        for x in range(10):
            map_index = (x + y) % 2
            screen.blit(MAP_IMAGES[map_index], (x * 80, y * 80))

def draw_plants(screen, plants):
    for plant in plants:
        image = sunflower_image if plant['type'] == 'sunflower' else peashooter_image
        screen.blit(image, (plant['x'], plant['y']))

class Map:
    def __init__(self, x, y, img_index):
        self.image = MAP_IMAGES[img_index]
        self.position = (x, y)
        self.can_grow = True

class Plant:
    def __init__(self):
        self.live = True
        self.hp = 100

class Sunflower(Plant):
    def __init__(self, x, y):
        super().__init__()
        self.image = sunflower_image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.price = 50
        self.hp = 100
        self.time_count = 0

    def produce_money(self):
        self.time_count += 1
        if self.time_count == 25:  # 每25個時間單位產生金錢
            self.time_count = 0
            return 5  # 產生5塊錢
        return 0

class PeaShooter(Plant):
    def __init__(self, x, y):
        super().__init__()
        self.image = peashooter_image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.price = 50
        self.hp = 200
        self.shot_count = 0
    
    def should_shoot(self, zombies):
        for zombie in zombies:
            if (zombie.rect.y == self.rect.y and 
                zombie.rect.x < SCREEN_WIDTH and 
                zombie.rect.x > self.rect.x):
                return True
        return False

class PeaBullet:
    def __init__(self, peashooter):
        self.image = peabullet_image
        self.rect = self.image.get_rect()
        self.rect.x = peashooter['x'] + 60
        self.rect.y = peashooter['y'] + 15
        self.damage = 50
        self.speed = 10
        self.live = True

    def move(self):
        if self.rect.x < SCREEN_WIDTH:
            self.rect.x += self.speed
        else:
            self.live = False

    def draw(self, screen):
        if self.live:
            screen.blit(self.image, self.rect)

def init_map():
    map_list = []
    for y in range(1, 7):
        temp_map_list = []
        for x in range(10):
            if (x + y) % 2 == 0:
                map = Map(x * 80, y * 80, 0)
            else:
                map = Map(x * 80, y * 80, 1)
            temp_map_list.append(map)
        map_list.append(temp_map_list)
    return map_list

def main():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 初始化遊戲數據
    money = 200
    map_list = init_map()
    plants = []
    zombies = []
    peabullets = []  # 新增子彈列表

    # 添加重試連接機制
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        try:
            client_socket.connect(SERVER_ADDRESS)
            print("Connected to server!")
            
            # Tell server this is plant client
            client_socket.send("plant".encode())
            break
            
        except ConnectionRefusedError:
            attempt += 1
            print(f"Connection failed, retrying... ({attempt}/{max_attempts})")
            time.sleep(2)
            
    if attempt >= max_attempts:
        print("Could not connect to server")
        return

    clock = pygame.time.Clock()
    running = True

    # 創建向日葵實例列表
    sunflowers = []
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x = event.pos[0] // 80
                y = event.pos[1] // 80
                
                # 確保不在第一排種植
                if 0 <= x < 10 and 1 <= y < 7:  # y 必須從 1 開始
                    map = map_list[y-1][x]
                    
                    if map.can_grow and money >= 50:
                        if event.button == 1:  # 左鍵放向日葵
                            sunflower = Sunflower(x * 80, y * 80)
                            sunflowers.append(sunflower)
                            plant_data = {
                                'type': 'sunflower',
                                'x': x * 80,
                                'y': y * 80,
                                'hp': 100
                            }
                            
                            # 嘗試發送植物放置訊息
                            if send_plant_placement(x * 80, y * 80, 'sunflower'):
                                plants.append(plant_data)
                                map.can_grow = False
                                money -= 50
                            else:
                                # 如果發送失敗，嘗試重新連接
                                if reconnect():
                                    # 重新發送
                                    if send_plant_placement(x * 80, y * 80, 'sunflower'):
                                        plants.append(plant_data)
                                        map.can_grow = False
                                        money -= 50
                                else:
                                    print("無法重新連接到伺服器")
                                    running = False
                                    break
                                    
                        elif event.button == 3:  # 右鍵放豌豆射手
                            peashooter = PeaShooter(x * 80, y * 80)
                            plants.append({
                                'type': 'peashooter',
                                'x': x * 80,
                                'y': y * 80,
                                'hp': 200
                            })
                            map.can_grow = False
                            money -= 50
                            send_plant_placement(x * 80, y * 80, 'peashooter')

        try:
            # 接收服務器更新
            client_socket.setblocking(False)
            data = client_socket.recv(1024).decode('utf-8')
            if data:
                game_state = json.loads(data)
                # 更新殭屍位置
                zombies = []
                for zombie_data in game_state.get('active_zombies', []):
                    if zombie_data.get('live', False):
                        x = zombie_data['x']
                        y = zombie_data['y']
                        zombie = Zombie(x, y)
                        zombie.hp = zombie_data.get('hp', 1000)
                        zombies.append(zombie)
        except (ConnectionAbortedError, ConnectionResetError):
            print("連線中斷，嘗試重新連接...")
            if not reconnect():
                print("無法重新連接到伺服器")
                running = False
        except:
            pass

        # 更新畫面
        screen.fill((255, 255, 255))
        draw_map(screen)
        
        # 繪製殭屍
        for zombie in zombies:
            if zombie.live:
                screen.blit(zombie_image, zombie.rect)

        # 更新豌豆射手的射擊
        for plant in plants:
            if plant['type'] == 'peashooter' and plant.get('hp', 0) > 0:
                peashooter = PeaShooter(plant['x'], plant['y'])
                if peashooter.should_shoot(zombies):
                    peashooter.shot_count += 1
                    if peashooter.shot_count >= 25:
                        peashooter.shot_count = 0
                        bullet = PeaBullet(plant)
                        peabullets.append(bullet)
                        # 發送子彈創建消息給服務器
                        message = {
                            'action': 'create_bullet',
                            'position': (plant['x'], plant['y'])
                        }
                        client_socket.sendall(json.dumps(message).encode('utf-8'))
        
        # 更新和繪製子彈
        for bullet in peabullets[:]:
            bullet.move()
            bullet.draw(screen)
            if not bullet.live:
                peabullets.remove(bullet)

        # 更新畫面
        screen.fill((255, 255, 255))
        draw_map(screen)
        
        # 繪製遊戲資訊在最上排
        try:
            font = pygame.font.SysFont('arial', 24)  # Use Arial font
        except:
            font = pygame.font.SysFont(None, 24)  # Use system default font
        
        money_text = font.render(f'Money: ${money}', True, (0, 0, 0))
        help_text = font.render('Left click: Sunflower ($50)    Right click: Peashooter ($50)', True, (0, 0, 0))
        screen.blit(money_text, (10, 10))  # Top left
        screen.blit(help_text, (250, 10))  # Top right
        
        # 繪製植物
        for plant in plants:
            # 添加預設值處理
            hp = plant.get('hp', 100)  # 如果沒有 hp 欄位，預設為 100
            if hp > 0:
                if plant['type'] == 'sunflower':
                    screen.blit(sunflower_image, (plant['x'], plant['y']))
                else:
                    screen.blit(peashooter_image, (plant['x'], plant['y']))
        
        # 在遊戲迴圈中更新金錢
        for sunflower in sunflowers[:]:  # 使用切片來避免在迴圈中修改列表
            if sunflower.hp > 0:  # 只有活著的向日葵才能產生金錢
                money += sunflower.produce_money()
            else:
                sunflowers.remove(sunflower)

        pygame.display.flip()
        clock.tick(FPS)

    client_socket.close()
    pygame.quit()

if __name__ == "__main__":
    main()