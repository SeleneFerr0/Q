"""
"""
# import
from jqdata import *

MA_WIN_1 = 10
MA_WIN_2 = 30


RISK_RATIO = 0.001

STOCK_RISK_RATIO = 0.01



def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    # log.set_level('order', 'error')
    
    # brokeage fee
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')

    # scheduled run
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
    
    g.stock_pool = get_index_stocks("000016.XSHG", date=context.current_dt)
    g.init_cash = context.portfolio.starting_cash  #initial 

# before the market opens
def before_market_open(context):
    look_ahead_n = max(MA_WIN_1, MA_WIN_2) + 1
    g.up_cross_signaled = set()
    g.down_cross_signaled = set()
    for code in g.stock_pool:
        df = attribute_history(code, look_ahead_n, "1d", ["close"], skip_paused=True)  
        if len(df) != look_ahead_n:
            continue
        close = df["close"]
        ma_short = pd.rolling_mean(close, MA_WIN_1)  #
        ma_long = pd.rolling_mean(close, MA_WIN_2)   # 
        uc_flags = (ma_short.shift(1) <= ma_long.shift(1)) & (ma_short > ma_long)  #
        dc_flags = (ma_short.shift(1) >= ma_long.shift(1)) & (ma_short < ma_long)  #
        if uc_flags.iloc[-1]:
            g.up_cross_signaled.add(code)
        if dc_flags.iloc[-1]:
            g.down_cross_signaled.add(code)


def market_open(context):
    cur_dt = context.current_dt.date()
    p = context.portfolio  
    current_data = get_current_data()

   
    for code, pos in p.positions.items():
        if code in g.down_cross_signaled:
            order_target(code, 0)


    for code in g.up_cross_signaled:
        if code not in p.positions:
            if current_data[code].paused:
                continue
           
            num_to_buy = (g.init_cash * RISK_RATIO) / (current_data[code].last_price * STOCK_RISK_RATIO) 
            order(code, num_to_buy)

def after_market_close(context):
    p = context.portfolio
    pos_level = p.positions_value / p.total_value
    record(pos_level=pos_level)
