# 06 列表、元组、字典、集合

> 主题标签：`collections` ｜ 对应考试主题：列表/元组/字典/集合

## 6.1 四种内置容器对比

| 容器 | 字面量 | 有序 | 可变 | 可哈希 | 适用场景 |
| --- | --- | --- | --- | --- | --- |
| `list` | `[1, 2]` | ✅ | ✅ | ❌ | 有序集合、栈/队列 |
| `tuple` | `(1, 2)` | ✅ | ❌ | ✅（元素可哈希时） | 固定结构、函数多返回值、dict 键 |
| `dict` | `{"a": 1}` | ✅（3.7+插入序） | ✅ | ❌ | 键值映射、JSON |
| `set` | `{1, 2}` | ❌ | ✅ | ❌ | 去重、成员判断、集合运算 |
| `frozenset` | `frozenset({1})` | ❌ | ❌ | ✅ | 需要哈希的集合 |

## 6.2 列表 list

```python
nums = [3, 1, 2]
nums.append(4)            # 末尾追加一个元素        -> [3,1,2,4]
nums.extend([5, 6])       # 展开追加多个            -> [3,1,2,4,5,6]
nums.insert(0, 0)         # 在索引 0 插入           -> [0,3,1,...]
nums.remove(3)            # 按值删除第一个匹配项（找不到 ValueError）
last = nums.pop()         # 弹出并返回末尾（O(1)）
first = nums.pop(0)       # 弹出并返回头部（O(n)）
del nums[0]               # 按索引删除，无返回值
nums.clear()              # 清空
nums.reverse()            # 原地反转，返回 None
nums.sort()               # 原地升序，返回 None
nums.sort(reverse=True)   # 降序
nums.sort(key=lambda x: abs(x))   # 自定义 key
nums.sort(key=lambda x: (-x[1], x[0]))  # 多级排序
```

查找与统计：

```python
nums = [1, 2, 2, 3]
print(nums.index(2))       # 1   第一个匹配的索引
print(nums.count(2))       # 2
print(2 in nums)           # True
print(len(nums))           # 4
```

`sort()` vs `sorted()`：

```python
a = [3, 1, 2]
b = a.sort()          # b 是 None！a 变成 [1, 2, 3]
c = sorted(a)         # c 是新列表，a 不变
```

复制：

```python
d = a[:]              # 浅拷贝（切片）
e = a.copy()
f = list(a)
g = a[:]
import copy
h = copy.deepcopy(a)  # 深拷贝（嵌套对象也复制）
```

`append` vs `extend` 的经典区别：

```python
a = [1, 2]
a.append([3, 4])   # [1, 2, [3, 4]]   整体作为一个元素
a = [1, 2]
a.extend([3, 4])   # [1, 2, 3, 4]     逐个追加
a = [1, 2]
a += [3, 4]        # 同 extend（原地修改）
```

## 6.3 列表推导式（详见第 9 章）

```python
squares = [x * x for x in range(5)]          # [0, 1, 4, 9, 16]
evens = [x for x in range(10) if x % 2 == 0]
matrix = [[0] * 3 for _ in range(2)]         # 每个内层都是独立对象
flat = [x for row in matrix for x in row]    # 展平
```

**陷阱**：

```python
bad = [[0] * 2] * 3      # 三行是同一个列表的引用
bad[0][0] = 1
print(bad)               # [[1,0],[1,0],[1,0]]  ← 全都变了
```

## 6.4 元组 tuple

```python
t = (1, 2, 3)
one = (1,)            # 单元素必须有逗号，否则是 int
empty = ()
print(t[0], t[-1], t[1:])   # 支持索引与切片
# t[0] = 9            # TypeError：不可变

a, b, c = t           # 解包
first, *rest = t      # first=1, rest=[2, 3]
x, y = y, x           # 交换变量（背后是元组打包 + 解包）

# 具名元组：给字段起名字
from collections import namedtuple
Point = namedtuple("Point", "x y")
p = Point(1, 2)
print(p.x, p.y, p[0])   # 1 2 1

# 现代替代：dataclass（见第 11 章）
```

元组可作 dict 的键：

```python
grid = {(0, 0): "start", (1, 2): "goal"}
print(grid[(0, 0)])
```

## 6.5 字典 dict

```python
user = {"name": "Alice", "age": 30}
user["city"] = "Beijing"          # 新增/覆盖
print(user.get("email"))          # None    键不存在不报错
print(user.get("email", "无"))    # '无'     带默认值
print("name" in user)             # True    判断键
del user["city"]                  # 删除键（不存在会 KeyError）
age = user.pop("age", 0)          # 弹出并返回，带默认值
user.update({"age": 31, "vip": True})   # 批量更新
user.setdefault("tags", []).append("py")  # 键不存在则写入默认值并返回

print(list(user.keys()))          # 键列表
print(list(user.values()))        # 值列表
print(list(user.items()))         # [(k, v), ...]
for k, v in user.items():         # 遍历
    print(k, v)

# 合并
a = {"x": 1}; b = {"y": 2}
print({**a, **b})                 # {'x': 1, 'y': 2}（后者覆盖同名键）
print(a | b)                      # 3.9+ 操作符写法
```

