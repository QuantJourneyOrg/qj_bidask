"""
	Eodhistorical Data Connector - Financial and Economic Data Integration for QuantJourney Framework
    ---------------------------------------------------------

	This module provides a class for fetching financial and economic data from the Eodhistorical Data API.
	It supports the retrieval of OHLCV data, fundamental data, and other financial metrics for a wide range of stocks and indices.

	Last Updated: 2024-03-18

	Note:
    This module is part of a larger educational and prototyping framework and may lack
	advanced features or optimizations found in production-grade systems.

	Proprietary License - QuantJourney Framework

	This file is part of the QuantJourney Framework and is licensed for internal, non-commercial use only.
    Modifications are permitted solely for personal, non-commercial testing. Redistribution and commercial use are prohibited.

	For full terms, see the LICENSE file or contact Jakub Polec at jakub@quantjourney.pro.
"""

import pytz
import os
import pandas as pd
from typing import List, Union, Optional, Dict
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import urllib
import urllib.parse

from eod import EodHistoricalData

import quantjourney.data.data_fetch as ff
from quantjourney.logger import logger


# EodHistoricalData Connector class -----------------------------------------------------------
class EodConnector:
    def __init__(self, api_key):
        """
        Initialize a EodConnector class.

        Args:
                api_key: str, The API key for the EodHistorical Data API.
        """
        if not api_key:
            raise ValueError("EOD: API key is required")
        self.api_key = api_key
        self.connector = EodHistoricalData(api_key)

    # OHLCV Data --------------------------------------------------------------

    async def async_get_ohlcv(
        self,
        tickers: List[str],
        exchanges: List[str],
        granularity: str,
        period_starts: List[str],
        period_ends: List[str],
    ) -> List[pd.DataFrame]:
        """
        Asynchronously fetches OHLCV data for a given list of tickers and exchanges.

        Args:
                tickers (list of str): List of stock tickers.
                exchanges (list of str): List of stock exchanges corresponding to tickers.
                granularity (str): Time period ('5m', '15m', '30m', '1h', '1d').
                period_starts (list of str): List of start dates for each ticker's data retrieval period.
                period_ends (list of str): List of end dates for each ticker's data retrieval period.

        Returns:
                list of pd.DataFrame: List of DataFrames containing OHLCV data for each ticker.
        """
        # Use the last 30 days as default period if starts and ends are not provided
        if not period_starts:
            period_starts = [
                datetime.datetime.utcnow() - datetime.timedelta(days=30)
            ] * len(tickers)
        if not period_ends:
            period_ends = [datetime.datetime.utcnow()] * len(tickers)

        if not all(isinstance(item, str) for item in tickers):
            raise TypeError("EOD: All tickers must be strings.")
        if not all(isinstance(item, str) for item in exchanges):
            raise TypeError("EOD: All exchanges must be strings.")
        if len(tickers) != len(exchanges) != len(period_starts) != len(period_ends):
            raise ValueError(
                "EOD: Length of tickers, exchanges, period_starts, and period_ends must be the same."
            )

        urls = []
        results = []
        for ticker, exchange, period_start, period_end in zip(
            tickers, exchanges, period_starts, period_ends
        ):
            params = {
                "fmt": "json",
                "from": period_start,
                "to": period_end,
                "period": granularity,
                "api_token": self.api_key,
            }
            url = (
                f"https://eodhistoricaldata.com/api/eod/{ticker}.{exchange}?"
                + urllib.parse.urlencode(params)
            )
            urls.append(url)

        try:
            # Fetch data asynchronously
            results = await ff.async_aiohttp_get_all(urls)

        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise

        dfs = []
        for result in results:
            if not result:
                dfs.append(pd.DataFrame())
                continue

            try:
                df = pd.DataFrame(result).rename(
                    columns={"date": "datetime", "adjusted_close": "adj_close"}
                )
                if len(df) > 0:
                    df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize(
                        pytz.utc
                    )
                    if granularity == "d":
                        df["datetime"] = df["datetime"].apply(
                            lambda dt: datetime(
                                dt.year, dt.month, dt.day, tzinfo=pytz.utc
                            )
                        )
                dfs.append(df)
            except Exception as e:
                logger.error(f"Error processing data: {e}")
                dfs.append(pd.DataFrame())
                continue

        return dfs

    async def async_get_live_lagged_prices(
        self, tickers: List[str], exchanges: List[str]
    ) -> List[pd.DataFrame]:
        """
        Asynchronously fetches live and lagged prices for the given tickers and exchanges.

        Args:
                tickers (list of str): List of stock tickers.
                exchanges (list of str): List of stock exchanges corresponding to tickers.

        Returns:
                dict: Dictionary containing live and lagged prices for each ticker.
        """
        if not all(isinstance(item, str) for item in tickers):
            raise TypeError("EOD: All tickers must be strings.")
        if not all(isinstance(item, str) for item in exchanges):
            raise TypeError("EOD: All exchanges must be strings.")

        urls = []
        results = {}
        for ticker, exchange in zip(tickers, exchanges):
            params = {
                "api_token": os.getenv("EOD_KEY"),
                "fmt": "json",
                "api_token": self.api_key,
            }
            url = (
                f"https://eodhistoricaldata.com/api/real-time/{ticker}.{exchange}?"
                + urllib.parse.urlencode(params)
            )
            urls.append(url)

        try:
            # Fetch data asynchronously
            responses = await ff.async_aiohttp_get_all(urls)
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise

        for i, response in enumerate(responses):
            if response is not None:
                # Process the fetched data and convert it into DataFrame
                try:
                    df = pd.DataFrame(response).rename(
                        columns={"date": "datetime", "adjusted_close": "adj_close"}
                    )
                    if len(df) > 0:
                        df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize(
                            pytz.utc
                        )
                    results[(tickers[i], exchanges[i])] = df
                except Exception as e:
                    logger.error(f"Error processing data: {e}")

        return results

    async def async_get_intraday_data(
        self,
        tickers: List[str],
        exchanges: List[str],
        interval: str = "5m",
        to_utc: datetime = None,
        period_days: int = 120,
    ) -> List[pd.DataFrame]:
        """
        Asynchronously fetches intraday data for the given tickers and exchanges.

        Args:
                tickers (list of str): List of stock tickers.
                exchanges (list of str): List of stock exchanges corresponding to tickers.
                interval (str): Interval for the intraday data ('1m', '5m', '15m', '30m', '1h').
                to_utc (datetime): End date and time in UTC. Defaults to current UTC time.
                period_days (int): Number of days for the data period.

        Returns:
                dict: Dictionary containing intraday data DataFrames for each ticker.
        """
        if not all(isinstance(item, str) for item in tickers):
            raise TypeError("All tickers must be strings.")
        if not all(isinstance(item, str) for item in exchanges):
            raise TypeError("All exchanges must be strings.")

        if to_utc is None:
            to_utc = datetime.utcnow()

        urls = []
        results = {}
        for ticker, exchange in zip(tickers, exchanges):
            params = {
                "api_token": os.getenv("EOD_KEY"),
                "interval": interval,
                "fmt": "json",
                "from": int((to_utc - timedelta(days=period_days)).timestamp()),
                "to": int(to_utc.timestamp()),
                "api_token": self.api_key,
            }
            url = (
                f"https://eodhistoricaldata.com/api/intraday/{ticker}.{exchange}?"
                + urllib.parse.urlencode(params)
            )
            urls.append(url)

        try:
            # Fetch data asynchronously
            responses = await ff.async_aiohttp_get_all(urls)
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise

        for i, response in enumerate(responses):
            if response is not None:
                # Process the fetched data and convert it into DataFrame
                try:
                    df = (
                        pd.DataFrame(response)
                        .reset_index(drop=True)
                        .set_index("datetime")
                    )
                    results[(tickers[i], exchanges[i])] = df
                except Exception as e:
                    logger.error(f"Error processing data: {e}")

        return results

    # Fundamental Data ---------------------------------------------------------

    async def async_get_fundamental_data(
        self, ticker: str, exchange: str = "US"
    ) -> Dict:
        """
        Get fundamental data for a given stock ticker or Index.
        Available data:: https://eodhistoricaldata.com/financial-apis/stock-etfs-fundamental-data-feeds/

        Args:
                ticker (str): Stock ticker or Index.
                exchange (str): Stock exchange. Default is 'US'.

        Returns:
                dict: Dictionary containing fundamental data.
        """
        try:
            output = self.connector.get_fundamental_equity(f"{ticker}.{exchange}")
            logger.info(f"Fetched fundamental data for {ticker}.{exchange}")

            return output

        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise

    # Fundamental Data ---------------------------------------------------------

    async def async_get_income_statement(
        self, ticker: str, exchange: str, option: str = "q"
    ) -> pd.DataFrame:
        """
		Get income statement data for a given stock ticker and exchange.

		Examples:
			income_statement = await async_get_income_statement("AAPL", "US", "q")

			Income Statement (Quarterly):
							date filing_date currency_symbol researchDevelopment  \
			1985-09-30  1985-09-30  1985-09-30             USD                None
			1985-12-31  1985-12-31  1985-12-31             USD                None
			1986-03-31  1986-03-31  1986-03-31             USD                None
			1986-06-30  1986-06-30  1986-06-30             USD                None
			1986-09-30  1986-09-30  1986-09-30             USD                None
			...                ...         ...             ...                 ...
			2022-12-31  2022-12-31  2023-02-03             USD       7709000000.00
			2023-03-31  2023-03-31  2023-05-05             USD       7457000000.00
			2023-06-30  2023-06-30  2023-08-04             USD       7442000000.00
			2023-09-30  2023-09-30  2023-11-03             USD       7307000000.00
			2023-12-31  2023-12-31  2024-02-02             USD       7696000000.00

		Args:
			ticker (str): Stock ticker.
			exchange (str): Stock exchange.
			option (str): Option for quarterly ('q') or yearly ('y') data.

		Returns:
			pd.DataFrame: DataFrame containing income statement data.
		"""
        try:
            fundamental_data = await self.async_get_fundamental_data(ticker, exchange)
            income_statement = fundamental_data["Financials"]["Income_Statement"]
            if option == "q":
                return (
                    pd.DataFrame(income_statement["quarterly"]).transpose().iloc[::-1]
                )
            elif option == "y":
                return pd.DataFrame(income_statement["yearly"]).transpose().iloc[::-1]
            else:
                raise ValueError(
                    "Invalid option. Choose 'q' for quarterly or 'y' for yearly."
                )
        except Exception as e:
            logger.error(
                f"Error retrieving income statement for {ticker}.{exchange}: {e}"
            )
            raise

    async def async_get_balance_sheet(
        self, ticker, exchange, option="q"
    ) -> pd.DataFrame:
        """
		Get balance sheet data for a given stock ticker and exchange.

		Examples:
			balance_sheet = await async_get_balance_sheet("AAPL", "US", "q")

			Balance Sheet (Quarterly):
							date filing_date currency_symbol      totalAssets  \
			1985-09-30  1985-09-30  1985-09-30             USD     936200000.00   
			1985-12-31  1985-12-31  1985-12-31             USD             None   
			1986-03-31  1986-03-31  1986-03-31             USD             None   
			1986-06-30  1986-06-30  1986-06-30             USD             None   
			1986-09-30  1986-09-30  1986-09-30             USD    1160100000.00   
			...                ...         ...             ...              ...   
			2022-12-31  2022-12-31  2023-02-03             USD  346747000000.00   
			2023-03-31  2023-03-31  2023-05-05             USD  332160000000.00   
			2023-06-30  2023-06-30  2023-08-04             USD  335038000000.00   
			2023-09-30  2023-09-30  2023-11-03             USD  352583000000.00   
			2023-12-31  2023-12-31  2024-02-02             USD  353514000000.00   

		Args:
			ticker (str): Stock ticker.
			exchange (str): Stock exchange.
			option (str): Option for quarterly ('q') or yearly ('y') data.

		Returns:
			pd.DataFrame: DataFrame containing balance sheet data.
		"""
        try:
            fundamental_data = await self.async_get_fundamental_data(ticker, exchange)
            balance_sheet = fundamental_data["Financials"]["Balance_Sheet"]
            if option == "q":
                return pd.DataFrame(balance_sheet["quarterly"]).transpose().iloc[::-1]
            elif option == "y":
                return pd.DataFrame(balance_sheet["yearly"]).transpose().iloc[::-1]
            else:
                raise ValueError(
                    "Invalid option. Choose 'q' for quarterly or 'y' for yearly."
                )
        except Exception as e:
            logger.error(f"Error retrieving balance sheet for {ticker}.{exchange}: {e}")
            raise

    async def async_get_cash_flow(self, ticker, exchange, option="q"):
        """
		Get cash flow data for a given stock ticker and exchange.

		Examples:
			cash_flow = await async_get_cash_flow("AAPL", "US", "q")

			Cash Flow (Quarterly):
				date filing_date currency_symbol     investments  \
			1989-12-31  1989-12-31  1989-12-31             USD            None
			1990-03-31  1990-03-31  1990-03-31             USD            None
			1990-06-30  1990-06-30  1990-06-30             USD            None
			1990-09-30  1990-09-30  1990-09-30             USD            None
			1990-12-31  1990-12-31  1990-12-31             USD            None
			...                ...         ...             ...             ...
			2022-12-31  2022-12-31  2023-02-03             USD  -1445000000.00
			2023-03-31  2023-03-31  2023-05-05             USD   2319000000.00
			2023-06-30  2023-06-30  2023-08-04             USD    437000000.00
			2023-09-30  2023-09-30  2023-11-03             USD   2394000000.00
			2023-12-31  2023-12-31  2024-02-02             USD   1927000000.00

		Args:
			ticker (str): Stock ticker.
			exchange (str): Stock exchange.
			option (str): Option for quarterly ('q') or yearly ('y') data.

		Returns:
			pd.DataFrame: DataFrame containing cash flow data.
		"""
        try:
            fundamental_data = await self.async_get_fundamental_data(ticker, exchange)
            cash_flow = fundamental_data["Financials"]["Cash_Flow"]
            if option == "q":
                return pd.DataFrame(cash_flow["quarterly"]).transpose().iloc[::-1]
            elif option == "y":
                return pd.DataFrame(cash_flow["yearly"]).transpose().iloc[::-1]
            else:
                raise ValueError(
                    "Invalid option. Choose 'q' for quarterly or 'y' for yearly."
                )
        except Exception as e:
            logger.error(f"Error retrieving cash flow for {ticker}.{exchange}: {e}")
            raise

    # Highlights ---------------------------------------------------------------
    # We can use the fundamental data to get the highlights data for a given stock ticker and exchange.
    # This is to limit the number of API calls and improve efficiency.

    async def get_ticker_highlights(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Get highlights data for a given stock ticker and exchange. If fundamental data is pre-fetched,
        it can be passed directly to avoid fetching it again.

        Examples:
                {'MarketCapitalization': 2614313615360, 'MarketCapitalizationMln': 2614313.6154, 'EBITDA': 130108997632, 'PERatio': 26.3297,
                'PEGRatio': 2.112, 'WallStreetTargetPrice': 198.9, 'BookValue': 4.793, 'DividendShare': 0.95, 'DividendYield': 0.0057,
                'EarningsShare': 6.43, 'EPSEstimateCurrentYear': 6.53, 'EPSEstimateNextYear': 7.13, 'EPSEstimateNextQuarter': 1.57,
                'EPSEstimateCurrentQuarter': 2.1, 'MostRecentQuarter': '2023-12-31', 'ProfitMargin': 0.2616, 'OperatingMarginTTM': 0.3376,
                'ReturnOnAssetsTTM': 0.2118, 'ReturnOnEquityTTM': 1.5427, 'RevenueTTM': 385706000384, 'RevenuePerShareTTM': 24.648,
                'QuarterlyRevenueGrowthYOY': 0.021, 'GrossProfitTTM': 170782000000, 'DilutedEpsTTM': 6.43, 'QuarterlyEarningsGrowthYOY': 0.16}

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Pre-fetched fundamental data for the ticker.

        Returns:
                Optional[Dict]: Dictionary containing highlights data if found, otherwise None.
        """
        try:
            if fundamental_data is None:
                fundamental_data = await self.async_get_fundamental_data(
                    ticker, exchange
                )
            return fundamental_data.get("Highlights", None)
        except Exception as e:
            logger.error(f"Error retrieving highlights for {ticker} on {exchange}: {e}")
            raise

    async def get_financial_metric(
        self,
        ticker: str,
        exchange: str,
        metric_key: str,
        fundamental_data: Optional[Dict] = None,
    ) -> Optional[Union[str, float]]:
        """
        Fetch a specific financial metric from the highlights data for a given stock ticker and exchange, using either pre-fetched
        fundamental data or by fetching it anew. This method ensures that the data is handled efficiently and errors are logged properly.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                metric_key (str): The key of the financial metric in the highlights.
                fundamental_data (Optional[Dict]): Optionally pre-fetched fundamental data containing the 'Highlights' key.

        Returns:
                Optional[Union[str, float]]: The requested financial metric in its original format if available, otherwise None.
        """
        try:
            # Check if fundamental data is provided, and ensure it contains 'Highlights'
            if fundamental_data is None or "Highlights" not in fundamental_data:
                fundamental_data = await self.get_ticker_highlights(ticker, exchange)
                if fundamental_data is None:
                    logger.error(
                        f"No fundamental data found for {ticker} on {exchange}"
                    )
                    return None
                elif metric_key in fundamental_data:
                    return fundamental_data[metric_key]
                else:
                    logger.warning(
                        f"Metric {metric_key} not found in highlights for {ticker} on {exchange}"
                    )
                    return None

            # Retrieve the specific financial metric from provided fundamental data, first extract the 'Highlights' section
            highlights_data = fundamental_data.get("Highlights", {})

            if metric_key in highlights_data:
                return highlights_data[metric_key]
            else:
                logger.warning(
                    f"Metric {metric_key} not found in highlights for {ticker} on {exchange}"
                )
                return None
        except Exception as e:
            logger.error(
                f"Error retrieving {metric_key} for {ticker} on {exchange}: {e}"
            )
            raise

    # Retrieve Market Capitalization
    async def get_ticker_mcap(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "MarketCapitalization", fundamental_data
        )

    # Retrieve EBITDA
    async def get_ticker_ebitda(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "EBITDA", fundamental_data
        )

    # Retrieve Price to Earnings Ratio
    async def get_ticker_pe(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "PERatio", fundamental_data
        )

    # Retrieve Price to Earnings Growth Ratio
    async def get_ticker_peg(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "PEGRatio", fundamental_data
        )

    # Retrieve Book Value
    async def get_ticker_book(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "BookValue", fundamental_data
        )

    # Retrieve Dividend Per Share
    async def get_ticker_div_ps(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "DividendShare", fundamental_data
        )

    # Retrieve Dividend Yield
    async def get_ticker_div_yield(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "DividendYield", fundamental_data
        )

    # Retrieve Earnings Per Share
    async def get_ticker_eps(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "EarningsShare", fundamental_data
        )

    # Retrieve Date of Most Recent Quarter
    async def get_ticker_last_quarter_date(
        self, ticker, exchange, fundamental_data=None
    ):
        return await self.get_financial_metric(
            ticker, exchange, "MostRecentQuarter", fundamental_data
        )

    # Retrieve Profit Margin
    async def get_ticker_profit_margin(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "ProfitMargin", fundamental_data
        )

    # Retrieve Operating Margin TTM
    async def get_ticker_op_marginTTM(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "OperatingMarginTTM", fundamental_data
        )

    # Retrieve Return on Assets TTM
    async def get_ticker_roaTTM(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "ReturnOnAssetsTTM", fundamental_data
        )

    # Retrieve Return on Equity TTM
    async def get_ticker_roeTTM(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "ReturnOnEquityTTM", fundamental_data
        )

    # Retrieve Revenue TTM
    async def get_ticker_revenueTTM(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "RevenueTTM", fundamental_data
        )

    # Retrieve Revenue Per Share TTM
    async def get_ticker_revenue_psTTM(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "RevenuePerShareTTM", fundamental_data
        )

    # Retrieve Quarterly Revenue Growth YOY
    async def get_ticker_qoq_rev_growth(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "QuarterlyRevenueGrowthYOY", fundamental_data
        )

    # Retrieve Quarterly Earnings Growth YOY
    async def get_ticker_qoq_earnings_growth(
        self, ticker, exchange, fundamental_data=None
    ):
        return await self.get_financial_metric(
            ticker, exchange, "QuarterlyEarningsGrowthYOY", fundamental_data
        )

    # Retrieve Gross Profit TTM
    async def get_ticker_gross_profitTTM(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "GrossProfitTTM", fundamental_data
        )

    # Retrieve Diluted EPS TTM
    async def get_ticker_diluted_epsTTM(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "DilutedEpsTTM", fundamental_data
        )

    # Retrieve Wall Street Target Price
    async def get_ticker_analyst_target(self, ticker, exchange, fundamental_data=None):
        return await self.get_financial_metric(
            ticker, exchange, "WallStreetTargetPrice", fundamental_data
        )

    # Shares Stats -----------------------------------------------------------

    async def get_ticker_sharestats(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Fetch ShareStats data for a given stock ticker and exchange.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Optionally pre-fetched fundamental data.

        Returns:
                Optional[Dict]: Dictionary containing ShareStats data if found, otherwise None.
        """
        try:
            if fundamental_data is None:
                fundamental_data = await self.async_get_fundamental_data(
                    ticker, exchange
                )
            return fundamental_data.get("ShareStats", None)
        except Exception as e:
            logger.error(f"Error retrieving ShareStats for {ticker} on {exchange}: {e}")
            raise

    async def get_ticker_shortratio(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[float]:
        """
        Get the short ratio from ShareStats for a given ticker and exchange.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Pre-fetched ShareStats or fundamental data.

        Returns:
                Optional[float]: Short ratio if available, otherwise None.
        """
        sharestats = await self.get_ticker_sharestats(
            ticker, exchange, fundamental_data
        )
        return (
            float(sharestats["ShortRatio"])
            if sharestats and "ShortRatio" in sharestats
            else None
        )

    async def get_ticker_percentinsiders(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[float]:
        """
        Get the percentage of insiders from ShareStats for a given ticker and exchange.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Pre-fetched ShareStats or fundamental data.

        Returns:
                Optional[float]: Percent of insiders if available, otherwise None.
        """
        sharestats = await self.get_ticker_sharestats(
            ticker, exchange, fundamental_data
        )
        return (
            float(sharestats["PercentInsiders"])
            if sharestats and "PercentInsiders" in sharestats
            else None
        )

    # Valuation --------------------------------------------------------------

    async def get_ticker_valuation(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Fetch valuation data for a given stock ticker and exchange.

        Examples:
                ticker_val = await get_ticker_valuation("AAPL", "US")

                {'TrailingPE': 26.3297, 'ForwardPE': 26.3158, 'PriceSalesTTM': 6.778, 'PriceBookMRQ': 35.4267, 'EnterpriseValue': 2649250332672,
                'EnterpriseValueRevenue': 6.8966, 'EnterpriseValueEbitda': 19.929}

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Optionally pre-fetched fundamental data.

        Returns:
                Optional[Dict]: Valuation data if found, otherwise None.
        """
        if fundamental_data is None:
            try:
                fundamental_data = await self.async_get_fundamental_data(
                    ticker, exchange
                )
            except Exception as e:
                logger.error(
                    f"Error retrieving fundamental data for {ticker} on {exchange}: {e}"
                )
                raise
        return fundamental_data.get("Valuation", None)

    async def get_ticker_trailing_pe(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[float]:
        """
        Get the trailing PE ratio from the valuation data for a given ticker and exchange.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Optionally pre-fetched fundamental or valuation data.

        Returns:
                Optional[float]: Trailing PE ratio if available, otherwise None.
        """
        valuation = await self.get_ticker_valuation(ticker, exchange, fundamental_data)
        return (
            float(valuation["TrailingPE"])
            if valuation and "TrailingPE" in valuation
            else None
        )

    async def get_ticker_forward_pe(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[float]:
        """
        Get the forward PE ratio from the valuation data for a given ticker and exchange.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Optionally pre-fetched fundamental or valuation data.

        Returns:
                Optional[float]: Forward PE ratio if available, otherwise None.
        """
        valuation = await self.get_ticker_valuation(ticker, exchange, fundamental_data)
        return (
            float(valuation["ForwardPE"])
            if valuation and "ForwardPE" in valuation
            else None
        )

    async def get_ticker_price_to_sales(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[float]:
        """
        Get the price-to-sales ratio from the valuation data for a given ticker and exchange.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Optionally pre-fetched fundamental or valuation data.

        Returns:
                Optional[float]: Price-to-sales ratio if available, otherwise None.
        """
        valuation = await self.get_ticker_valuation(ticker, exchange, fundamental_data)
        return (
            float(valuation["PriceSalesTTM"])
            if valuation and "PriceSalesTTM" in valuation
            else None
        )

    async def get_ticker_price_to_book(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[float]:
        """
        Get the price-to-book ratio from the valuation data for a given ticker and exchange.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Optionally pre-fetched fundamental or valuation data.

        Returns:
                Optional[float]: Price-to-book ratio if available, otherwise None.
        """
        valuation = await self.get_ticker_valuation(ticker, exchange, fundamental_data)
        return (
            float(valuation["PriceBookMRQ"])
            if valuation and "PriceBookMRQ" in valuation
            else None
        )

    async def get_ticker_ev(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[float]:
        """
        Get the enterprise value from the valuation data for a given ticker and exchange.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Optionally pre-fetched fundamental or valuation data.

        Returns:
                Optional[float]: Enterprise value if available, otherwise None.
        """
        valuation = await self.get_ticker_valuation(ticker, exchange, fundamental_data)
        return (
            float(valuation["EnterpriseValue"])
            if valuation and "EnterpriseValue" in valuation
            else None
        )

    async def get_ticker_ev_revenue(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[float]:
        """
        Get the enterprise value to revenue ratio from the valuation data for a given ticker and exchange.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Optionally pre-fetched fundamental or valuation data.

        Returns:
                Optional[float]: Enterprise value to revenue ratio if available, otherwise None.
        """
        valuation = await self.get_ticker_valuation(ticker, exchange, fundamental_data)
        return (
            float(valuation["EnterpriseValueRevenue"])
            if valuation and "EnterpriseValueRevenue" in valuation
            else None
        )

    async def get_ticker_ev_ebitda(
        self, ticker: str, exchange: str, fundamental_data: Optional[Dict] = None
    ) -> Optional[float]:
        """
        Get the enterprise value to EBITDA ratio from the valuation data for a given ticker and exchange.

        Args:
                ticker (str): Stock ticker.
                exchange (str): Stock exchange.
                fundamental_data (Optional[Dict]): Optionally pre-fetched fundamental or valuation data.

        Returns:
                Optional[float]: Enterprise value to EBITDA ratio if available, otherwise None.
        """
        valuation = await self.get_ticker_valuation(ticker, exchange, fundamental_data)
        return (
            float(valuation["EnterpriseValueEbitda"])
            if valuation and "EnterpriseValueEbitda" in valuation
            else None
        )

    # EOD Other ---------------------------------------------------------------

    def get_exchange_symbols(self, exchange="US") -> List[str]:
        """
        Get all symbols for a given exchange.

        Args:
                exchange (str): Stock exchange. Default is 'US'.

        Returns:
                list: List of symbols for the exchange.
        """
        try:
            output = self.connector.get_exchange_symbols(exchange)
            logger.info(f"Fetched symbols for {exchange}")
            return output
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise

    def get_exchange_list(self) -> List[str]:
        """
        Get a list of all exchanges.

        Returns:
                list: List of all exchanges.
        """
        try:
            output = self.connector.get_exchange_list()
            logger.info(f"Fetched exchange list")
            return output
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise

    def get_index_list(self) -> List[str]:
        """
        Get a list of all indices.

        #Supported indices: https://eodhistoricaldata.com/financial-apis/list-supported-indices/

        Returns:
                List
        """
        try:
            output = self.connector.get_index_list()
            logger.info(f"Fetched index list")
            return output
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise

    # Forex -------------------------------------------------------------------

    async def async_get_intraday_forex_data(
        self,
        pairs: List[str],
        interval: str = "5m",
        to_utc: datetime = None,
        period_days: int = 120,
    ) -> List[pd.DataFrame]:
        """
        Asynchronously fetches intraday data for the given forex pairs.


        Args:
                pairs (list of str): List of forex pairs.
                interval (str): Interval for the intraday data ('1m', '5m', '15m', '30m', '1h').
                to_utc (datetime): End date and time in UTC. Defaults to current UTC time.
                period_days (int): Number of days for the data period.

        Returns:
                dict: Dictionary containing intraday data DataFrames for each pair.
        """
        if not all(isinstance(item, str) for item in pairs):
            raise TypeError("All pairs must be strings.")

        if to_utc is None:
            to_utc = datetime.utcnow()

        urls = []
        results = {}
        for pair in pairs:
            params = {
                "api_token": self.api_key,
                "interval": interval,
                "fmt": "json",
                "from": int((to_utc - timedelta(days=period_days)).timestamp()),
                "to": int(to_utc.timestamp()),
                "api_token": self.api_key,
            }
            url = (
                f"https://eodhistoricaldata.com/api/intraday/{pair}.FOREX?"
                + urllib.parse.urlencode(params)
            )
            urls.append(url)

        try:
            # Fetch data asynchronously
            print(urls)
            responses = await ff.async_aiohttp_get_all(urls)
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise

        for i, response in enumerate(responses):
            if response is not None:
                # Process the fetched data and convert it into DataFrame
                try:
                    df = (
                        pd.DataFrame(response)
                        .reset_index(drop=True)
                        .set_index("datetime")
                    )
                    results[pairs[i]] = df
                except Exception as e:
                    logger.error(f"Error processing data: {e}")

        return results

    async def async_forex_get_intraday_data(
        self, pairs, interval, to_utc, period_days
    ) -> Dict:
        """
        Fetches intraday data for the given forex pairs

        Args:
                pairs (list of str): List of forex pairs.
                interval (str): Interval for the intraday data ('1m', '5m', '15m', '30m', '1h').
                to_utc (datetime): End date and time in UTC.
                period_days (int): Number of days for the data period.

        Returns:
                dict: Dictionary containing intraday data DataFrames for each pair.
        """
        data = {}
        for pair in pairs:
            url = f"https://eodhd.com/api/intraday/{pair}.FOREX?interval={interval}&from={to_utc - timedelta(days=period_days)}&to={to_utc}&api_token=demo&fmt=json"
            response = requests.get(url).json()
            data[pair] = pd.DataFrame(response["data"])
        return data


# Unit Tests ----------------------------------------------------------------
class UnitTests(Enum):
    FUNDAMENTAL_DATA = 2
    INCOME_STATEMENT = 20
    BALANCE_SHEET = 21
    CASH_FLOW = 22
    TICKER_HIGHLIGHTS = 23
    TICKER_MCAP = 24
    TICKER_EBITDA = 25
    TICKER_PE = 26
    TICKER_PEG = 27
    TICKER_BOOK = 28
    TICKER_DIV_PS = 29
    TICKER_DIV_YIELD = 30
    TICKER_EPS = 31
    TICKER_LAST_QUARTER_DATE = 32
    TICKER_PROFIT_MARGIN = 33
    TICKER_OP_MARGINTTM = 34
    TICKER_ROATTM = 35
    TICKER_ROETTM = 36
    TICKER_REVENUETTM = 37
    TICKER_REVENUE_PSTTM = 38
    TICKER_QOQ_REV_GROWTH = 39
    TICKER_QOQ_EARNINGS_GROWTH = 40
    TICKER_GROSS_PROFITTTM = 41
    TICKER_DILUTED_EPSTTM = 42
    TICKER_ANALYST_TARGET = 43
    TICKER_SHARESTATS = 44
    TICKER_SHORTRATIO = 45
    TICKER_PERCENTINSIDERS = 46
    TICKER_VALUATION = 47
    TICKER_TRAILING_PE = 48
    TICKER_FORWARD_PE = 49
    TICKER_PRICE_TO_SALES = 50
    TICKER_PRICE_TO_BOOK = 51
    TICKER_EV = 52
    TICKER_EV_REVENUE = 53
    TICKER_EV_EBITDA = 54


async def run_unit_test(unit_test: UnitTests):

    # Local quantjourney classes
    from quantjourney.data.data_connector import DataConnector

    pd.set_option("display.max_columns", None)

    dc = DataConnector()

    ticker = "orcl"
    exchange = "us"

    if unit_test == UnitTests.FUNDAMENTAL_DATA:
        fundamental_data = await dc.eod.async_get_fundamental_data(ticker, exchange)
        print(f"Fundamental Data:\n{fundamental_data}")

    elif unit_test == UnitTests.INCOME_STATEMENT:
        income_statement_q = await dc.eod.async_get_income_statement(
            ticker, exchange, option="q"
        )
        print(f"Income Statement (Quarterly):\n{income_statement_q}")
        income_statement_y = await dc.eod.async_get_income_statement(
            ticker, exchange, option="y"
        )
        print(f"Income Statement (Yearly):\n{income_statement_y}")
        print(f"Columns in Income Statement: {income_statement_y.columns.tolist()}")

    elif unit_test == UnitTests.BALANCE_SHEET:
        balance_sheet_q = await dc.eod.async_get_balance_sheet(
            ticker, exchange, option="q"
        )
        print(f"Balance Sheet (Quarterly):\n{balance_sheet_q}")
        balance_sheet_y = await dc.eod.async_get_balance_sheet(
            ticker, exchange, option="y"
        )
        print(f"Balance Sheet (Yearly):\n{balance_sheet_y}")
        print(f"Columns in Balance Sheet: {balance_sheet_y.columns.tolist()}")

    elif unit_test == UnitTests.CASH_FLOW:
        cash_flow_q = await dc.eod.async_get_cash_flow(ticker, exchange, option="q")
        print(f"Cash Flow (Quarterly):\n{cash_flow_q}")
        cash_flow_y = await dc.eod.async_get_cash_flow(ticker, exchange, option="y")
        print(f"Cash Flow (Yearly):\n{cash_flow_y}")
        print(f"Columns in Cash Flow: {cash_flow_y.columns.tolist()}")

    elif unit_test == UnitTests.TICKER_HIGHLIGHTS:
        highlights = await dc.eod.get_ticker_highlights(ticker, exchange)
        print(f"Ticker Highlights:\n{highlights}")

    elif unit_test == UnitTests.TICKER_MCAP:
        mcap = await dc.eod.get_ticker_mcap(ticker, exchange)
        print(f"Market Cap: {mcap}")

    elif unit_test == UnitTests.TICKER_EBITDA:
        ebitda = await dc.eod.get_ticker_ebitda(ticker, exchange)
        print(f"EBITDA: {ebitda}")

    elif unit_test == UnitTests.TICKER_PE:
        pe = await dc.eod.get_ticker_pe(ticker, exchange)
        print(f"P/E Ratio: {pe}")

    elif unit_test == UnitTests.TICKER_PEG:
        peg = await dc.eod.get_ticker_peg(ticker, exchange)
        print(f"PEG Ratio: {peg}")

    elif unit_test == UnitTests.TICKER_BOOK:
        book = await dc.eod.get_ticker_book(ticker, exchange)
        print(f"Book Value: {book}")

    elif unit_test == UnitTests.TICKER_DIV_PS:
        div_ps = await dc.eod.get_ticker_div_ps(ticker, exchange)
        print(f"Dividend per Share: {div_ps}")

    elif unit_test == UnitTests.TICKER_DIV_YIELD:
        div_yield = await dc.eod.get_ticker_div_yield(ticker, exchange)
        print(f"Dividend Yield: {div_yield}")

    elif unit_test == UnitTests.TICKER_EPS:
        eps = await dc.eod.get_ticker_eps(ticker, exchange)
        print(f"Earnings per Share: {eps}")

    elif unit_test == UnitTests.TICKER_LAST_QUARTER_DATE:
        last_quarter_date = await dc.eod.get_ticker_last_quarter_date(ticker, exchange)
        print(f"Last Quarter Date: {last_quarter_date}")

    elif unit_test == UnitTests.TICKER_PROFIT_MARGIN:
        profit_margin = await dc.eod.get_ticker_profit_margin(ticker, exchange)
        print(f"Profit Margin: {profit_margin}")

    elif unit_test == UnitTests.TICKER_OP_MARGINTTM:
        op_marginTTM = await dc.eod.get_ticker_op_marginTTM(ticker, exchange)
        print(f"Operating Margin TTM: {op_marginTTM}")

    elif unit_test == UnitTests.TICKER_ROATTM:
        roaTTM = await dc.eod.get_ticker_roaTTM(ticker, exchange)
        print(f"Return on Assets TTM: {roaTTM}")

    elif unit_test == UnitTests.TICKER_ROETTM:
        roeTTM = await dc.eod.get_ticker_roeTTM(ticker, exchange)
        print(f"Return on Equity TTM: {roeTTM}")

    elif unit_test == UnitTests.TICKER_REVENUETTM:
        revenueTTM = await dc.eod.get_ticker_revenueTTM(ticker, exchange)
        print(f"Revenue TTM: {revenueTTM}")

    elif unit_test == UnitTests.TICKER_REVENUE_PSTTM:
        revenue_psTTM = await dc.eod.get_ticker_revenue_psTTM(ticker, exchange)
        print(f"Revenue per Share TTM: {revenue_psTTM}")

    elif unit_test == UnitTests.TICKER_QOQ_REV_GROWTH:
        qoq_rev_growth = await dc.eod.get_ticker_qoq_rev_growth(ticker, exchange)
        print(f"Quarter-over-Quarter Revenue Growth: {qoq_rev_growth}")

    elif unit_test == UnitTests.TICKER_QOQ_EARNINGS_GROWTH:
        qoq_earnings_growth = await dc.eod.get_ticker_qoq_earnings_growth(
            ticker, exchange
        )
        print(f"Quarter-over-Quarter Earnings Growth: {qoq_earnings_growth}")

    elif unit_test == UnitTests.TICKER_GROSS_PROFITTTM:
        gross_profitTTM = await dc.eod.get_ticker_gross_profitTTM(ticker, exchange)
        print(f"Gross Profit TTM: {gross_profitTTM}")

    elif unit_test == UnitTests.TICKER_DILUTED_EPSTTM:
        diluted_epsTTM = await dc.eod.get_ticker_diluted_epsTTM(ticker, exchange)
        print(f"Diluted EPS TTM: {diluted_epsTTM}")

    elif unit_test == UnitTests.TICKER_ANALYST_TARGET:
        analyst_target = await dc.eod.get_ticker_analyst_target(ticker, exchange)
        print(f"Analyst Target Price: {analyst_target}")

    elif unit_test == UnitTests.TICKER_SHARESTATS:
        sharestats = await dc.eod.get_ticker_sharestats(ticker, exchange)
        print(f"Share Stats:\n{sharestats}")

    elif unit_test == UnitTests.TICKER_SHORTRATIO:
        shortratio = await dc.eod.get_ticker_shortratio(ticker, exchange)
        print(f"Short Ratio: {shortratio}")

    elif unit_test == UnitTests.TICKER_PERCENTINSIDERS:
        percentinsiders = await dc.eod.get_ticker_percentinsiders(ticker, exchange)
        print(f"Percent Insiders: {percentinsiders}")

    elif unit_test == UnitTests.TICKER_VALUATION:
        valuation = await dc.eod.get_ticker_valuation(ticker, exchange)
        print(f"Valuation:\n{valuation}")

    elif unit_test == UnitTests.TICKER_TRAILING_PE:
        trailing_pe = await dc.eod.get_ticker_trailing_pe(ticker, exchange)
        print(f"Trailing P/E: {trailing_pe}")

    elif unit_test == UnitTests.TICKER_FORWARD_PE:
        forward_pe = await dc.eod.get_ticker_forward_pe(ticker, exchange)
        print(f"Forward P/E: {forward_pe}")

    elif unit_test == UnitTests.TICKER_PRICE_TO_SALES:
        price_to_sales = await dc.eod.get_ticker_price_to_sales(ticker, exchange)
        print(f"Price to Sales: {price_to_sales}")

    elif unit_test == UnitTests.TICKER_PRICE_TO_BOOK:
        price_to_book = await dc.eod.get_ticker_price_to_book(ticker, exchange)
        print(f"Price to Book: {price_to_book}")

    elif unit_test == UnitTests.TICKER_EV:
        ev = await dc.eod.get_ticker_ev(ticker, exchange)
        print(f"Enterprise Value: {ev}")

    elif unit_test == UnitTests.TICKER_EV_REVENUE:
        ev_revenue = await dc.eod.get_ticker_ev_revenue(ticker, exchange)
        print(f"Enterprise Value to Revenue: {ev_revenue}")

    elif unit_test == UnitTests.TICKER_EV_EBITDA:
        ev_ebitda = await dc.eod.get_ticker_ev_ebitda(ticker, exchange)
        print(f"Enterprise Value to EBITDA: {ev_ebitda}")


async def run_tests_sequentially():

    is_run_all_tests = True

    if is_run_all_tests:
        for unit_test in UnitTests:
            print(f"\n--- Running Unit Test: {unit_test.name} ---")
            await run_unit_test(
                unit_test=unit_test
            )  # This ensures tests run one after another
    else:
        unit_test = UnitTests.TICKER_EBITDA
        print(f"\n--- Running Unit Test: {unit_test.name} ---")
        await run_unit_test(unit_test=unit_test)


if __name__ == "__main__":
    asyncio.run(run_tests_sequentially())
