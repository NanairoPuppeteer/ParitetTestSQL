from urllib.request import urlopen

import json

from datetime import datetime

from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import select

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

class Base(DeclarativeBase):
    pass

class Breeds(Base):
    __tablename__ = "breeds"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(), unique=True)
    origin: Mapped[str] = mapped_column(String())
    coat: Mapped[str] = mapped_column(String())
    pattern: Mapped[str] = mapped_column(String())

    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    country: Mapped["Countries"] = relationship(back_populates="breeds")

class Countries(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(), unique=True)

    breeds: Mapped[List["Breeds"]] = relationship(back_populates="country", cascade="all, delete-orphan")

# Используем memory-only sqlite БД
engine = create_engine("sqlite://")
Base.metadata.create_all(engine)

# Декоратор для проверки типов
def accepts(*types):
    def check_accepts(f):
        assert len(types) == f.__code__.co_argcount
        def new_f(*args, **kwds):
            for (a, t) in zip(args, types):
                assert isinstance(a, t)
            return f(*args, **kwds)
        new_f.__name__ = f.__name__
        return new_f
    return check_accepts


class Test:

    @accepts(object, int, int)
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
    
    def fetchData(self) -> None:
        url = "https://catfact.ninja/breeds?limit=" + str(self.x)
        response = urlopen(url)
        data = json.loads(response.read())["data"]

        # Множества имен пород/стран в ответе
        countries = set(item["country"] for item in data)
        breeds = set(item["breed"] for item in data)

        with Session(engine) as session:
            # Загрузка моделей для проверки на уникальность
            countries_models = session.query(Countries).where(Countries.name.in_(countries)).all()
            breeds_models = session.query(Breeds).where(Breeds.name.in_(breeds)).all()

            for item in data:
                # Проверка на уникальность - пропускаем породы, уже существующие в БД
                if any(b.name == item["breed"] for b in breeds_models):
                    continue

                # Проверка на уникальность - если страна существует в БД, добавляем породу к сущесвующей стране
                country = next((c for c in countries_models if c.name == item["country"]), None)
                if country == None:
                    # Если страна не существует - создаем
                    country = Countries(name=item["country"], breeds=[])

                    # Добавляем новую модель в список для проверки на уникальность
                    countries_models.append(country)
                
                breed = Breeds(
                    name=item["breed"],
                    origin=item["origin"],
                    coat=item["coat"],
                    pattern=item["pattern"]
                )

                # Раскладываем записи пород по странам
                country.breeds.append(breed)
                
                # Добавляем новую модель в список для проверки на уникальность
                breeds_models.append(breed)
            
            session.add_all(countries_models)
            session.commit()
        
    @accepts(object, str)
    def countBreeds(self, country: str) -> int:
        with Session(engine) as session:
            stmt = select(func.count(Breeds.id)).join(Breeds.country).where(Countries.name == country)
            count = session.scalars(stmt).first()
            return count

    def saveToJson(self):
        dt = datetime.now()
        filename = f"{dt.day:02d}{dt.month:02d}{dt.year:4d}_{dt.hour:02d}{dt.minute:02d}{dt.second:02d}.json"

        with Session(engine) as session, open(filename, "w") as file:
            breeds_models = session.query(Breeds).limit(self.y).all()
            
            # Формат исходящего файла индентичен формату поля data в ответе
            breeds = [
                {
                    "breed": b.name,
                    "country": b.country.name,
                    "origin": b.origin,
                    "coat": b.coat,
                    "pattern": b.pattern
                }
                for b in breeds_models
            ]

            file.write(json.dumps(breeds))
