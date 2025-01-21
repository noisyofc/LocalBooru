from models import init_db

def create_database(db_path='booru_34.db'):
    # Initialize the database with the given path
    session_maker = init_db(f'sqlite:///{db_path}')
    session = session_maker()

    # You can add initial data here if needed
    print(f"Database '{db_path}' created successfully.")

if __name__ == '__main__':
    create_database()