import unittest
import asyncio
from unittest.mock import AsyncMock, patch
from fetcher import CryptoStream, CryptoStreamManager, CryptoDataFetcher, SyntheticDataGenerator

class TestCryptoStream(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.stream = CryptoStream(
            exchange="binance",
            symbols=[
                {"symbol": "BTC/USDT", "watch_ticker": True, "watch_ohlcv": True, "watch_order_book": True},
                {"symbol": "ETH/USDT", "watch_ticker": True, "watch_ohlcv": False, "watch_order_book": True}
            ],
            interval="1s",
            is_synthetic=False,
            api_credentials={}
        )

    def test_add_callback(self):
        """
        \nTest callback registration.\n
        """
        callback = lambda x: None
        self.stream.add_callback(callback)
        self.assertIn(callback, self.stream.callbacks)

    def test_parse_interval(self):
        """
        \nTest interval parsing.\n
        """
        self.assertEqual(self.stream._parse_interval("1s"), 1.0)
        self.assertEqual(self.stream._parse_interval("500ms"), 0.5)
        with self.assertRaises(ValueError):
            self.stream._parse_interval("invalid")

    @patch('ccxt.async_support.binance')
    async def test_stream_ticker(self, mock_exchange):
        """
        \nTest ticker streaming.\n
        """
        mock_exchange.watch_ticker = AsyncMock(return_value={
            'timestamp': 1625097600000, 'close': 50000.0, 'baseVolume': 1.0, 'bid': 49990.0, 'ask': 50010.0
        })
        mock_exchange.fetch_ticker = AsyncMock(return_value={
            'timestamp': 1625097600000, 'close': 50000.0, 'baseVolume': 1.0, 'bid': 49990.0, 'ask': 50010.0
        })
        mock_exchange.load_markets = AsyncMock()
        self.stream.async_exchange = mock_exchange
        self.stream._supports_ticker['BTC/USDT'] = True
        callback = AsyncMock()
        self.stream.add_callback(callback)
        task = asyncio.create_task(self.stream._stream_ccxt())
        await asyncio.sleep(0.1)
        self.stream._running = False
        await task
        callback.assert_called_with({
            'timestamp': pd.to_datetime(1625097600000, unit='ms', utc=True),
            'symbol': 'BTCUSDT',
            'close': 50000.0,
            'volume': 1.0,
            'bid': 49990.0,
            'ask': 50010.0,
            'spread': 20.0,
            'spread_pct': (20.0 / 50000.0) * 100,
            'exchange': 'binance',
            'type': 'ticker'
        })

    @patch('ccxt.async_support.binance')
    async def test_stream_kline(self, mock_exchange):
        """
        \nTest 1-second kline streaming.\n
        """
        mock_exchange.watch_ohlcv = AsyncMock(return_value=[
            [1625097600000, 50000.0, 50100.0, 49900.0, 50050.0, 1.0]
        ])
        mock_exchange.fetch_ohlcv = AsyncMock(return_value=[[1625097600000, 50000.0, 50100.0, 49900.0, 50050.0, 1.0]])
        mock_exchange.timeframes = {'1s': '1s'}
        mock_exchange.load_markets = AsyncMock()
        self.stream.async_exchange = mock_exchange
        self.stream._supports_1s_kline['BTC/USDT'] = True
        callback = AsyncMock()
        self.stream.add_callback(callback)
        task = asyncio.create_task(self.stream._stream_ccxt())
        await asyncio.sleep(0.1)
        self.stream._running = False
        await task
        callback.assert_called_with({
            'timestamp': pd.to_datetime(1625097600000, unit='ms', utc=True),
            'symbol': 'BTCUSDT',
            'open': 50000.0,
            'high': 50100.0,
            'low': 49900.0,
            'close': 50050.0,
            'volume': 1.0,
            'is_closed': True,
            'exchange': 'binance',
            'type': 'ohlcv'
        })

    @patch('ccxt.async_support.binance')
    async def test_stream_order_book(self, mock_exchange):
        """
        \nTest order book streaming.\n
        """
        mock_exchange.watch_order_book = AsyncMock(return_value={
            'bids': [[50000.0, 1.0]], 'asks': [[50010.0, 1.0]], 'timestamp': 1625097600000
        })
        mock_exchange.fetch_order_book = AsyncMock(return_value={
            'bids': [[50000.0, 1.0]], 'asks': [[50010.0, 1.0]], 'timestamp': 1625097600000
        })
        mock_exchange.load_markets = AsyncMock()
        self.stream.async_exchange = mock_exchange
        self.stream._supports_order_book['BTC/USDT'] = True
        callback = AsyncMock()
        self.stream.add_callback(callback)
        task = asyncio.create_task(self.stream._stream_ccxt())
        await asyncio.sleep(0.1)
        self.stream._running = False
        await task
        callback.assert_called()

    @patch('ccxt.async_support.binance')
    async def test_reconnect(self, mock_exchange):
        """
        \nTest reconnect with backoff.\n
        """
        mock_exchange.close = AsyncMock()
        mock_exchange.load_markets = AsyncMock(side_effect=[Exception("Connection error"), None])
        mock_exchange.fetch_ticker = AsyncMock(return_value={'close': 50000.0, 'baseVolume': 1.0})
        mock_exchange.fetch_ohlcv = AsyncMock(return_value=[])
        mock_exchange.fetch_order_book = AsyncMock(return_value={'bids': [[50000.0, 1.0]], 'asks': [[50010.0, 1.0]]})
        self.stream.async_exchange = mock_exchange
        await self.stream._reconnect()
        self.assertEqual(mock_exchange.load_markets.call_count, 2)

    def tearDown(self):
        self.loop.run_until_complete(self.stream.stop())

class TestCryptoStreamManager(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        with open('test_config.yaml', 'w') as f:
            f.write("""
exchanges:
  - exchange: synthetic
    symbols:
      - symbol: BTCUSDT
        watch_ticker: true
        watch_ohlcv: true
        watch_order_book: true
    interval: 1s
    is_synthetic: true
""")
        self.manager = CryptoStreamManager('test_config.yaml')

    async def test_stream_manager(self):
        """
        \nTest multi-exchange streaming.\n
        """
        callback = AsyncMock()
        for stream in self.manager.streams:
            stream.add_callback(callback)
        task = asyncio.create_task(self.manager.start())
        await asyncio.sleep(0.1)
        for stream in self.manager.streams:
            stream._running = False
        await task
        callback.assert_called()

    def tearDown(self):
        self.loop.run_until_complete(self.manager.stop())
        import os
        os.remove('test_config.yaml')

class TestSyntheticDataGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = SyntheticDataGenerator()

    def test_generate_ticker_only(self):
        """
        \nTest synthetic ticker data generation.\n
        """
        df = self.generator.generate_crypto_data(
            symbols=["BTCUSDT"], hours=1, interval_minutes=1, seed=42,
            generate_ticker=True, generate_ohlcv=False, generate_order_book=False
        )
        self.assertIn('close', df.columns)
        self.assertNotIn('open', df.columns)
        self.assertNotIn('best_bid', df.columns)
        self.assertEqual(len(df), 60)

    def test_generate_ohlcv_only(self):
        """
        \nTest synthetic OHLCV data generation.\n
        """
        df = self.generator.generate_crypto_data(
            symbols=["BTCUSDT"], hours=1, interval_minutes=1, seed=42,
            generate_ticker=False, generate_ohlcv=True, generate_order_book=False
        )
        self.assertIn('open', df.columns)
        self.assertNotIn('bid', df.columns)
        self.assertNotIn('best_bid', df.columns)
        self.assertEqual(len(df), 60)

    def test_generate_order_book_only(self):
        """
        \nTest synthetic order book data generation.\n
        """
        df = self.generator.generate_crypto_data(
            symbols=["BTCUSDT"], hours=1, interval_minutes=1, seed=42,
            generate_ticker=False, generate_ohlcv=False, generate_order_book=True
        )
        self.assertIn('best_bid', df.columns)
        self.assertNotIn('open', df.columns)
        self.assertNotIn('bid', df.columns)
        self.assertEqual(len(df), 60)

    def test_generate_all(self):
        """
        \nTest synthetic ticker, OHLCV, and order book data generation.\n
        """
        df = self.generator.generate_crypto_data(
            symbols=["BTCUSDT"], hours=1, interval_minutes=1, seed=42,
            generate_ticker=True, generate_ohlcv=True, generate_order_book=True
        )
        self.assertIn('close', df.columns)
        self.assertIn('open', df.columns)
        self.assertIn('best_bid', df.columns)
        self.assertEqual(len(df), 60)

if __name__ == "__main__":
    unittest.main()