字典推导式：

```python
sq = {x: x * x for x in range(3)}         # {0:0, 1:1, 2:4}
upper = {k.upper(): v for k, v in a.items()}
flipped = {v: k for k, v in a.items()}
```

嵌套访问技巧：

```python
data = {"user": {"profile": {"name": "Alice"}}}
name = data.get("user", {}).get("profile", {}).get("name", "匿名")
```

排序与遍历顺序：

```python
d = {"b": 2, "a": 1}
for k in sorted(d):                       # 按键排序
    ...
for k, v in sorted(d.items(), key=lambda kv: kv[1], reverse=True):
    print(k, v)                           # 按值降序
```

## 6.6 集合 set

```python
s = {1, 2, 3}
s.add(4)              # 加一个元素
s.discard(4)          # 删除（不存在也不报错）
s.remove(3)           # 删除（不存在抛 KeyError）
print(1 in s)         # True    O(1) 平均
print({1, 2, 2, 3})   # {1, 2, 3}  自动去重
empty = set()         # 空集合！{} 是空字典
print(type({}))       # <class 'dict'>

a, b = {1, 2, 3}, {2, 3, 4}
print(a & b)          # {2, 3}        交集
print(a | b)          # {1, 2, 3, 4}  并集
print(a - b)          # {1}           差集
print(a ^ b)          # {1, 4}        对称差
print(a <= b)         # False         子集判断
print(a.isdisjoint({9}))  # True      无交集

# 推导式
print({x % 3 for x in range(10)})   # {0, 1, 2}
```

去重并保持顺序：

```python
items = [3, 1, 3, 2]
uniq = list(dict.fromkeys(items))   # [3, 1, 2]
```

## 6.7 常用工具：Counter / defaultdict / deque

```python
from collections import Counter, defaultdict, deque

c = Counter("abracadabra")
print(c.most_common(2))     # [('a', 5), ('b', 2)]
print(c["a"], c["z"])       # 5 0（不存在的键返回 0，而不是 KeyError）

groups = defaultdict(list)
for name, dept in [("A", "dev"), ("B", "ops"), ("C", "dev")]:
    groups[dept].append(name)     # 不需要先判断键是否存在
print(dict(groups))               # {'dev': ['A', 'C'], 'ops': ['B']}

q = deque([1, 2, 3])
q.appendleft(0)     # O(1) 头部插入
q.pop()             # O(1) 尾部弹出
```

## 6.8 复制语义（重点）

```python
import copy

original = [1, [2, 3]]
alias = original              # 别名：同一个对象
shallow = original.copy()     # 浅拷贝：外层新对象，内层仍共享
deep = copy.deepcopy(original)# 深拷贝：完全独立

alias.append(4)               # 影响 original
shallow[1].append(99)         # 也影响 original[1]！
deep[1].append(0)             # 不影响 original

print(original)               # [1, [2, 3, 99], 4]
```

用 `id()` 验证身份：

```python
print(id(original) == id(alias))    # True
print(id(original) == id(shallow))  # False
```

## 6.9 与 JS/TS 对照

| 需求 | TypeScript | Python |
| --- | --- | --- |
| 数组追加 | `arr.push(x)` | `arr.append(x)` |
| 合并数组 | `arr.concat(other)` | `arr.extend(other)` / `arr + other` |
| 删除末尾 | `arr.pop()` | `arr.pop()` |
| 按值删除 | `arr.splice(i, 1)` / `filter` | `arr.remove(x)` |
| 排序（新数组） | `arr.sort()`（原地）/ `[...arr].sort()` | `arr.sort()`（原地）/ `sorted(arr)` |
| 长度 | `arr.length` | `len(arr)` |
| 查找索引 | `arr.indexOf(x)` | `arr.index(x)`（无则 ValueError） |
| 包含 | `arr.includes(x)` | `x in arr` |
| 映射/过滤 | `map` / `filter` | 推导式 / `map` / `filter` |
| 字典/对象 | `{a: 1}` / `Map` | `{"a": 1}`（键可为任意可哈希对象） |
| 键是否存在 | `"k" in obj`（含原型链） | `"k" in d`（仅自身键） |
| 集合 | `new Set()` | `{1, 2}` / `set()` |
| 不可变列表 | `as const` / `readonly T[]` | `tuple` |

## 6.10 小练习

```python
# 1. 统计词频
from collections import Counter
def top_words(text: str, n: int = 3):
    return Counter(text.split()).most_common(n)

# 2. 按部门分组
from collections import defaultdict
def group_by(rows, key):
    result = defaultdict(list)
    for row in rows:
        result[row[key]].append(row)
    return dict(result)

# 3. 安全地取嵌套值
def dig(data, *keys, default=None):
    cur = data
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur
```

- [ ] 我知道 `append` 与 `extend` 的区别。
- [ ] 我能解释 `[[0]*2]*3` 的问题。
- [ ] 我知道排序用 `sorted` 而 `list.sort()` 返回 `None`。
- [ ] 我知道 `{}` 是字典，空集合要写 `set()`。
- [ ] 我能说清浅拷贝与深拷贝的差别。
