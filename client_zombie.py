import socket
import pygame
import json
import time
import random

# 初始化 Pygame
pygame.init()

# 常數設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 560
FPS = 30
IMAGE_PATH = 'imgs/'

# 設定視窗
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Zombie Player")

# 載入圖片
zombie_image = pygame.image.load('imgs/zombie.png')
sunflower_image = pygame.image.load('imgs/sunflower.png')
peashooter_image = pygame.image.load('imgs/peashooter.png')
peabullet_image = pygame.image.load('imgs/peabullet.png')
MAP_IMAGES = [
    pygame.image.load(IMAGE_PATH + 'map1.png'),
    pygame.image.load(IMAGE_PATH + 'map2.png')
]

class Zombie:
    def __init__(self, x, y):
        self.image = zombie_image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.hp = 1000
        self.damage = 2
        self.speed = 1
        self.live = True
        self.stop = False

    def check_bullet_hit(self, bullets):
        if not bullets:
            return False
            
        for bullet in bullets:
            if not bullet.get('live', False):
                continue
                
            if (self.live and 
                abs(bullet['x'] - self.rect.x) < 40 and 
                abs(bullet['y'] - (self.rect.y + 15)) < 40):  # 調整碰撞檢測的 y 軸位置
                self.hp -= 50
                if self.hp <= 0:
                    self.live = False
                return True
        return False

    def move(self):
        if self.live and not self.stop:
            self.rect.x -= self.speed
            if self.rect.x < -80:  # 如果殭屍走到最左邊
                self.live = False

    def draw(self, screen):
        if self.live:
            screen.blit(self.image, self.rect)

class PeaBullet:
    def __init__(self, x, y):
        self.image = peabullet_image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def draw(self, screen):
        screen.blit(self.image, self.rect)

def draw_map(screen):
    for y in range(1, 7):  # 從第二排開始繪製 (跳過第一排)
        for x in range(10):
            map_index = (x + y) % 2
            screen.blit(MAP_IMAGES[map_index], (x * 80, y * 80))

def connect_to_server(max_attempts=5):
    server_address = ('localhost', 12345)
    attempt = 0
    
    while attempt < max_attempts:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(server_address)
            
            # 告訴伺服器這是殭屍客戶端
            client_socket.send("zombie".encode())
            print("成功連接到伺服器！")
            return client_socket
            
        except (ConnectionRefusedError, ConnectionResetError) as e:
            attempt += 1
            print(f"連接失敗 ({attempt}/{max_attempts}): {str(e)}")
            if attempt < max_attempts:
                print("2秒後重試...")
                time.sleep(2)
            client_socket.close()
    
    raise ConnectionError("無法連接到伺服器，請確認伺服器是否已啟動")

def send_zombie_placement(client_socket, x, y, retries=3):
    """傳送殭屍放置訊息到伺服器，有重試機制"""
    message = {
        'action': 'place_zombie',
        'position': (x, y)
    }
    
    for attempt in range(retries):
        try:
            # 加入訊息結束標記
            json_data = json.dumps(message) + '\n'
            client_socket.sendall(json_data.encode('utf-8'))
            return True
        except (ConnectionAbortedError, ConnectionResetError) as e:
            print(f"傳送失敗 (嘗試 {attempt + 1}/{retries}): {str(e)}")
            if attempt < retries - 1:
                print("正在重試...")
                time.sleep(1)
                continue
    return False

def reconnect():
    """重新連接到伺服器"""
    try:
        new_socket = connect_to_server()
        new_socket.setblocking(False)
        return new_socket
    except Exception as e:
        print(f"重新連接失敗: {str(e)}")
        return None

