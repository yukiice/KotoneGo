# 11 面向对象

> 主题标签：`oop` ｜ 对应考试主题：面向对象

## 11.1 类与实例

```python
class Dog:
    species = "Canis familiaris"        # 类变量（所有实例共享）

    def __init__(self, name: str, age: int):   # 初始化方法
        self.name = name                        # 实例变量
        self.age = age

    def bark(self) -> str:                      # 实例方法
        return f"{self.name}: 汪！"

    def __repr__(self) -> str:                  # 调试表示
        return f"Dog(name={self.name!r}, age={self.age})"

    def __str__(self) -> str:                   # 用户友好表示
        return f"{self.name}（{self.age} 岁）"

d = Dog("旺财", 3)        # 创建实例（不需要 new）
print(d.bark())           # 旺财：汪！
print(d)                  # 旺财（3 岁）         ← __str__
print(repr(d))            # Dog(name='旺财', age=3)
print(d.species, Dog.species)
```

要点：

- **没有 `new`**，类名加括号即实例化。
- 实例方法第一个参数是 `self`（约定名，自动传入）。
- `__init__` 是初始化，不是构造（真正的构造是 `__new__`）。
- `type(d)` 是 `Dog`；`isinstance(d, Dog)` 为 `True`。

## 11.2 类变量 vs 实例变量

```python
class Counter:
    total = 0                      # 类变量：共享

    def __init__(self, name):
        self.name = name           # 实例变量：各自独立
        Counter.total += 1         # 修改类变量要用类名

c1, c2 = Counter("a"), Counter("b")
print(Counter.total)     # 2
print(c1.total)          # 2   ← 读实例时回退到类变量
c1.total = 99            # 在实例上新建属性，遮蔽类变量
print(c1.total, Counter.total)   # 99 2
```

**共享可变类变量的坑**：

```python
class Config:
    items = []                 # ❌ 所有实例共享同一个列表

a, b = Config(), Config()
a.items.append(1)
print(b.items)                 # [1]  ← 被污染

class Config2:
    def __init__(self):
        self.items = []        # ✅ 每个实例独立
```

## 11.3 继承与 super()

```python
class Animal:
    def __init__(self, name: str):
        self.name = name

    def speak(self) -> str:
        raise NotImplementedError

class Dog(Animal):
    def __init__(self, name: str, breed: str):
        super().__init__(name)          # 调用父类初始化
        self.breed = breed

    def speak(self) -> str:
        return "汪"

d = Dog("旺财", "柴犬")
print(d.speak(), d.name, d.breed)       # 汪 旺财 柴犬
print(isinstance(d, Animal))            # True
print(Dog.__mro__)                      # (<class Dog>, <class Animal>, <class object>)
```

- 方法解析顺序（MRO）由 C3 线性化算法决定，可用 `__mro__` 查看。
- 多继承：`class C(A, B)`，`super()` 沿 MRO 找“下一个”类，因此协作式多继承里每层都应调用 `super()`。
- 不要硬编码 `Animal.__init__(self, ...)`（多重继承会出错）。

## 11.4 访问控制（约定而非强制）

```python
class Account:
    def __init__(self):
        self.owner = "Alice"          # 公开
        self._balance = 0              # 约定：内部使用，别直接依赖
        self.__secret = "token"        # 名字改写为 _Account__secret

a = Account()
print(a._balance)          # 语法上能访问（警告）
print(a.__secret)          # ❌ AttributeError
print(a._Account__secret)  # 能访问，但不该这么做
```

Python 的哲学：**我们都是成年人**（用命名与文档表达意图，而不是语言强制）。

## 11.5 property：受控属性访问

```python
class Temperature:
    def __init__(self, celsius: float = 0):
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        """摄氏度（读）。"""
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("低于绝对零度")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        return self._celsius * 9 / 5 + 32

t = Temperature()
t.celsius = 25          # 触发 setter 校验
print(t.fahrenheit)     # 77.0
# t.celsius = -300      # ValueError
```

好处：先写普通属性，之后需要校验/计算时**不用改调用方代码**。

## 11.6 classmethod / staticmethod

```python
class Date:
    def __init__(self, year: int, month: int, day: int):
        self.year, self.month, self.day = year, month, day

    @classmethod
    def from_string(cls, text: str) -> "Date":
        """工厂方法：收到 cls，子类调用会返回子类实例。"""
        y, m, d = map(int, text.split("-"))
        return cls(y, m, d)

    @staticmethod
    def is_leap(year: int) -> bool:
        """工具函数：与实例/类无关，只是逻辑上属于这里。"""
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

print(Date.from_string("2024-05-01").year)   # 2024
print(Date.is_leap(2024))                    # True
```

| 装饰器 | 第一个参数 | 用途 |
| --- | --- | --- |
| 无 | `self` | 操作实例 |
| `@classmethod` | `cls` | 工厂方法、替代构造函数 |
| `@staticmethod` | 无 | 命名空间内的工具函数 |

## 11.7 魔术方法（dunder methods）

