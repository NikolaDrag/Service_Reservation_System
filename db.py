from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db: SQLAlchemy = SQLAlchemy()


def init_db(app: Flask) -> None:
    """
    Инициализира базата данни.
    
    1. Свързва SQLAlchemy с Flask приложението
    2. Създава таблиците ако не съществуват
    3. Създава първоначален администратор ако няма
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Създава таблиците
        
        # Създаваме първоначален администратор
        _create_initial_admin()


def _create_initial_admin() -> None:
    """
    Създава първоначален админ ако няма такъв.
    
    Тази функция е private (започва с _) - използва се само вътрешно.
    
    Данни за админ:
        username: admin
        email: admin@reservations.com
        password: admin123
    """
    # Импортираме тук за да избегнем circular import
    from models.user import Admin, RegisteredUser, UserRole
    
    # Проверяваме дали вече има админ
    existing_admin = RegisteredUser.query.filter_by(role=UserRole.ADMIN).first()
    if existing_admin:
        return  # Вече има админ, не правим нищо
    
    # Създаваме админ
    admin = Admin(
        username='admin',
        email='admin@reservations.com',
        role=UserRole.ADMIN
    )
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    print("Създаден първоначален администратор (admin / admin123)")
