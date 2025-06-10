# pvz-socket

這個專案是一個基於 socket 的多人遊戲，玩家可以在遊戲中放置植物和殭屍。專案包含以下主要檔案：

## 檔案結構

- `server.py`: 設置伺服器以處理來自客戶端的連接，管理遊戲狀態，包括植物和殭屍的放置，並向兩位玩家傳送更新。
  
- `client_plant.py`: 代表植物玩家的客戶端，連接到伺服器並允許玩家在遊戲地圖上放置植物，將植物放置數據發送到伺服器並監聽更新。

- `client_zombie.py`: 代表殭屍玩家的客戶端，連接到伺服器並允許玩家在遊戲地圖上放置殭屍，將殭屍放置數據發送到伺服器並監聽更新。

## 圖片資源

- `imgs/map1.png`: 遊戲使用的第一張地圖。
- `imgs/map2.png`: 遊戲使用的第二張地圖。
- `imgs/peabullet.png`: PeaShooter 使用的子彈。
- `imgs/peashooter.png`: PeaShooter 植物。
- `imgs/sunflower.png`: 向日葵植物。
- `imgs/zombie.png`: 殭屍角色。

## 使用說明

1. 確保已安裝 Python 3.x。
2. 在終端中運行 `server.py` 以啟動伺服器。
3. 分別運行 `client_plant.py` 和 `client_zombie.py` 以啟動植物和殭屍玩家的客戶端。
4. 按照提示在遊戲中放置植物和殭屍，享受遊戲！