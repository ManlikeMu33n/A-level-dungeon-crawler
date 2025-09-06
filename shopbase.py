import sqlite3

class ShopDatabase:
    def __init__(self, db_name = "shop.db"):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_items_table()

    def create_items_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            
            item_name TEXT NOT NULL,
            cost REAL NOT NULL,
            image TEXT NOT NULL
                            
        )
        ''')
        self.connection.commit()

    def add_item(self, item_name, cost, image):
        if item_name:
            # Check if the item already exists
            self.cursor.execute('SELECT * FROM items WHERE item_name = ?', (item_name,))
            if self.cursor.fetchone() is None:  # If no item is found
                self.cursor.execute('''INSERT INTO items (item_name, cost, image) VALUES 
                                    (?, ?, ?)''', (item_name, cost, image))
                self.connection.commit()

            else:
                print(f"Item '{item_name}' already exists.")
        else:
            print("Item name cannot be empty.")

    def fetch_items(self):
        self.cursor.execute('SELECT * FROM items')
        return self.cursor.fetchall()

    def close(self):
        self.connection.close()

if __name__ == '__main__':
    db = ShopDatabase()
    
    db.add_item('AOE blast', 10.0)
    db.add_item('Sword', 15.0)
    db.add_item('Immunity shield', 50.0)
    # db.add_item('', 30.0)  # This line is commented out to prevent an empty item name
    
    # Fetch and print items
    items = db.fetch_items()
    print("Items in the shop:")
    for item in items:
        print(f"ID: {item[0]}, Name: {item[1]}, Cost: {item[2]}")
    
 # Close the database connection when done