from app import db, User, app

def create_admin():
    with app.app_context():
        user = User(username="suman", password="admin", name="Admin", role="sponsor", niche="all")
        db.session.add(user)
        db.session.commit()
        print("Admin-User created successfully...")
        
if __name__ == '__main__':
    create_admin()

