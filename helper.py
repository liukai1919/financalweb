import yfinance as yf

def get_stock_info(ticker: str):
    """
    获取股票的基本信息和历史数据
    """
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="5d")
    return info, hist 