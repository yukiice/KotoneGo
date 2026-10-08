# 17 异步编程（asyncio）

> 主题标签：`async` ｜ 对应考试主题：异步编程
> 如果你写过 `async/await` + `Promise.all`，本章主要讲“Python 的事件循环与陷阱”。

## 17.1 核心概念

| 概念 | 说明 |
| --- | --- |
| 协程（coroutine） | `async def` 定义的函数，调用后返回协程对象 |
| 事件循环（event loop） | 单线程调度器，负责在 IO 等待时切换任务 |
| `await` | 挂起当前协程，把控制权交回事件循环，等结果就绪再恢复 |
| Task | 被事件循环调度的协程包装（`asyncio.create_task`） |
| 并发（concurrency） | 单线程交替执行多个任务（IO 密集友好） |
| 并行（parallelism） | 真正同时执行（多进程 / 多核） |

**一句话**：asyncio 解决的是“等 IO 时不要干等”，它不会让 CPU 计算变快。

## 17.2 最小示例

```python
import asyncio

async def say(name: str, delay: float) -> str:
    print(f"{name} 开始")
    await asyncio.sleep(delay)          # 让出控制权（不是 time.sleep！）
    print(f"{name} 结束")
    return f"{name} 完成"

async def main() -> None:
    result = await say("A", 1)
    print(result)

asyncio.run(main())                      # 程序入口
```

调用 `say("A", 1)` **不会执行**函数体，只创建协程对象：

```python
coro = say("A", 1)
print(coro)          # <coroutine object say at 0x...>
# 不 await 就丢弃 -> RuntimeWarning: coroutine 'say' was never awaited
```

## 17.3 并发：gather / TaskGroup

```python
import asyncio, time

async def fetch(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name

async def serial():
    start = time.perf_counter()
    for name, d in [("A", 1), ("B", 1), ("C", 1)]:
        await fetch(name, d)
    print(f"串行 {time.perf_counter() - start:.2f}s")     # ~3.0s

async def concurrent():
    start = time.perf_counter()
    results = await asyncio.gather(
        fetch("A", 1), fetch("B", 1), fetch("C", 1)
    )
    print(results, f"{time.perf_counter() - start:.2f}s")  # ['A','B','C'] ~1.0s

# 3.11+ 更推荐 TaskGroup（异常处理更清晰）
async def with_task_group():
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch(n, 1)) for n in "ABC"]
    print([t.result() for t in tasks])
```

| 方式 | 特点 |
| --- | --- |
| `await` 逐个 | 串行 |
| `asyncio.gather` | 并发，返回结果列表（顺序与传入一致） |
| `asyncio.TaskGroup` | 并发 + 结构化取消与异常聚合（推荐） |
| `asyncio.as_completed` | 谁先完成先处理 |

## 17.4 取消与超时

```python
import asyncio

async def slow() -> str:
    await asyncio.sleep(10)
    return "done"

async def main() -> None:
    try:
        result = await asyncio.wait_for(slow(), timeout=1.0)
    except asyncio.TimeoutError:
        print("超时了")

    # 3.11+ 更简洁
    async with asyncio.timeout(1.0):
        await slow()
```

手动取消：

```python
task = asyncio.create_task(slow())
await asyncio.sleep(0.1)
task.cancel()
try:
    await task
except asyncio.CancelledError:
    print("任务被取消")
```

清理代码要能响应取消（`finally` 或 `async with`），不要在 `finally` 里吞掉 `CancelledError`。

## 17.5 同步阻塞是头号杀手

```python
import time, requests

async def bad():
    time.sleep(1)                    # ❌ 阻塞整个事件循环
    requests.get("https://example.com")   # ❌ 同步网络 IO

async def good():
    await asyncio.sleep(1)           # ✅
    import httpx
    async with httpx.AsyncClient() as client:
        await client.get("https://example.com")   # ✅
```

如果必须调用同步阻塞函数：

```python
import asyncio

def blocking_io() -> str:
    time.sleep(2)
    return "ok"

async def main():
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, blocking_io)   # 丢到线程池
    print(result)
```

小提醒：`asyncio.to_thread(func, *args)`（3.9+）是 `run_in_executor` 的简洁包装。

## 17.6 异步迭代与异步上下文管理器

```python
async def aiter_lines(urls: list[str]):
    for url in urls:
        await asyncio.sleep(0.1)
        yield url.upper()

async def main():
    async for line in aiter_lines(["a", "b"]):     # 异步生成器
        print(line)

import httpx
async def with_client():
    async with httpx.AsyncClient() as client:      # 异步上下文管理器
        r = await client.get("https://example.com")
        print(r.status_code)
```

异步生成器 + 推导式（3.6+）：

```python
results = [x async for x in aiter_lines(["a", "b"])]
```

## 17.7 并发控制：信号量

```python
import asyncio

async def limited_worker(sem: asyncio.Semaphore, i: int):
    async with sem:                     # 最多同时 N 个
        await asyncio.sleep(0.5)
        return i

async def main():
    sem = asyncio.Semaphore(5)
    results = await asyncio.gather(*(limited_worker(sem, i) for i in range(50)))
    print(len(results))
```

