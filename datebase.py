import sqlite3

def create_database(db_path="users.db"):
    """
    Crea la base de datos si no existe.

    Args:
        db_path (str): Ruta al archivo de la base de datos.

    Returns:
        None
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
