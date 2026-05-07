import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'campus_trade.db')

def init():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript('''
    DROP TABLE IF EXISTS Orders;
    DROP TABLE IF EXISTS Item;
    DROP TABLE IF EXISTS User;

    CREATE TABLE User (
        user_id TEXT PRIMARY KEY,
        user_name TEXT NOT NULL,
        phone TEXT
    );

    CREATE TABLE Item (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        category TEXT,
        price REAL,
        status INTEGER DEFAULT 0 CHECK(status IN (0, 1)),
        seller_id TEXT,
        FOREIGN KEY (seller_id) REFERENCES User(user_id)
    );

    CREATE TABLE Orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER UNIQUE,
        buyer_id TEXT,
        order_date DATE,
        FOREIGN KEY (item_id) REFERENCES Item(item_id),
        FOREIGN KEY (buyer_id) REFERENCES User(user_id)
    );

    -- 视图任务
    CREATE VIEW IF NOT EXISTS sold_items_view AS 
    SELECT i.item_name, o.buyer_id FROM Item i JOIN Orders o ON i.item_id = o.item_id;

    CREATE VIEW IF NOT EXISTS unsold_items_view AS 
    SELECT * FROM Item WHERE status = 0;
    ''')

    # 初始数据
    users = [('u001', 'ZhangSan', '13800000001'), ('u002', 'LiSi', '13800000002'), 
             ('u003', 'WangWu', '13800000003'), ('u004', 'ZhaoLiu', '13800000004')]
    items = [(1001, 'CalculusBook', 'Book', 20, 0, 'u001'),
             (1002, 'DeskLamp', 'DailyGoods', 35, 1, 'u002'),
             (1003, 'Microcontroller', 'Electronics', 80, 0, 'u001'),
             (1004, 'Chair', 'Furniture', 50, 1, 'u003'),
             (1005, 'WaterBottle', 'DailyGoods', 15, 0, 'u004')]
    orders = [(1002, 'u001', '2024-05-01'), (1004, 'u002', '2024-05-03')]

    cursor.executemany("INSERT INTO User VALUES (?,?,?)", users)
    cursor.executemany("INSERT INTO Item VALUES (?,?,?,?,?,?)", items)
    cursor.executemany("INSERT INTO Orders (item_id, buyer_id, order_date) VALUES (?,?,?)", orders)

    conn.commit()
    conn.close()
    print("数据库初始化成功！")

if __name__ == '__main__':
    init()