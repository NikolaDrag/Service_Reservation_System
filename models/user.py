from enum import Enum
from typing import Optional, List
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from models.service import Service
from models.review import Review
from models.reservation import Reservation, ReservationStatus


class Guest:
    """
    Базов клас за гост (нерегистриран потребител).
    
    Гостът може да:
    - Търси услуги по име и категория
    - Преглежда страница на услуга
    - Преглежда ревюта за услуга
    - Да се регистрира (става RegisteredUser)
    
    ВАЖНО: Този клас НЕ наследява db.Model, защото гостите
    не се записват в базата данни - те са анонимни посетители.
    """
    
    def search_services(self, name: Optional[str] = None, 
                       category: Optional[str] = None,
                       date_on: Optional[date] = None) -> List[dict]:
        """
        Търсене на услуги по име, категория и дата.
        
        Параметри:
            name: Част от името на услугата (незадължително)
            category: Категория на услугата (незадължително)
            date_on: Търси услуги налични НА тази дата (незадължително)
        
        Връща:
            Списък с речници, съдържащи данни за услугите
        """
        
        query = Service.query # Започваме с празна заявка (SELECT * FROM services)
        
        # Добавяме филтри само ако параметърът е подаден
        if name:
            query = query.filter(Service.name.ilike(f'%{name}%'))# ilike = case-insensitive LIKE (търси без значение от главни/малки букви)
            
        if category:
            query = query.filter(Service.category.ilike(f'%{category}%'))
        
        if date_on:
            
            reserved_service_ids = db.session.query(Reservation.service_id).filter( # db.session.query(колона) = избираме само 1 колона, вместо целия обект
                db.func.date(Reservation.datetime) == date_on # db.func.date() = SQL функция DATE() - извлича само датата от datetime поле
            ).all() # Резултат: списък от tuples [(1,), (3,), (5,)]
            
            if reserved_service_ids:
                reserved_ids = [r[0] for r in reserved_service_ids]
                query = query.filter(~Service.id.in_(reserved_ids))# ~ = NOT, .in_() = IN оператор
        
        services = query.all() # Изпълняваме заявката и взимаме всички резултати
        
        result = []
        for s in services: # Преобразуваме SQLAlchemy обектите в прости речници
            result.append({
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'category': s.category
            })
        return result
    
    def view_service(self, service_id: int) -> Optional[dict]:
        """
        Преглед на конкретна услуга по ID.
        
        Параметри:
            service_id: ID на услугата
        
        Връща:
            Речник с данни за услугата или None ако не е намерена
            
        Обяснение:
            - query.get(id) = SELECT * FROM services WHERE id = service_id
            - Връща един обект или None
        """
        service = Service.query.get(service_id)
        
        if not service:
            return None
        
        return {
            'id': service.id,
            'name': service.name,
            'description': service.description,
            'category': service.category,
            'provider_id': service.provider_id
        }
    
    def view_reviews(self, service_id: int) -> List[dict]:
        """
        Преглед на ревюта за услуга.
        
        Параметри:
            service_id: ID на услугата
        
        Връща:
            Списък с речници, съдържащи ревютата
            
        Обяснение:
            - filter_by(service_id=X) = WHERE service_id = X
            - Проста форма на filter() за точно съвпадение
        """
        reviews = Review.query.filter_by(service_id=service_id).all()
        
        result = []
        for r in reviews:
            result.append({
                'id': r.id,
                'rating': r.rating,
                'comment': r.comment,
                'user_id': r.user_id
            })
        return result


class UserRole(Enum):
    USER = "user"
    PROVIDER = "provider"
    ADMIN = "admin"


