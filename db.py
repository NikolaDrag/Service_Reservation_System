from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db: SQLAlchemy = SQLAlchemy()


def init_db(app: Flask) -> None:
    db.init_app(app)
    with app.app_context():
        db.create_all()
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
    from models.user import Admin, Provider, RegisteredUser, UserRole
    from models.service import Service
    
    existing_admin = RegisteredUser.query.filter_by(role=UserRole.ADMIN).first()
    if existing_admin:
        return  

    admin = Admin(
        username='admin',
        email='admin@reservations.com',
        role=UserRole.ADMIN
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    provider = Provider(
        username='autoservice',
        email='service@autoservice.bg',
        role=UserRole.PROVIDER
    )
    provider.set_password('provider123')
    db.session.add(provider)
    db.session.flush()  # Получаваме provider.id
    
    services = [
        Service(
            name='Смяна на масло',
            description='Пълна смяна на моторно масло и маслен филтър',
            category='Поддръжка',
            price=89.99,
            duration=30,
            availability='Пон-Пет 9:00-18:00, Съб 9:00-14:00',
            provider_id=provider.id
        ),
        Service(
            name='Смяна на накладки',
            description='Смяна на предни или задни спирачни накладки',
            category='Спирачна система',
            price=120.00,
            duration=60,
            availability='Пон-Пет 9:00-18:00',
            provider_id=provider.id
        ),
        Service(
            name='Компютърна диагностика',
            description='Пълна диагностика с професионален скенер',
            category='Диагностика',
            price=45.00,
            duration=30,
            availability='Пон-Съб 9:00-18:00',
            provider_id=provider.id
        ),
        Service(
            name='Смяна на гуми',
            description='Демонтаж, монтаж и баланс на 4 гуми',
            category='Гуми',
            price=40.00,
            duration=45,
            availability='Пон-Съб 8:00-19:00',
            provider_id=provider.id
        ),
        Service(
            name='Годишен технически преглед',
            description='Подготовка и преглед за ГТП',
            category='Преглед',
            price=70.00,
            duration=90,
            availability='Пон-Пет 9:00-17:00',
            provider_id=provider.id
        ),
    ]
    
    for service in services:
        db.session.add(service)
    
    db.session.commit()
    print("Създаден първоначален администратор (admin / admin123)")
    print("Създаден демо автосервиз (autoservice / provider123)")
    print(f"Създадени {len(services)} начални услуги")
