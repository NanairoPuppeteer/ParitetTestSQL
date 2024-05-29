# Зависимости
Требуется SQLAlchemy 2.0
```sh
python -m pip install 'sqlalchemy>=2.0'
```

# Использование
```sh
from test import Test

# Создаем экземпляр класса с двумя числовыми агрументами - x и y
t = Test(15, 15)

# Получаем x пород с https://catfact.ninja/ и записываем в БД с проверкой на уникальность
t.fetchData()

# Получаем кол-во записей по стране
t.countBreeds("United Kingdom")
# Возвращает число записей

# Возвращаем y записей с БД и сохраняем в json c названием текущей даты
t.saveToJson()
```
