"""
ETF 績效追蹤與視覺化 — 桌面應用程式
進階程式設計課程專案
"""

import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib.pyplot as plt
import yfinance as yf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class DataFetcher:
    """負責透過 yfinance 取得歷史收盤價資料。"""

    PERIOD_OPTIONS = {
        "1個月": "1mo",
        "半年": "6mo",
        "1年": "1y",
        "5年": "5y",
    }

    def fetch_close_prices(self, ticker: str, period_label: str):
        """
        取得指定代碼與時間範圍的收盤價序列。

        Returns:
            tuple: (日期索引序列, 收盤價序列)

        Raises:
            ValueError: 代碼無效、查無資料或參數錯誤
            OSError: 網路連線問題
        """
        ticker = ticker.strip()
        if not ticker:
            raise ValueError("請輸入股票代碼。")

        if period_label not in self.PERIOD_OPTIONS:
            raise ValueError("請選擇有效的時間範圍。")

        period = self.PERIOD_OPTIONS[period_label]

        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)
        except (ConnectionError, TimeoutError, OSError) as exc:
            raise OSError("無法連線至資料伺服器，請檢查網路連線。") from exc
        except Exception as exc:
            err_msg = str(exc).lower()
            if any(
                keyword in err_msg
                for keyword in ("connection", "network", "timeout", "resolve", "ssl")
            ):
                raise OSError("無法連線至資料伺服器，請檢查網路連線。") from exc
            raise ValueError(f"無法取得資料：{exc}") from exc

        if history is None or history.empty:
            raise ValueError(f"查無「{ticker}」的歷史資料，請確認股票代碼是否正確。")

        if "Close" not in history.columns:
            raise ValueError(f"「{ticker}」資料格式異常，無法取得收盤價。")

        close_series = history["Close"].dropna()
        if close_series.empty:
            raise ValueError(f"「{ticker}」在選定區間內沒有有效收盤價資料。")

        return close_series.index, close_series.values


class AppWindow:
    """負責 tkinter 介面與圖表嵌入顯示。"""

    TIME_RANGE_CHOICES = list(DataFetcher.PERIOD_OPTIONS.keys())

    def __init__(self) -> None:
        self._fetcher = DataFetcher()
        self._canvas = None
        self._figure = None

        self.root = tk.Tk()
        self.root.title("ETF 績效追蹤與視覺化")
        self.root.geometry("900x600")
        self.root.minsize(700, 500)

        self._build_ui()

    def _build_ui(self) -> None:
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(control_frame, text="股票代碼：").grid(row=0, column=0, padx=(0, 5))
        self.ticker_var = tk.StringVar(value="006208.TW")
        self.ticker_entry = ttk.Entry(
            control_frame, textvariable=self.ticker_var, width=20
        )
        self.ticker_entry.grid(row=0, column=1, padx=(0, 20))

        ttk.Label(control_frame, text="時間範圍：").grid(row=0, column=2, padx=(0, 5))
        self.period_var = tk.StringVar(value=self.TIME_RANGE_CHOICES[0])
        self.period_combo = ttk.Combobox(
            control_frame,
            textvariable=self.period_var,
            values=self.TIME_RANGE_CHOICES,
            state="readonly",
            width=10,
        )
        self.period_combo.grid(row=0, column=3, padx=(0, 20))

        self.plot_button = ttk.Button(
            control_frame, text="生成圖表", command=self._on_generate_chart
        )
        self.plot_button.grid(row=0, column=4)

        self.chart_frame = ttk.Frame(self.root, padding=10)
        self.chart_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        placeholder = ttk.Label(
            self.chart_frame,
            text="請輸入股票代碼並點擊「生成圖表」",
            anchor=tk.CENTER,
        )
        placeholder.pack(fill=tk.BOTH, expand=True)
        self._placeholder = placeholder

    def _on_generate_chart(self) -> None:
        ticker = self.ticker_var.get()
        period_label = self.period_var.get()

        try:
            dates, closes = self._fetcher.fetch_close_prices(ticker, period_label)
        except ValueError as exc:
            messagebox.showerror("資料錯誤", str(exc))
            return
        except OSError as exc:
            messagebox.showerror("網路錯誤", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("未知錯誤", f"發生未預期的錯誤：{exc}")
            return

        try:
            self._render_chart(ticker, period_label, dates, closes)
        except Exception as exc:
            messagebox.showerror("繪圖錯誤", f"無法繪製圖表：{exc}")

    def _clear_chart_area(self) -> None:
        if self._placeholder is not None:
            self._placeholder.destroy()
            self._placeholder = None

        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None

        if self._figure is not None:
            plt.close(self._figure)
            self._figure = None

        for widget in self.chart_frame.winfo_children():
            widget.destroy()

    def _render_chart(self, ticker: str, period_label: str, dates, closes) -> None:
        self._clear_chart_area()

        self._figure = Figure(figsize=(8, 4.5), dpi=100)
        ax = self._figure.add_subplot(111)
        ax.plot(dates, closes, color="#1f77b4", linewidth=1.5)
        ax.set_title(f"{ticker} 收盤價走勢（{period_label}）", fontsize=12)
        ax.set_xlabel("日期")
        ax.set_ylabel("收盤價")
        ax.grid(True, linestyle="--", alpha=0.5)
        self._figure.autofmt_xdate()
        self._figure.tight_layout()

        self._canvas = FigureCanvasTkAgg(self._figure, master=self.chart_frame)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = AppWindow()
    app.run()


if __name__ == "__main__":
    main()