```python
class Vector:
    def __init__(self, x: float, y: float):
        self.x, self.y = x, y

    def __repr__(self):                  # 调试
        return f"Vector({self.x}, {self.y})"

    def __eq__(self, other):             # == 
        if not isinstance(other, Vector):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):                  # 可放进 set / 作 dict 键
        return hash((self.x, self.y))

    def __add__(self, other):            # +
        return Vector(self.x + other.x, self.y + other.y)

    def __mul__(self, k: float):         # *
        return Vector(self.x * k, self.y * k)

    def __len__(self):                   # len()
        return 2

    def __iter__(self):                  # for x in v
        yield self.x
        yield self.y

    def __getitem__(self, i):            # v[0]
        return (self.x, self.y)[i]

    def __call__(self, k):               # v(3)
        return self * k

v = Vector(1, 2)
print(v + Vector(3, 4))      # Vector(4, 6)
print(v * 2)                 # Vector(2, 4)
print(list(v), len(v), v[1]) # [1, 2] 2 2
print({v, Vector(1, 2)})     # 只有一个元素（因为 __eq__ + __hash__）
```

**重要联动**：一旦定义 `__eq__`，Python 会把 `__hash__` 设为 `None`（对象不再可哈希），需要可哈希就显式实现。

常用魔术方法表：

| 方法 | 触发 |
| --- | --- |
| `__init__` / `__new__` | 创建实例 |
| `__repr__` / `__str__` | `repr()` / `str()` |
| `__eq__` / `__lt__` / `__hash__` | 比较、哈希 |
| `__len__` / `__bool__` | `len()` / 真值 |
| `__getitem__` / `__setitem__` | `obj[k]` |
| `__iter__` / `__next__` | 迭代 |
| `__call__` | `obj()` |
| `__enter__` / `__exit__` | `with` 语句 |
| `__add__` / `__mul__` | 运算符重载 |

## 11.8 dataclass：少写样板代码

```python
from dataclasses import dataclass, field, asdict

@dataclass
class Point:
    x: float
    y: float
    tags: list[str] = field(default_factory=list)   # 可变默认值必须这样写

    def norm(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

p = Point(3, 4)
print(p)                       # Point(x=3, y=4, tags=[])
print(p == Point(3, 4))        # True（自动生成 __eq__）
print(asdict(p))               # {'x': 3, 'y': 4, 'tags': []}

@dataclass(frozen=True)        # 不可变 + 可哈希
class Config:
    host: str = "localhost"
    port: int = 8000

@dataclass(order=True)         # 生成排序方法
class Version:
    major: int
    minor: int
```

对比普通类：自动生成 `__init__`、`__repr__`、`__eq__`，适合“主要用来装数据”的类。

## 11.9 抽象基类与 Protocol

```python
from abc import ABC, abstractmethod

class Repository(ABC):
    @abstractmethod
    def get(self, key: str) -> str: ...

    @abstractmethod
    def save(self, key: str, value: str) -> None: ...

# Repository()          # ❌ TypeError: Can't instantiate abstract class

class MemoryRepo(Repository):
    def __init__(self):
        self._data = {}
    def get(self, key): return self._data[key]
    def save(self, key, value): self._data[key] = value
```

结构化类型（更接近 TS 的 interface）：

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class HasArea(Protocol):
    def area(self) -> float: ...

class Circle:
    def __init__(self, r): self.r = r
    def area(self) -> float: return 3.14 * self.r ** 2

def print_area(shape: HasArea) -> None:
    print(shape.area())

print_area(Circle(1))               # 不需要显式继承
print(isinstance(Circle(1), HasArea))   # True
```

## 11.10 与 JS/TS 对照

| 需求 | TypeScript | Python |
| --- | --- | --- |
| 定义类 | `class A { constructor() {} }` | `class A: def __init__(self): ...` |
| 实例化 | `new A()` | `A()` |
| this | `this` | `self`（显式参数） |
| 接口 | `interface` / `implements` | `Protocol` / `ABC` |
| 访问修饰符 | `private` / `protected`（编译期） | `_x` / `__x`（约定） |
| getter/setter | `get x() {}` / `set x(v) {}` | `@property` / `@x.setter` |
| 静态成员 | `static x` | 类变量 / `@staticmethod` |
| 继承 | `extends` / `super()` | `(Base)` / `super()` |
| 抽象类 | `abstract class` | `ABC` + `@abstractmethod` |
| 数据类 | 对象字面量 / interface | `@dataclass` |
| 运算符重载 | 不支持 | 魔术方法 |

## 11.11 小练习

```python
# 1. 带校验的 BankAccount
class BankAccount:
    def __init__(self, balance: float = 0):
        self._balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("金额必须为正")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        if amount > self._balance:
            raise ValueError("余额不足")
        self._balance -= amount

# 2. 用 dataclass 表示 API 响应
@dataclass
class User:
    id: int
    name: str
    email: str | None = None
```

- [ ] 我能解释 `self` 是什么、为什么是显式参数。
- [ ] 我知道 `__eq__` 与 `__hash__` 的联动。
- [ ] 我知道 `__str__` 与 `__repr__` 的分工。
- [ ] 我能写出 `@property` + setter 的校验模式。
- [ ] 我知道 `@classmethod` 的工厂方法用途。