class RegisteredUser(Guest, db.Model):
    """
    Регистриран потребител - наследява Guest.
    
    Наследяване:
        Guest -> RegisteredUser
        
    Това означава, че RegisteredUser може всичко, което Guest може
    (search_services, view_service, view_reviews), плюс нови методи.
    
    Регистрираният потребител може:
        - Всичко, което госта може
        - Влизане/излизане от акаунта
        - Управление на профила си
        - Създаване на резервация
        - Преглед и управление на своите резервации
        - Отмяна или промяна на резервация
        - Оставяне на ревю
        
    ВАЖНО: Този клас наследява db.Model, защото данните се записват в базата.
    """
    __tablename__ = 'users'

    # Колони в базата данни
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.USER)

    # Релации с други таблици
    # backref='customer' означава: от Reservation можеш да достъпиш reservation.customer
    reservations = db.relationship('Reservation', foreign_keys='Reservation.customer_id', backref='customer', lazy=True)
    reviews = db.relationship('Review', backref='author', lazy=True)

    # ==================== МЕТОДИ ЗА АВТЕНТИКАЦИЯ ====================
    
    @classmethod
    def login(cls, email_or_username: str, password: str) -> Optional['RegisteredUser']:
        """
        Влизане в акаунт с имейл/потребителско име и парола.
        
        Параметри:
            email_or_username: Имейл ИЛИ потребителско име
            password: Паролата
            
        Връща:
            RegisteredUser обект ако успешно, None ако грешни данни
            
        Защо @classmethod?
            - Не е нужен конкретен потребител за да извикаме login
            - Извикваме го на класа: RegisteredUser.login(...)
            - cls = самият клас RegisteredUser
        """
        
        user = cls.query.filter(
            db.or_(cls.email == email_or_username, cls.username == email_or_username)# db.or_() = SQL OR оператор (по-добре от | за Pylance)
        ).first()
        
        # Ако не намерим потребител или паролата е грешна
        if not user or not user.check_password(password):
            return None
        
        return user
    
    def set_password(self, password: str) -> None:
        """
        Хешира и записва паролата.
        
        Параметри:
            password: Паролата в чист текст
            
        Защо хешираме?
            - Никога не записваме пароли в чист текст!
            - generate_password_hash() създава hash, който не може да се обърне
            - Дори ако базата бъде хакната, паролите са защитени
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        Проверява дали паролата е вярна.
        
        Параметри:
            password: Паролата за проверка
            
        Връща:
            True ако паролата съвпада, False ако не
            
        Как работи:
            - check_password_hash() хешира подадената парола
            - Сравнява я със записания hash
            - Връща True/False
        """
        return check_password_hash(self.password_hash, password)
    
    def create_reservation(self, service_id: int, reservation_date: datetime, 
                          notes: Optional[str] = None) -> Reservation:
        """
        Създава нова резервация за услуга.
        
        Параметри:
            service_id: ID на услугата, която искаме да резервираме
            reservation_date: Дата и час на резервацията
            notes: Бележки към резервацията (незадължително)
            
        Връща:
            Създадената резервация (обектът, не само ID-то)
            
        Защо връщаме Reservation обект?
            - Можем да вземем ID-то: reservation.id
            - Можем да го използваме веднага
            - Обектът вече Е записан в базата след commit()
            
        Изключения:
            ValueError: Ако услугата не съществува
        """
        service = Service.query.get(service_id)
        if not service:
            raise ValueError("Услугата не съществува")
        
        reservation = Reservation(
            datetime=reservation_date,              # Кога е резервацията
            status=ReservationStatus.PENDING,       # от ReservationStatus(Enum)
            customer_id=self.id,                    # Клиентът е текущият потребител (self)
            provider_id=service.provider_id,        # Доставчикът е собственикът на услугата
            service_id=service_id,                  # подадена като аргумент
            notes=notes                             # подадена като аргумент
        )
        
        # db.session.add() - подготвя обекта за запис (още не е в базата!)
        db.session.add(reservation)
        
        # db.session.commit() - ЗАПИСВА в базата данни (като "Save" бутон)
        db.session.commit()
        
        return reservation
    
    def get_my_reservations(self, status: Optional[ReservationStatus] = None) -> List[dict]:
        """
        Връща всички резервации на потребителя.
        
        Параметри:
            status: Филтрира по статус (незадължително)
            
        Връща:
            Списък с речници, съдържащи данни за резервациите
        """
        query = Reservation.query.filter_by(customer_id=self.id)
        
        if status:
            query = query.filter_by(status=status)
        
        reservations = query.all()
        
        result = []
        for r in reservations:
            result.append({
                'id': r.id,
                'datetime': r.datetime.isoformat(),
                'status': r.status.value,
                'service_id': r.service_id,
                'notes': r.notes
            })
        return result
    
    def cancel_reservation(self, reservation_id: int) -> bool:
        """
        Отменя резервация.
        
        Параметри:
            reservation_id: ID на резервацията
            
        Връща:
            True ако е успешно, False ако резервацията не е намерена
            или не принадлежи на този потребител
        """
        # Търсим резервация, която е наша (customer_id == self.id)
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            customer_id=self.id
        ).first()
        
        if not reservation:
            return False
        
        reservation.status = ReservationStatus.CANCELED
        db.session.commit()
        return True
    
    def update_reservation(self, reservation_id: int, 
                          new_datetime: Optional[datetime] = None,
                          new_notes: Optional[str] = None) -> bool:
        """
        Променя резервация.
        
        Параметри:
            reservation_id: ID на резервацията
            new_datetime: Нова дата и час (незадължително)
            new_notes: Нови бележки (незадължително)
            
        Връща:
            True ако е успешно, False ако резервацията не е намерена
        """
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            customer_id=self.id
        ).first()
        
        if not reservation:
            return False
        
        if new_datetime:
            reservation.datetime = new_datetime
        if new_notes is not None:  # Позволяваме празен string
            reservation.notes = new_notes
        
        db.session.commit()
        return True

    # ==================== МЕТОДИ ЗА РЕВЮТА ====================
    
    def leave_review(self, service_id: int, rating: int, 
                    comment: Optional[str] = None) -> Review:
        """
        Оставя ревю за услуга.
        
        Параметри:
            service_id: ID на услугата
            rating: Оценка от 1 до 5
            comment: Коментар (незадължително)
            
        Връща:
            Създаденото ревю
            
        Изключения:
            ValueError: Ако оценката не е между 1 и 5
            ValueError: Ако услугата не съществува
        """
        if not 1 <= rating <= 5:
            raise ValueError("Оценката трябва да е между 1 и 5")
        
        service = Service.query.get(service_id)
        if not service:
            raise ValueError("Услугата не съществува")
        
        review = Review(
            rating=rating,
            comment=comment,
            user_id=self.id,
            service_id=service_id
        )
        
        db.session.add(review)
        db.session.commit()
        return review

    # ==================== МЕТОДИ ЗА ПРОФИЛ ====================
    
    def update_profile(self, new_username: Optional[str] = None,
                      new_email: Optional[str] = None) -> bool:
        """
        Обновява профила на потребителя.
        
        Параметри:
            new_username: Ново потребителско име (незадължително)
            new_email: Нов имейл (незадължително)
            
        Връща:
            True ако е успешно
            
        Изключения:
            ValueError: Ако потребителското име или имейл вече са заети
        """
        if new_username:
            existing = RegisteredUser.query.filter_by(username=new_username).first()
            if existing and existing.id != self.id:
                raise ValueError("Потребителското име е заето")
            self.username = new_username
        
        if new_email:
            existing = RegisteredUser.query.filter_by(email=new_email).first()
            if existing and existing.id != self.id:
                raise ValueError("Имейлът е зает")
            self.email = new_email
        
        db.session.commit()
        return True
    
    def to_dict(self) -> dict:
        """
        Преобразува потребителя в речник.
        
        Връща:
            Речник с данни за потребителя (без паролата!)
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value
        }


# ==================== PROVIDER КЛАС ====================

class Provider(RegisteredUser):
    """
    Доставчик на услуги - наследява RegisteredUser.
    
    Наследяване:
        Guest -> RegisteredUser -> Provider
        
    Provider може:
        - Всичко, което RegisteredUser може (резервации, ревюта, профил)
        - Създаване и управление на услуги
        - Преглед на получени резервации
        - Потвърждаване/отказване на резервации
        - Преглед на ревюта за своите услуги
        - Управление на работно време (чрез availability поле в Service)
        
    ВАЖНО: Използваме Single Table Inheritance (STI).
    Provider НЕ създава нова таблица - използва същата 'users' таблица,
    но с role = UserRole.PROVIDER
    
    Single Table Inheritance означава:
        - Всички типове потребители са в ЕДНА таблица 'users'
        - Разликата е в колоната 'role'
        - SQLAlchemy знае кой клас да използва по role
    """
    
    # Казваме на SQLAlchemy, че това НЕ е отделна таблица
    # __mapper_args__ настройва наследяването
    __mapper_args__ = {
        'polymorphic_identity': UserRole.PROVIDER  # Когато role = PROVIDER, използвай този клас
    }
    
    # ==================== МЕТОДИ ЗА УПРАВЛЕНИЕ НА УСЛУГИ ====================
    
    def create_service(self, name: str, description: str, category: str,
                      price: float, duration: int = 60,
                      availability: Optional[str] = None) -> Service:
        """
        Създава нова услуга.
        
        Параметри:
            name: Име на услугата
            description: Описание
            category: Категория (например: "Фризьорски", "Козметични")
            price: Цена
            duration: Продължителност в минути (по подразбиране 60)
            availability: Работно време като текст (например: "Пон-Пет 9:00-18:00")
            
        Връща:
            Създадената услуга
            
        Пример:
            provider.create_service(
                name="Мъжко подстригване",
                description="Класическо подстригване с машинка",
                category="Фризьорски",
                price=25.00,
                duration=30,
                availability="Пон-Съб 10:00-19:00"
            )
        """
        service = Service(
            name=name,
            description=description,
            category=category,
            price=price,
            duration=duration,
            availability=availability,
            provider_id=self.id  # Собственикът е текущият provider
        )
        
        db.session.add(service)
        db.session.commit()
        return service
    
    def update_service(self, service_id: int, 
                      name: Optional[str] = None,
                      description: Optional[str] = None,
                      category: Optional[str] = None,
                      price: Optional[float] = None,
                      duration: Optional[int] = None,
                      availability: Optional[str] = None) -> bool:
        """
        Обновява услуга.
        
        Параметри:
            service_id: ID на услугата
            name, description, category, price, duration, availability: 
                Новите стойности (само подадените се променят)
            
        Връща:
            True ако е успешно, False ако услугата не е намерена
            или не принадлежи на този provider
        """
        # Търсим услуга, която е НАША (provider_id == self.id)
        service = Service.query.filter_by(
            id=service_id,
            provider_id=self.id
        ).first()
        
        if not service:
            return False
        
        # Обновяваме само подадените полета
        if name is not None:
            service.name = name
        if description is not None:
            service.description = description
        if category is not None:
            service.category = category
        if price is not None:
            service.price = price
        if duration is not None:
            service.duration = duration
        if availability is not None:
            service.availability = availability
        
        db.session.commit()
        return True
    
    def delete_service(self, service_id: int) -> bool:
        """
        Изтрива услуга.
        
        Параметри:
            service_id: ID на услугата
            
        Връща:
            True ако е успешно, False ако услугата не е намерена
        """
        service = Service.query.filter_by(
            id=service_id,
            provider_id=self.id
        ).first()
        
        if not service:
            return False
        
        db.session.delete(service)  # db.session.delete() = премахва от базата
        db.session.commit()
        return True
    
    def get_my_services(self) -> List[dict]:
        """
        Връща всички услуги на този provider.
        
        Връща:
            Списък с речници с данни за услугите
        """
        services = Service.query.filter_by(provider_id=self.id).all()
        
        result = []
        for s in services:
            result.append({
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'category': s.category,
                'price': s.price,
                'duration': s.duration,
                'availability': s.availability
            })
        return result
    
    # ==================== МЕТОДИ ЗА УПРАВЛЕНИЕ НА РЕЗЕРВАЦИИ ====================
    
    def get_received_reservations(self, 
                                  status: Optional[ReservationStatus] = None) -> List[dict]:
        """
        Връща резервациите, получени от клиенти за услугите на този provider.
        
        Параметри:
            status: Филтрира по статус (незадължително)
            
        Връща:
            Списък с речници с данни за резервациите
            
        Разлика от get_my_reservations():
            - get_my_reservations() = резервации, които АЗ съм направил като клиент
            - get_received_reservations() = резервации, които КЛИЕНТИ са направили при мен
        """
        query = Reservation.query.filter_by(provider_id=self.id)
        
        if status:
            query = query.filter_by(status=status)
        
        reservations = query.all()
        
        result = []
        for r in reservations:
            result.append({
                'id': r.id,
                'datetime': r.datetime.isoformat(),
                'status': r.status.value,
                'service_id': r.service_id,
                'customer_id': r.customer_id,
                'notes': r.notes
            })
        return result
    
    def confirm_reservation(self, reservation_id: int) -> bool:
        """
        Потвърждава резервация.
        
        Параметри:
            reservation_id: ID на резервацията
            
        Връща:
            True ако е успешно, False ако резервацията не е намерена
        """
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            provider_id=self.id
        ).first()
        
        if not reservation:
            return False
        
        reservation.status = ReservationStatus.CONFIRMED
        db.session.commit()
        return True
    
    def reject_reservation(self, reservation_id: int) -> bool:
        """
        Отказва резервация.
        
        Параметри:
            reservation_id: ID на резервацията
            
        Връща:
            True ако е успешно, False ако резервацията не е намерена
        """
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            provider_id=self.id
        ).first()
        
        if not reservation:
            return False
        
        reservation.status = ReservationStatus.CANCELED
        db.session.commit()
        return True
    
    def complete_reservation(self, reservation_id: int) -> bool:
        """
        Маркира резервация като изпълнена.
        
        Параметри:
            reservation_id: ID на резервацията
            
        Връща:
            True ако е успешно, False ако резервацията не е намерена
        """
        reservation = Reservation.query.filter_by(
            id=reservation_id,
            provider_id=self.id
        ).first()
        
        if not reservation:
            return False
        
        reservation.status = ReservationStatus.COMPLETED
        db.session.commit()
        return True
    
    # ==================== МЕТОДИ ЗА РЕВЮТА ====================
    
    def get_service_reviews(self, service_id: int) -> List[dict]:
        """
        Връща ревютата за конкретна услуга на този provider.
        
        Параметри:
            service_id: ID на услугата
            
        Връща:
            Списък с ревюта, или празен списък ако услугата не е наша
        """
        # Проверяваме дали услугата е наша
        service = Service.query.filter_by(
            id=service_id,
            provider_id=self.id
        ).first()
        
        if not service:
            return []
        
        reviews = Review.query.filter_by(service_id=service_id).all()
        
        result = []
        for r in reviews:
            result.append({
                'id': r.id,
                'rating': r.rating,
                'comment': r.comment,
                'user_id': r.user_id
            })
        return result
    
    def get_average_rating(self, service_id: Optional[int] = None) -> Optional[float]:
        """
        Изчислява средната оценка.
        
        Параметри:
            service_id: ID на услуга (ако None, изчислява за всички услуги)
            
        Връща:
            Средна оценка (float) или None ако няма ревюта
            
        Пример:
            provider.get_average_rating()           # За всички услуги
            provider.get_average_rating(service_id=5)  # За конкретна услуга
        """
        if service_id:
            # Средна оценка за конкретна услуга
            reviews = Review.query.filter_by(service_id=service_id).all()
        else:
            # Средна оценка за ВСИЧКИ наши услуги
            my_service_ids = db.session.query(Service.id).filter_by(
                provider_id=self.id
            ).all()
            
            if not my_service_ids:
                return None
            
            service_ids = [s[0] for s in my_service_ids]
            reviews = Review.query.filter(Review.service_id.in_(service_ids)).all()
        
        if not reviews:
            return None
        
        # Изчисляваме средната стойност
        total = sum(r.rating for r in reviews)
        return total / len(reviews)
    
    # ==================== УПРАВЛЕНИЕ НА РАБОТНО ВРЕМЕ ====================
    
    def set_availability(self, service_id: int, availability: str) -> bool:
        """
        Задава работно време за услуга.
        
        Параметри:
            service_id: ID на услугата
            availability: Работно време като текст
                         Пример: "Пон-Пет 9:00-18:00, Съб 10:00-14:00"
            
        Връща:
            True ако е успешно, False ако услугата не е намерена
            
        Забележка:
            Работното време се записва като текст в Service модела.
            За по-сложна система може да се създаде отделен модел 
            AvailabilitySlot с конкретни дни и часове.
        """
        return self.update_service(service_id, availability=availability)


# Alias за обратна съвместимост - старият код използва User
User = RegisteredUser

