#!/usr/bin/env python3
"""
日本標準時（JST）TUIアナログ時計
紫と黒の配色でリアルタイム表示
"""

import time
import datetime
import os
import sys
import math
import psutil
from collections import deque
from typing import List, Tuple


class JSTClock:
    def __init__(self):
        # ANSI カラーコード
        self.PURPLE = "\033[95m"
        self.BRIGHT_PURPLE = "\033[35m"
        self.BLACK = "\033[30m"
        self.BG_BLACK = "\033[40m"
        self.BG_PURPLE = "\033[45m"
        self.RESET = "\033[0m"
        self.BOLD = "\033[1m"
        self.CLEAR_SCREEN = "\033[2J"
        self.MOVE_CURSOR = "\033[H"

        # アナログ時計の設定（小さく円形に）
        self.clock_radius = 5
        self.clock_width = self.clock_radius * 2 + 3
        self.clock_height = self.clock_radius * 2 + 3
        self.center_x = self.clock_width // 2
        self.center_y = self.clock_height // 2

        # システム監視の設定
        self.graph_width = 40
        self.graph_height = 12
        self.cpu_history = deque(maxlen=self.graph_width)
        self.memory_history = deque(maxlen=self.graph_width)

        # 初期データを0で埋める
        for _ in range(self.graph_width):
            self.cpu_history.append(0)
            self.memory_history.append(0)

    def clear_screen(self):
        """画面をクリア"""
        # より確実な画面クリア
        os.system("clear" if os.name == "posix" else "cls")

    def get_jst_time(self) -> datetime.datetime:
        """日本標準時を取得"""
        # UTCから9時間進める（JST = UTC+9）
        utc_now = datetime.datetime.utcnow()
        jst_now = utc_now + datetime.timedelta(hours=9)
        return jst_now

    def get_hand_position(self, angle: float, length: float) -> Tuple[int, int]:
        """針の位置を計算"""
        # 角度を調整（12時を0度とし、時計回りに進む）
        adjusted_angle = angle - 90
        radian = math.radians(adjusted_angle)

        x = self.center_x + int(length * math.cos(radian))
        y = self.center_y + int(length * math.sin(radian))

        return x, y

    def draw_line(
        self, clock: List[List[str]], x1: int, y1: int, x2: int, y2: int, char: str
    ):
        """2点間に線を描画"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        x_inc = 1 if x1 < x2 else -1
        y_inc = 1 if y1 < y2 else -1
        error = dx - dy

        while True:
            if 0 <= y < self.clock_height and 0 <= x < self.clock_width:
                clock[y][x] = char

            if x == x2 and y == y2:
                break

            e2 = 2 * error
            if e2 > -dy:
                error -= dy
                x += x_inc
            if e2 < dx:
                error += dx
                y += y_inc

    def get_system_stats(self):
        """システム使用率を取得"""
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_percent = psutil.virtual_memory().percent

        self.cpu_history.append(cpu_percent)
        self.memory_history.append(memory_percent)

        return cpu_percent, memory_percent

    def create_graph(self, data: deque, title: str, color: str) -> List[str]:
        """折れ線グラフを作成"""
        graph = [
            [" " for _ in range(self.graph_width + 10)]
            for _ in range(self.graph_height + 3)
        ]

        # タイトル
        title_line = f"{color}{title}{self.RESET}"
        for i, char in enumerate(title):
            if i < len(title):
                graph[0][i] = char

        # Y軸の目盛り（0-100%）
        for i in range(self.graph_height):
            y_value = 100 - (i * 100 // (self.graph_height - 1))
            y_label = f"{y_value:3d}%"
            for j, char in enumerate(y_label):
                if j < 4:
                    graph[i + 2][j] = char

        # グラフの枠
        for i in range(self.graph_height):
            graph[i + 2][5] = "│"

        for j in range(self.graph_width):
            graph[self.graph_height + 1][j + 6] = "─"

        # データをプロット
        if len(data) > 1:
            for i in range(1, len(data)):
                if data[i - 1] is not None and data[i] is not None:
                    # Y座標を計算（上下反転）
                    y1 = (
                        self.graph_height
                        - int((data[i - 1] / 100) * (self.graph_height - 1))
                        + 1
                    )
                    y2 = (
                        self.graph_height
                        - int((data[i] / 100) * (self.graph_height - 1))
                        + 1
                    )

                    x1 = i - 1 + 6
                    x2 = i + 6

                    # 線を描画
                    if (
                        0 <= y1 < self.graph_height + 2
                        and 0 <= y2 < self.graph_height + 2
                    ):
                        if abs(y2 - y1) <= 1:
                            # 水平に近い場合
                            if x2 < self.graph_width + 6:
                                graph[y2][x2] = "●"
                        else:
                            # 垂直線を描画
                            start_y = min(y1, y2)
                            end_y = max(y1, y2)
                            for y in range(start_y, end_y + 1):
                                if (
                                    y < self.graph_height + 2
                                    and x2 < self.graph_width + 6
                                ):
                                    graph[y][x2] = "│"

        # 文字列に変換
        return ["".join(row).rstrip() for row in graph]

    def create_clock_face(self, hour: int, minute: int, second: int) -> List[str]:
        """アナログ時計の文字盤を作成"""
        clock = [
            [" " for _ in range(self.clock_width)] for _ in range(self.clock_height)
        ]

        # 時計の外枠を描画（真円に近づける）
        for i in range(self.clock_height):
            for j in range(self.clock_width):
                dx = j - self.center_x
                dy = i - self.center_y
                distance = math.sqrt(dx * dx + dy * dy)

                if abs(distance - (self.clock_radius - 1)) < 0.6:
                    clock[i][j] = "●"

        # 主要な時刻のみ表示（12, 3, 6, 9時）
        main_hours = [0, 3, 6, 9]
        for h in main_hours:
            angle = h * 30
            radian = math.radians(angle - 90)

            mark_x = self.center_x + int((self.clock_radius - 2) * math.cos(radian))
            mark_y = self.center_y + int((self.clock_radius - 2) * math.sin(radian))

            if 0 <= mark_y < self.clock_height and 0 <= mark_x < self.clock_width:
                if h == 0:
                    clock[mark_y][mark_x] = "12"[0]
                    if mark_x + 1 < self.clock_width:
                        clock[mark_y][mark_x + 1] = "12"[1]
                else:
                    clock[mark_y][mark_x] = str(h if h != 0 else 12)

        # 針の角度を計算
        hour_angle = (hour % 12) * 30 + minute * 0.5
        minute_angle = minute * 6
        second_angle = second * 6

        # 時針を描画（短い）
        hour_radian = math.radians(hour_angle - 90)
        hour_x = self.center_x + int(self.clock_radius * 0.4 * math.cos(hour_radian))
        hour_y = self.center_y + int(self.clock_radius * 0.4 * math.sin(hour_radian))
        self.draw_line(clock, self.center_x, self.center_y, hour_x, hour_y, "━")

        # 分針を描画（長い）
        minute_radian = math.radians(minute_angle - 90)
        minute_x = self.center_x + int(
            self.clock_radius * 0.7 * math.cos(minute_radian)
        )
        minute_y = self.center_y + int(
            self.clock_radius * 0.7 * math.sin(minute_radian)
        )
        self.draw_line(clock, self.center_x, self.center_y, minute_x, minute_y, "─")

        # 秒針を描画（最も長い、細い）
        second_radian = math.radians(second_angle - 90)
        second_x = self.center_x + int(
            self.clock_radius * 0.8 * math.cos(second_radian)
        )
        second_y = self.center_y + int(
            self.clock_radius * 0.8 * math.sin(second_radian)
        )
        self.draw_line(clock, self.center_x, self.center_y, second_x, second_y, "│")

        # 中心点
        clock[self.center_y][self.center_x] = "●"

        # 文字列に変換
        return ["".join(row) for row in clock]

    def display_split_screen(self, jst_time: datetime.datetime):
        """画面を分割して時計とグラフを表示"""
        # システム使用率を取得
        cpu_percent, memory_percent = self.get_system_stats()

        # 時計を作成
        hour = jst_time.hour
        minute = jst_time.minute
        second = jst_time.second
        clock_lines = self.create_clock_face(hour, minute, second)

        # 時計の下にデジタル時刻とタイムゾーンを追加
        time_str = jst_time.strftime("%H:%M:%S")
        timezone_str = "JST (UTC+9)"
        clock_lines.append("")
        clock_lines.append(f"{self.PURPLE}{time_str}{self.RESET}")
        clock_lines.append(f"{self.BRIGHT_PURPLE}{timezone_str}{self.RESET}")

        # 時計セクションを固定の高さにする
        clock_section = [
            f"{self.BRIGHT_PURPLE}【アナログ時計】{self.RESET}"
        ] + clock_lines

        # 時計セクションを固定の高さ（15行）にパディング
        clock_fixed_height = 15
        while len(clock_section) < clock_fixed_height:
            clock_section.append("")

        # グラフを作成
        cpu_graph = self.create_graph(
            self.cpu_history, f"CPU: {cpu_percent:.1f}%", self.BRIGHT_PURPLE
        )
        memory_graph = self.create_graph(
            self.memory_history, f"Memory: {memory_percent:.1f}%", self.PURPLE
        )

        # CPUグラフにタイトルを追加
        cpu_section = [f"{self.BRIGHT_PURPLE}【CPU使用率】{self.RESET}"] + cpu_graph

        # メモリグラフにタイトルを追加
        memory_section = [f"{self.PURPLE}【メモリ使用率】{self.RESET}"] + memory_graph

        # 各セクションの幅を設定
        clock_width = 20
        graph_width = 55

        # 最大行数を計算（時計セクションは固定高さを使用）
        max_lines = max(clock_fixed_height, len(cpu_section), len(memory_section))

        print(f"{self.BOLD}")
        for i in range(max_lines):
            line_parts = []

            # 左側：時計（固定高さ）
            if i < len(clock_section):
                clock_content = clock_section[i]
            else:
                clock_content = ""
            line_parts.append(clock_content.ljust(clock_width))

            # 区切り文字
            line_parts.append(" │ ")

            # 中央：CPUグラフ
            if i < len(cpu_section):
                cpu_content = cpu_section[i]
            else:
                cpu_content = ""
            line_parts.append(cpu_content.ljust(graph_width))

            # 区切り文字
            line_parts.append(" │ ")

            # 右側：メモリグラフ
            if i < len(memory_section):
                memory_content = memory_section[i]
            else:
                memory_content = ""
            line_parts.append(memory_content)

            # 行を結合して表示
            print("".join(line_parts))

        print(self.RESET)

    def display_date_info(self, jst_time: datetime.datetime):
        """日付情報を表示"""
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        weekday = weekdays[jst_time.weekday()]

        date_str = f"{jst_time.year}年{jst_time.month}月{jst_time.day}日 ({weekday})"

        # 中央揃えで表示
        terminal_width = os.get_terminal_size().columns
        padding = (terminal_width - len(date_str)) // 2

        print(f"{self.PURPLE}{' ' * padding}{date_str}{self.RESET}")
        print()

    def display_header(self):
        """ヘッダーを表示"""
        header = "🕐 日本標準時 (JST) 🕐"
        terminal_width = os.get_terminal_size().columns
        padding = (terminal_width - len(header)) // 2

        print(f"{self.BG_PURPLE}{self.BLACK}{self.BOLD}")
        print(f"{' ' * terminal_width}")
        print(
            f"{' ' * padding}{header}{' ' * (terminal_width - padding - len(header))}"
        )
        print(f"{' ' * terminal_width}")
        print(self.RESET)
        print()

    def display_footer(self):
        """フッターを表示"""
        footer = "Ctrl+C で終了"
        terminal_width = os.get_terminal_size().columns
        padding = (terminal_width - len(footer)) // 2

        print()
        print(f"{self.PURPLE}{' ' * padding}{footer}{self.RESET}")

    def run(self):
        """メインループ"""
        try:
            while True:
                self.clear_screen()

                # 現在のJST時刻を取得
                jst_time = self.get_jst_time()

                # 表示
                self.display_date_info(jst_time)
                self.display_split_screen(jst_time)
                self.display_footer()

                # 1秒待機
                time.sleep(1)

        except KeyboardInterrupt:
            self.clear_screen()
            print(f"{self.PURPLE}時計を終了しました。{self.RESET}")
            sys.exit(0)


def main():
    """メイン関数"""
    clock = JSTClock()
    clock.run()


if __name__ == "__main__":
    main()
