Using CCXT for an arbitrage bot is an excellent choice since it abstracts away a lot of the exchange-specific WebSocket handling and provides unified APIs across exchanges. 

### Threading Architecture
- One or more threads receiving the realtime exchange data and feeding it to a mutex protected store.
- One arbitrage thread scanning the store for opportunities and upon identifying one, starting the trading thread.
- One or more trading threads executing trades.

### Threading Architecture Downsides
- **Threading Overhead**: Python threads are lightweight but still incur management costs. If you're watching many assets, spawning a thread per asset could lead to high resource use without proportional gains.
- **Data Consistency**: A shared store is simple but prone to inconsistencies if updates arrive mid-iteration. You'd need `threading.Lock()` everywhere, which can create bottlenecks.
- **Latency**: Polling/iterating in a loop might miss fleeting opportunities if the loop isn't tight enough or if threads get starved.
- **Scalability**: For high-frequency arbitrage (e.g., cross-exchange or triangular), you need sub-millisecond responses, which threads alone might not guarantee.

### Async Architecture
- Everything cooperatively runs in the single thread using the Python `asyncio`.
- One async function per exchange receives the realtime exchange data and feeds the store or maybe an `asyncio.Queue`. This can timestamp.
- One async arbitrage function (or more?) checking for opportunities and strategically using `asyncio.sleep` to yield execution. If opportunities identified, feed an `asyncio.Queue`.
- One or more async trading functions executing on opportunities from the opportunities queue.
- This has better latency and is more GIL friendly.

### Async Architecture Downsides
- Complexity - missing an `await` here or there can have really bad outcomes but this can be mitigated via `pylint pylint-asyncio`.
- Difficult to follow in the debugger which is the biggest downside for me. Can be partially mitigated by extensive logging and `asyncio.run_with_timeout`.
- This is running in a single thread so any heavy computation will kill latency. Note that WebSockets don't negatively impact this architecture. This problem is Python specific too.


#### Further Considerations   
- For simple arbitrage checks (e.g., price differences), keep it async. For complex logic, offload to a process pool, maybe via `concurrent.futures.ProcessPoolExecutor`. Cython also for native crunching?

- Define arbitrage rules modularly (e.g., as functions or classes per strategy). Use efficient data structures like `collections.deque` for time-series prices (to keep only recent data) or a lightweight in-memory store like Redis if it grows.

- Add metrics (e.g., via `prometheus` or simple logging) to track latency and missed opportunities.

- Integrate `pandas` for quick analysis in the detector, or `redis` for distributed storage if running on multiple machines.

