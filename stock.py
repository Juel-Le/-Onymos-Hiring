# Simulation constants
NUM_TICKERS = 1024        # Total number of tickers (each ticker corresponds to one slot)
DEFAULT_NUM_WORKERS = 5   # Number of simulated traders (workers)
DEFAULT_TRANSACTIONS = 10 # Number of transactions per worker

# Global order book: an array of length NUM_TICKERS, each element is [buy_orders, sell_orders]
order_books = []
i = 0
while i < NUM_TICKERS:
    order_books.append([[], []])
    i += 1

# Linear Congruential Generator (LCG) parameters
LCG_MULTIPLIER = 1103515245
LCG_INCREMENT = 12345
LCG_MODULUS = 2**31

def ticker_to_index(ticker_symbol):
    """
    Convert ticker_symbol to an index.
    Assumes ticker_symbol is in the format "TICKER{number}".
    """
    num_part = ticker_symbol.replace("TICKER", "")
    return int(num_part) % NUM_TICKERS

def print_orders():
    """
    Print all orders (both Buy and Sell) for tickers that have orders.
    """
    print("\n----- Current Orders -----")
    i = 0
    while i < NUM_TICKERS:
        buy_orders = order_books[i][0]
        sell_orders = order_books[i][1]
        if buy_orders or sell_orders:
            print("Ticker: TICKER" + str(i))
            print("  Buy Orders:", buy_orders)
            print("  Sell Orders:", sell_orders)
        i += 1
    print("--------------------------\n")

def addOrder(order_type, ticker_symbol, quantity, price):
    """
    Add an order to the order book for ticker_symbol,
    then print the updated order book and attempt to match orders.
    """
    index = ticker_to_index(ticker_symbol)
    order = [order_type, ticker_symbol, quantity, price]
    print("Adding order:", order)
    if order_type == "Buy":
        order_books[index][0].append(order)
        # Sort Buy orders in descending order by price (higher price first)
        order_books[index][0].sort(key=lambda x: -x[3])
    elif order_type == "Sell":
        order_books[index][1].append(order)
        # Sort Sell orders in ascending order by price (lower price first)
        order_books[index][1].sort(key=lambda x: x[3])
    print_orders()
    matchOrder(ticker_symbol)

def matchOrder(ticker_symbol):
    """
    Match orders for the given ticker_symbol.
    If the best Buy order's price is >= the best Sell order's price,
    perform the match (supporting partial fills).
    """
    index = ticker_to_index(ticker_symbol)
    print("Matching orders for", ticker_symbol)
    buy_orders = order_books[index][0]
    sell_orders = order_books[index][1]
    while buy_orders and sell_orders:
        best_buy = buy_orders[0]
        best_sell = sell_orders[0]
        if best_buy[3] >= best_sell[3]:
            # Determine trade quantity: the smaller of the two orders
            trade_qty = best_buy[2] if best_buy[2] < best_sell[2] else best_sell[2]
            print("Matched:", best_buy, "with", best_sell, "for", trade_qty, "units")
            best_buy[2] -= trade_qty
            best_sell[2] -= trade_qty
            if best_buy[2] == 0:
                buy_orders.pop(0)
            if best_sell[2] == 0:
                sell_orders.pop(0)
        else:
            break
    print_orders()

def worker(num_transactions, tickers, worker_id):
    """
    Simulate a single trader's (worker's) actions.
    Each worker uses its own local seed (based on worker_id) so that its random sequence is independent.
    Instead of using the low bit (which较差), we choose:
      if local_seed < (LCG_MODULUS // 2): choose "Buy", else "Sell"
    """
    local_seed = 123456789 + worker_id  # Initialize local seed differently per worker
    txn = 0
    while txn < num_transactions:
        # Update local_seed and decide order type based on high-order randomness
        local_seed = (LCG_MULTIPLIER * local_seed + LCG_INCREMENT) % LCG_MODULUS
        if local_seed < (LCG_MODULUS // 2):
            order_type = "Buy"
        else:
            order_type = "Sell"
        # Update local_seed for ticker selection
        local_seed = (LCG_MULTIPLIER * local_seed + LCG_INCREMENT) % LCG_MODULUS
        ticker_index = local_seed % len(tickers)
        ticker_symbol = tickers[ticker_index]
        # Update local_seed for quantity
        local_seed = (LCG_MULTIPLIER * local_seed + LCG_INCREMENT) % LCG_MODULUS
        quantity = local_seed % 100 + 1
        # Update local_seed for price
        local_seed = (LCG_MULTIPLIER * local_seed + LCG_INCREMENT) % LCG_MODULUS
        price = local_seed % 991 + 10
        print("Worker", worker_id, "order:", order_type, ticker_symbol, quantity, price)
        addOrder(order_type, ticker_symbol, quantity, price)
        matchOrder(ticker_symbol)
        txn += 1
        yield

def simulate_transactions(num_transactions, num_workers=DEFAULT_NUM_WORKERS):
    """
    Simulate transactions by multiple traders.
    Each worker (trader) performs a series of transactions.
    """
    tickers = []
    i = 0
    while i < NUM_TICKERS:
        tickers.append("TICKER" + str(i))
        i += 1
    workers = []
    for worker_id in range(num_workers):
        workers.append(worker(num_transactions, tickers, worker_id))
    active = True
    while active:
        active = False
        j = 0
        while j < len(workers):
            try:
                next(workers[j])
                active = True
            except StopIteration:
                pass
            j += 1

# Run the simulation
simulate_transactions(DEFAULT_TRANSACTIONS, DEFAULT_NUM_WORKERS)
