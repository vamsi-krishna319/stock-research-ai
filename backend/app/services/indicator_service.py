# # """
# # Technical indicator computation using pandas-ta on top of
# # Yahoo Finance OHLCV history.
# # """
# # import logging

# # import pandas as pd
# # import pandas_ta as ta

# # logger = logging.getLogger(__name__)


# # def compute_indicators(history: pd.DataFrame) -> dict:
# #     """
# #     Compute a standard set of technical indicators from an OHLCV
# #     DataFrame (as returned by yfinance). Returns the latest values
# #     plus a short recent-history slice for charting.
# #     """
# #     if history.empty:
# #         return {"error": "No price history available."}

# #     df = history.copy()
# #     df.columns = [c.lower() for c in df.columns]

# #     try:
# #         df.ta.rsi(length=14, append=True)
# #         df.ta.macd(fast=12, slow=26, signal=9, append=True)
# #         df.ta.sma(length=20, append=True)
# #         df.ta.sma(length=50, append=True)
# #         df.ta.ema(length=20, append=True)
# #         df.ta.bbands(length=20, append=True)
# #         df.ta.adx(length=14, append=True)
# #     except Exception as exc:  # noqa: BLE001
# #         logger.error("pandas-ta computation failed: %s", exc)
# #         return {"error": f"Indicator computation failed: {exc}"}

# #     latest = df.iloc[-1]

# #     def safe(col):
# #         return None if col not in df.columns or pd.isna(latest.get(col)) else round(float(latest[col]), 4)

# #     result = {
# #         "close": safe("close"),
# #         "rsi_14": safe("rsi_14"),
# #         "macd": safe("macd_12_26_9"),
# #         "macd_signal": safe("macds_12_26_9"),
# #         "macd_hist": safe("macdh_12_26_9"),
# #         "sma_20": safe("sma_20"),
# #         "sma_50": safe("sma_50"),
# #         "ema_20": safe("ema_20"),
# #         "bb_lower": safe("bbl_20_2.0_2.0"),
# #         "bb_mid": safe("bbm_20_2.0_2.0"),
# #         "bb_upper": safe("bbu_20_2.0_2.0"),
# #         "adx_14": safe("adx_14"),
# #         "recent_close_history": df["close"].tail(30).round(2).to_dict(),
# #     }
# #     return result


# """
# Technical indicator computation using ta on top of
# Yahoo Finance OHLCV history.
# """
# import logging

# import pandas as pd
# from ta.momentum import RSIIndicator
# from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
# from ta.volatility import BollingerBands

# logger = logging.getLogger(__name__)


# def compute_indicators(history: pd.DataFrame) -> dict:
#     """
#     Compute a standard set of technical indicators from an OHLCV
#     DataFrame (as returned by yfinance). Returns the latest values
#     plus a short recent-history slice for charting.
#     """
#     if history.empty:
#         return {"error": "No price history available."}

#     df = history.copy()
#     df.columns = [c.lower() for c in df.columns]

#     try:
#         close = df["close"]
#         high = df["high"]
#         low = df["low"]

#         # RSI
#         df["rsi_14"] = RSIIndicator(close=close, window=14).rsi()

#         # MACD
#         macd = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
#         df["macd"] = macd.macd()
#         df["macd_signal"] = macd.macd_signal()
#         df["macd_hist"] = macd.macd_diff()

#         # Moving Averages
#         df["sma_20"] = SMAIndicator(close=close, window=20).sma_indicator()
#         df["sma_50"] = SMAIndicator(close=close, window=50).sma_indicator()
#         df["ema_20"] = EMAIndicator(close=close, window=20).ema_indicator()

#         # Bollinger Bands
#         bb = BollingerBands(close=close, window=20, window_dev=2)
#         df["bb_lower"] = bb.bollinger_lband()
#         df["bb_mid"] = bb.bollinger_mavg()
#         df["bb_upper"] = bb.bollinger_hband()

#         # ADX
#         adx = ADXIndicator(high=high, low=low, close=close, window=14)
#         df["adx_14"] = adx.adx()

#     except Exception as exc:
#         logger.error("Indicator computation failed: %s", exc)
#         return {"error": f"Indicator computation failed: {exc}"}

#     latest = df.iloc[-1]

#     def safe(col):
#         return (
#             None
#             if col not in df.columns or pd.isna(latest.get(col))
#             else round(float(latest[col]), 4)
#         )

#     return {
#         "close": safe("close"),
#         "rsi_14": safe("rsi_14"),
#         "macd": safe("macd"),
#         "macd_signal": safe("macd_signal"),
#         "macd_hist": safe("macd_hist"),
#         "sma_20": safe("sma_20"),
#         "sma_50": safe("sma_50"),
#         "ema_20": safe("ema_20"),
#         "bb_lower": safe("bb_lower"),
#         "bb_mid": safe("bb_mid"),
#         "bb_upper": safe("bb_upper"),
#         "adx_14": safe("adx_14"),
#         "recent_close_history": df["close"].tail(30).round(2).to_dict(),
#     }



"""
Technical indicator computation using ta on top of
Yahoo Finance OHLCV history.
"""
import logging

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
from ta.volatility import BollingerBands

logger = logging.getLogger(__name__)


def compute_indicators(history: pd.DataFrame) -> dict:
    """
    Compute a standard set of technical indicators from an OHLCV
    DataFrame (as returned by yfinance). Returns the latest values
    plus a short recent-history slice for charting.
    """
    if history.empty:
        return {"error": "No price history available."}

    df = history.copy()
    df.columns = [c.lower() for c in df.columns]

    try:
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # RSI
        df["rsi_14"] = RSIIndicator(close=close, window=14).rsi()

        # MACD
        macd = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_hist"] = macd.macd_diff()

        # Moving Averages
        df["sma_20"] = SMAIndicator(close=close, window=20).sma_indicator()
        df["sma_50"] = SMAIndicator(close=close, window=50).sma_indicator()
        df["ema_20"] = EMAIndicator(close=close, window=20).ema_indicator()

        # Bollinger Bands
        bb = BollingerBands(close=close, window=20, window_dev=2)
        df["bb_lower"] = bb.bollinger_lband()
        df["bb_mid"] = bb.bollinger_mavg()
        df["bb_upper"] = bb.bollinger_hband()

        # ADX
        adx = ADXIndicator(high=high, low=low, close=close, window=14)
        df["adx_14"] = adx.adx()

    except Exception as exc:
        logger.error("Indicator computation failed: %s", exc)
        return {"error": f"Indicator computation failed: {exc}"}

    latest = df.iloc[-1]

    def safe(col):
        return (
            None
            if col not in df.columns or pd.isna(latest.get(col))
            else round(float(latest[col]), 4)
        )

    # Convert timestamps to strings for MongoDB compatibility
    recent_history = {
        idx.strftime("%Y-%m-%d"): float(value)
        for idx, value in df["close"].tail(30).round(2).items()
    }

    result = {
        "close": safe("close"),
        "rsi_14": safe("rsi_14"),
        "macd": safe("macd"),
        "macd_signal": safe("macd_signal"),
        "macd_hist": safe("macd_hist"),
        "sma_20": safe("sma_20"),
        "sma_50": safe("sma_50"),
        "ema_20": safe("ema_20"),
        "bb_lower": safe("bb_lower"),
        "bb_mid": safe("bb_mid"),
        "bb_upper": safe("bb_upper"),
        "adx_14": safe("adx_14"),
        "recent_close_history": recent_history,
    }

    return result