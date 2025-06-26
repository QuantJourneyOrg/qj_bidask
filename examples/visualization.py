#!/usr/bin/env python3
"""
Visualization module for quantjourney_bidask examples.
Creates animated and static plots for spread monitoring.
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from collections import deque
from typing import List
from quantjourney_bidask import edge_rolling

class AnimatedSpreadMonitor:
    """Animated real-time spread monitor with live plotting."""
    def __init__(self, symbols: List[str], max_points: int = 100):
        self.symbols = symbols
        self.max_points = max_points
        self.data_history = {
            symbol: {
                'timestamps': deque(maxlen=max_points),
                'prices': deque(maxlen=max_points),
                'spreads': deque(maxlen=max_points),
                'volumes': deque(maxlen=max_points)
            } for symbol in symbols
        }
        self.fig, self.axes = plt.subplots(len(symbols), 2, figsize=(15, 6*len(symbols)))
        if len(symbols) == 1:
            self.axes = self.axes.reshape(1, -1)
        self.lines = {}
        self.setup_plots()
        self.animation = None

    def setup_plots(self):
        """Set up matplotlib plots."""
        for i, symbol in enumerate(self.symbols):
            ax_price = self.axes[i, 0]
            ax_price.set_title(f'{symbol} - Real-Time Price')
            ax_price.set_ylabel('Price ($)')
            ax_price.grid(True, alpha=0.3)
            line_price, = ax_price.plot([], [], 'b-', linewidth=2, label='Price')
            self.lines[f'{symbol}_price'] = line_price
            ax_price.legend()
            ax_spread = self.axes[i, 1]
            ax_spread.set_title(f'{symbol} - Real-Time Spread')
            ax_spread.set_ylabel('Spread (bps)')
            ax_spread.set_xlabel('Time')
            ax_spread.grid(True, alpha=0.3)
            line_spread, = ax_spread.plot([], [], 'r-', linewidth=2, label='Spread')
            self.lines[f'{symbol}_spread'] = line_spread
            ax_spread.legend()
        plt.tight_layout()

    def update_data(self, spread_data):
        """Update data from spread monitor callback."""
        symbol = spread_data['symbol']
        if symbol in self.data_history:
            self.data_history[symbol]['timestamps'].append(spread_data['timestamp'])
            self.data_history[symbol]['prices'].append(spread_data['price'])
            self.data_history[symbol]['spreads'].append(spread_data['spread_bps'])
            self.data_history[symbol]['volumes'].append(spread_data['volume'])
            print(f"{symbol}: Price=${spread_data['price']:.2f}, Spread={spread_data['spread_bps']:.2f}bps, Time={spread_data['timestamp']}")
            if hasattr(self, 'fig'):
                self.fig.canvas.draw_idle()

    def animate(self, frame):
        """Animation function for matplotlib."""
        for i, symbol in enumerate(self.symbols):
            history = self.data_history[symbol]
            if len(history['timestamps']) > 0:
                time_nums = [mdates.date2num(t) for t in history['timestamps']]
                self.lines[f'{symbol}_price'].set_data(time_nums, list(history['prices']))
                ax_price = self.axes[i, 0]
                if len(time_nums) >= 2:
                    time_range = max(time_nums) - min(time_nums)
                    if time_range > 0.000012:
                        ax_price.set_xlim(min(time_nums) - time_range*0.05, max(time_nums) + time_range*0.05)
                        ax_price.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                        ax_price.figure.autofmt_xdate()
                    price_range = max(history['prices']) - min(history['prices'])
                    buffer = max(history['prices'][0] * 0.0001, 0.01) if price_range == 0 else price_range * 0.01
                    ax_price.set_ylim(min(history['prices']) - buffer, max(history['prices']) + buffer)
                self.lines[f'{symbol}_spread'].set_data(time_nums, list(history['spreads']))
                ax_spread = self.axes[i, 1]
                if len(time_nums) >= 2:
                    time_range = max(time_nums) - min(time_nums)
                    if time_range > 0.000012:
                        ax_spread.set_xlim(min(time_nums) - time_range*0.05, max(time_nums) + time_range*0.05)
                        ax_spread.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                        ax_spread.figure.autofmt_xdate()
                    spread_max = max(history['spreads'])
                    spread_min = min(history['spreads'])
                    buffer = max(spread_max * 0.1, 0.1) if spread_max == spread_min else (spread_max - spread_min) * 0.1
                    ax_spread.set_ylim(max(0, spread_min - buffer), spread_max + buffer)
        return list(self.lines.values())

    def start_animation(self):
        """Start the animation."""
        self.animation = animation.FuncAnimation(
            self.fig, self.animate, interval=500, blit=False, cache_frame_data=False
        )
        plt.show()

    def stop_animation(self):
        """Stop the animation and close plots."""
        if self.animation:
            self.animation.event_source.stop()
        plt.close(self.fig)

def create_crypto_spread_comparison(df: pd.DataFrame, save_path: str = 'crypto_spread_comparison.png'):
    """Create static comparison of spreads across different crypto assets."""
    symbols = df['symbol'].unique()
    fig, axes = plt.subplots(len(symbols), 1, figsize=(12, 4*len(symbols)), sharex=True)
    if len(symbols) == 1:
        axes = [axes]
    colors = ['blue', 'green', 'red', 'orange'][:len(symbols)]
    for i, (symbol, color) in enumerate(zip(symbols, colors)):
        asset_data = df[df['symbol'] == symbol].dropna(subset=['spread'])
        if asset_data.empty:
            continue
        price_pct = (asset_data['close'] / asset_data['close'].iloc[0] - 1) * 100
        axes[i].plot(asset_data['timestamp'], price_pct, color=color, alpha=0.7, label='Price Change (%)')
        ax_twin = axes[i].twinx()
        ax_twin.plot(asset_data['timestamp'], asset_data['spread'] * 10000, color='red', linewidth=2, label='Spread (bps)')
        axes[i].set_title(f'{symbol} Price vs Spread')
        axes[i].set_ylabel('Price Change (%)', color=color)
        ax_twin.set_ylabel('Spread (bps)', color='red')
        axes[i].grid(True, alpha=0.3)
        mean_spread = asset_data['spread'].mean() * 10000
        std_spread = asset_data['spread'].std() * 10000
        axes[i].text(0.02, 0.98, f'Avg: {mean_spread:.1f}bps\nStd: {std_spread:.1f}bps',
                     transform=axes[i].transAxes, verticalalignment='top',
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        axes[i].legend(loc='upper left')
        ax_twin.legend(loc='upper right')
    plt.suptitle('Crypto Asset Spread Comparison', fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Comparison plot saved as '{save_path}'")
    plt.show()