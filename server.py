import socket
import threading
import json
import time

class GameServer:
    def __init__(self, host='localhost', port=12345):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        self.clients = {}
        self.SCREEN_WIDTH = 800
        self.update_rate = 2  # 殭屍移動速度
        self.update_interval = 0.05  # 更新間隔
        self.last_update = time.time()
        self.game_state = {
            'plants': [],
            'zombies': [],
            'active_zombies': [],
            'bullets': []
        }
        print(f'伺服器已啟動於 {host}:{port}')
        
        # 啟動主迴圈執行緒
        self.main_loop_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.main_loop_thread.start()

    def main_loop(self):
        """背景主迴圈：定時更新遊戲狀態"""
        while True:
            time.sleep(self.update_interval)
            self.update_game_state()
            self.broadcast_game_state()

    def handle_zombie_placement(self, message):
        """處理殭屍放置"""
        zombie = {
            'x': self.SCREEN_WIDTH,
            'y': message['position'][1] * 80,
            'hp': 1000,
            'live': True,
            'stop': False
        }
        self.game_state['active_zombies'].append(zombie)
        self.broadcast_game_state()

    def handle_plant_placement(self, message):
        """處理植物放置"""
        plant = {
            'type': message['plant_type'],
            'x': message['position'][0],
            'y': message['position'][1],
            'hp': 100 if message['plant_type'] == 'sunflower' else 200
        }
        self.game_state['plants'].append(plant)
        self.broadcast_game_state()

    def handle_bullet_creation(self, message):
        """處理子彈創建"""
        bullet = {
            'x': message['position'][0] + 60,
            'y': message['position'][1] + 15,
            'live': True
        }
        self.game_state['bullets'].append(bullet)
        self.broadcast_game_state()

    def update_game_state(self):
        """更新遊戲狀態"""
        # 更新子彈
        for bullet in self.game_state['bullets'][:]:
            if bullet['live']:
                bullet['x'] += 10
                # 檢查子彈碰撞
                for zombie in self.game_state['active_zombies']:
                    if (zombie['live'] and 
                        abs(bullet['x'] - zombie['x']) < 40 and 
                        abs(bullet['y'] - zombie['y']) < 40):
                        bullet['live'] = False
                        zombie['hp'] -= 50
                        if zombie['hp'] <= 0:
                            zombie['live'] = False
                        break
                
                if bullet['x'] >= self.SCREEN_WIDTH:
                    bullet['live'] = False
            
            if not bullet['live']:
                self.game_state['bullets'].remove(bullet)

        # 更新殭屍
        for zombie in self.game_state['active_zombies']:
            if zombie['live'] and not zombie.get('stop', False):
                zombie['x'] -= self.update_rate
                # 檢查是否碰到植物
                for plant in self.game_state['plants']:
                    if (plant.get('hp', 0) > 0 and 
                        abs(zombie['x'] - plant['x']) < 40 and 
                        zombie['y'] == plant['y']):
                        zombie['stop'] = True
                        plant['hp'] -= 2  # 殭屍攻擊植物
                        break
                
                if zombie['x'] < -80:
                    zombie['live'] = False

        # 清理死亡的物件
        self.game_state['active_zombies'] = [z for z in self.game_state['active_zombies'] if z['live']]
        self.game_state['bullets'] = [b for b in self.game_state['bullets'] if b['live']]
        self.game_state['plants'] = [p for p in self.game_state['plants'] if p.get('hp', 0) > 0]

    def handle_client(self, client_socket, addr):
        try:
            client_type = client_socket.recv(1024).decode('utf-8')
            self.clients[client_socket] = client_type
            print(f'新的 {client_type} 客戶端已連接: {addr}')
            self.broadcast_game_state()

            while True:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    message = json.loads(data.decode('utf-8'))
                    
                    # 根據動作類型處理
                    if message['action'] == 'place_zombie':
                        self.handle_zombie_placement(message)
                    elif message['action'] == 'place_plant':
                        self.handle_plant_placement(message)
                    elif message['action'] == 'create_bullet':
                        self.handle_bullet_creation(message)

                except json.JSONDecodeError:
                    print(f"收到無效的 JSON 資料從 {addr}")
                except Exception as e:
                    print(f"處理客戶端 {addr} 資料時發生錯誤: {str(e)}")
                    break
        finally:
            client_socket.close()
            if client_socket in self.clients:
                del self.clients[client_socket]
            print(f'客戶端斷開連接: {addr}')

    def broadcast_game_state(self):
        """廣播遊戲狀態給所有客戶端"""
        try:
            state_json = json.dumps(self.game_state) + '\n'
            encoded_data = state_json.encode('utf-8')
            for client in list(self.clients.keys()):  # 使用列表複製避免字典在迭代時被修改
                try:
                    client.sendall(encoded_data)
                except:
                    if client in self.clients:
                        del self.clients[client]
        except Exception as e:
            print(f"廣播遊戲狀態時發生錯誤: {str(e)}")

    def start(self):
        print("等待客戶端連接...")
        while True:
            client_socket, addr = self.server.accept()
            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket, addr)
            )
            client_thread.start()

if __name__ == '__main__':
    game_server = GameServer()
    game_server.start()