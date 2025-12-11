from app import db, User, app, hash_password

def create_admin():
    with app.app_context():
        user = User(username="admin@admin.com", password=hash_password("Admin@12345"), name="Admin", role="admin", niche="all")
        db.session.add(user)
        db.session.commit()
        print("Admin-User created successfully...")
        
if __name__ == '__main__':
    create_admin()