def receive_data(client_socket):
    """接收完整的資料並處理黏包問題"""
    try:
        data = ''
        try:
            chunk = client_socket.recv(4096).decode('utf-8')
            if chunk:
                data += chunk
        except BlockingIOError:
            pass
                 
        if data:
            # 取最後一個完整的訊息
            messages = data.split('\n')
            if len(messages) > 1:
                last_complete_message = messages[-2]  # -2 是因為最後一個可能不完整
                try:
                    decoded_data = json.loads(last_complete_message)
                    # 改成印出更詳細的資料
                    if 'plants' in decoded_data:
                        plants = decoded_data['plants']
                        print(f"===== 接收到的植物資料 =====")
                        print(f"植物總數: {len(plants)}")
                        for i, plant in enumerate(plants):
                            print(f"植物 {i+1}:")
                            print(f"  類型: {plant.get('type')}")
                            print(f"  位置: ({plant.get('x')}, {plant.get('y')})")
                            print(f"  血量: {plant.get('hp')}")
                        return decoded_data
                except json.JSONDecodeError as e:
                    print(f"JSON 解析錯誤: {e}")
                    
    except Exception as e:
        print(f"接收資料時發生錯誤: {str(e)}")
        
    return None

def main():
    clock = pygame.time.Clock()
    zombies = []
    running = True
    plant_positions = []
    # 初始化 game_state
    game_state = {
        'bullets': [], 
        'active_zombies': [], 
        'plants': []
    }
    
    try:
        client_socket = connect_to_server()
        client_socket.setblocking(False)
        last_update = time.time()
        reconnect_cooldown = 0  # 重連冷卻時間
        
        while running:
            current_time = time.time()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x = event.pos[0] // 80
                    y = event.pos[1] // 80
                    
                    if 1 <= y < 7:
                        if not send_zombie_placement(client_socket, x, y):
                            print("傳送失敗，嘗試重新連接...")
                            if current_time - reconnect_cooldown > 5:  # 5秒冷卻時間
                                new_socket = reconnect()
                                if new_socket:
                                    client_socket = new_socket
                                    reconnect_cooldown = current_time
                                    # 重試傳送
                                    send_zombie_placement(client_socket, x, y)
                                else:
                                    print("無法重新連接到伺服器")

            # 接收服務器更新
            try:
                new_state = receive_data(client_socket)
                if new_state:
                    # 確保有收到新狀態才更新
                    if new_state != game_state:  # 狀態有變化才印出
                        print(f"[ZOMBIE] 更新遊戲狀態:")
                        print(f"植物數量: {len(new_state.get('plants', []))}")
                        print(f"殭屍數量: {len(new_state.get('active_zombies', []))}")
                        print(f"子彈數量: {len(new_state.get('bullets', []))}")
                        game_state = new_state
            except Exception as e:
                print(f"更新遊戲狀態時發生錯誤: {str(e)}")

            # 更新畫面
            screen.fill((255, 255, 255))
            draw_map(screen)
            
            # 繪製植物
            for plant in game_state.get('plants', []):
                if plant and isinstance(plant, dict) and plant.get('hp', 0) > 0:
                    plant_type = plant.get('type')
                    x = plant.get('x')
                    y = plant.get('y')
                    hp = plant.get('hp', 0)
                    
                    if hp > 0 and x is not None and y is not None:
                        try:
                            # 選擇正確的圖片
                            plant_image = sunflower_image if plant_type == 'sunflower' else peashooter_image
                            screen.blit(plant_image, (x, y))
                            print(f"成功繪製植物: {plant_type} at ({x}, {y})")
                        except Exception as e:
                            print(f"繪製植物時發生錯誤: {e}")

            # 繪製子彈
            for bullet in game_state.get('bullets', []):
                if bullet.get('live', False):
                    screen.blit(peabullet_image, (bullet['x'], bullet['y']))
            
            # 繪製殭屍
            for zombie in game_state.get('active_zombies', []):
                if zombie.get('live', False):
                    screen.blit(zombie_image, (zombie['x'], zombie['y']))

            # 顯示說明文字
            font = pygame.font.SysFont('arial', 24)
            help_text = font.render('Click grid to place zombie', True, (0, 0, 0))
            screen.blit(help_text, (10, 10))

            pygame.display.flip()
            clock.tick(FPS)

    except Exception as e:
        print(f"發生錯誤: {str(e)}")
    finally:
        pygame.quit()
        if 'client_socket' in locals():
            client_socket.close()

if __name__ == "__main__":
    main()