队列模式（生产者/消费者）：

```python
async def producer(q: asyncio.Queue) -> None:
    for i in range(10):
        await q.put(i)
    await q.put(None)

async def consumer(q: asyncio.Queue) -> None:
    while (item := await q.get()) is not None:
        print("处理", item)
        q.task_done()

async def main():
    q: asyncio.Queue = asyncio.Queue(maxsize=3)
    await asyncio.gather(producer(q), consumer(q))
```

## 17.8 何时用 asyncio / 线程 / 进程

| 场景 | 方案 |
| --- | --- |
| 大量 IO 等待（HTTP、DB、文件） | `asyncio` + 异步库（httpx/aiohttp/asyncpg） |
| 少量阻塞 IO、已有同步库 | `asyncio.to_thread` 或 `concurrent.futures.ThreadPoolExecutor` |
| CPU 密集（数值计算、图像处理） | `multiprocessing` / `ProcessPoolExecutor` / numpy / C 扩展 |
| 需要绝对避免 GIL | 多进程 |

关于 GIL：CPython 同一时刻只有一个线程执行字节码，所以“多线程不会加速纯 Python 计算”，但 IO 阻塞时会释放 GIL，因此线程对 IO 仍有效。

## 17.9 FastAPI 里的异步（实用视角）

```python
from fastapi import FastAPI
import httpx

app = FastAPI()

@app.get("/slow")
async def slow_endpoint():
    async with httpx.AsyncClient() as client:      # 异步 IO：不阻塞事件循环
        r = await client.get("https://example.com")
    return {"len": len(r.text)}

@app.get("/cpu")
def cpu_endpoint():              # 用 def（同步）时 FastAPI 会丢到线程池执行
    return {"sum": sum(range(10 ** 6))}
```

规则：**在 `async def` 里做阻塞调用会拖垮整个服务**；如果不会写异步，就用普通 `def`，框架会在线程池里跑。

## 17.10 常见错误清单

| 错误 | 后果 | 修复 |
| --- | --- | --- |
| 忘记 `await` | 协程不执行（静默 bug） | 加 `await` 或 `create_task` |
| `async def` 里用 `time.sleep`/`requests` | 阻塞事件循环 | 改异步或 `to_thread` |
| 在同步函数里 `await` | `SyntaxError` | 改成 `async def` |
| 用 `asyncio.run` 在已运行的事件循环里 | `RuntimeError` | 用 `await` 或 `nest_asyncio`（尽量重构） |
| 未处理的 Task 异常 | “Task exception was never retrieved” | 保留引用并 `await`，或用 TaskGroup |
| 共享可变全局状态 | 竞态 | 用队列/Lock，或避免共享 |
| 无限生成器/无超时请求 | 卡死 | 加 `asyncio.timeout` |

## 17.11 与 JS/TS 对照

| 概念 | JavaScript | Python |
| --- | --- | --- |
| 定义异步函数 | `async function f() {}` | `async def f():` |
| 等待 | `await p` | `await coro` |
| 并发等待 | `Promise.all([...])` | `asyncio.gather(...)` / `TaskGroup` |
| 竞速 | `Promise.race` | `asyncio.wait(FIRST_COMPLETED)` |
| 事件循环 | 浏览器/Node 内建 | `asyncio.run()` 显式管理 |
| 定时器 | `setTimeout` | `asyncio.sleep` / `loop.call_later` |
| 队列 | 无（用库） | `asyncio.Queue` |
| 阻塞风险 | 同步 CPU 代码阻塞 UI | 同步阻塞代码卡住事件循环 |
| 线程/进程 | Worker + 子进程 | `to_thread` / `multiprocessing` |

## 17.12 小练习

```python
import asyncio
import time

async def download(name: str, delay: float) -> dict:
    await asyncio.sleep(delay)
    return {"name": name, "ok": True}

async def download_all(tasks: list[tuple[str, float]]) -> list[dict]:
    """并发下载，限制最大并发 3，失败不中断其它任务。"""
    sem = asyncio.Semaphore(3)

    async def one(name: str, delay: float) -> dict:
        async with sem:
            try:
                return await asyncio.wait_for(download(name, delay), timeout=5)
            except asyncio.TimeoutError:
                return {"name": name, "ok": False, "error": "timeout"}

    start = time.perf_counter()
    results = await asyncio.gather(*(one(n, d) for n, d in tasks))
    print(f"总耗时 {time.perf_counter() - start:.2f}s")
    return results

if __name__ == "__main__":
    asyncio.run(download_all([("a", 1), ("b", 1), ("c", 1), ("d", 2)]))
```

- [ ] 我知道调用协程函数不会执行函数体。
- [ ] 我知道 `time.sleep` 会阻塞事件循环。
- [ ] 我能用 `gather` 把串行改成并发。
- [ ] 我知道 CPU 密集应该用多进程。
- [ ] 我知道 FastAPI 里 `def` 与 `async def` 的处理差异。
