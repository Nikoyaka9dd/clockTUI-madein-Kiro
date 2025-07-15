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

        # アナログ時計の設定
        self.clock_radius = 10
        self.width = self.clock_radius * 4  # 横幅を広くして円形に近づける
        self.height = self.clock_radius * 2 + 1
        self.center_x = self.width // 2
        self.center_y = self.height // 2

    def clear_screen(self):
        """画面をクリア"""
        print(self.CLEAR_SCREEN + self.MOVE_CURSOR, end="")

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
            if 0 <= y < self.height and 0 <= x < self.width:
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

    def create_clock_face(self, hour: int, minute: int, second: int) -> List[str]:
        """アナログ時計の文字盤を作成"""
        clock = [[" " for _ in range(self.width)] for _ in range(self.height)]

        # 時計の外枠を描画（楕円補正）
        for i in range(self.height):
            for j in range(self.width):
                # 楕円の方程式を使用して円形に近づける
                dx = (j - self.center_x) / 2.0  # 横方向を半分に圧縮
                dy = i - self.center_y
                distance = math.sqrt(dx * dx + dy * dy)

                if abs(distance - self.clock_radius) < 0.8:
                    clock[i][j] = "█"

        # 12時間の目盛りを描画
        for h in range(12):
            angle = h * 30  # 30度ずつ
            # 楕円補正を適用した位置計算
            adjusted_angle = angle - 90
            radian = math.radians(adjusted_angle)

            mark_x = self.center_x + int((self.clock_radius - 1) * math.cos(radian) * 2)
            mark_y = self.center_y + int((self.clock_radius - 1) * math.sin(radian))

            if 0 <= mark_y < self.height and 0 <= mark_x < self.width:
                if h == 0:  # 12時
                    if mark_x + 1 < self.width:
                        clock[mark_y][mark_x] = "1"
                        clock[mark_y][mark_x + 1] = "2"
                    else:
                        clock[mark_y][mark_x] = "12"[0]
                elif h == 3:  # 3時
                    clock[mark_y][mark_x] = "3"
                elif h == 6:  # 6時
                    clock[mark_y][mark_x] = "6"
                elif h == 9:  # 9時
                    clock[mark_y][mark_x] = "9"
                else:
                    clock[mark_y][mark_x] = "•"

        # 針の角度を計算
        hour_angle = (hour % 12) * 30 + minute * 0.5  # 時針
        minute_angle = minute * 6  # 分針
        second_angle = second * 6  # 秒針

        # 時針を描画（短い）
        hour_radian = math.radians(hour_angle - 90)
        hour_x = self.center_x + int(
            self.clock_radius * 0.5 * math.cos(hour_radian) * 2
        )
        hour_y = self.center_y + int(self.clock_radius * 0.5 * math.sin(hour_radian))
        self.draw_line(clock, self.center_x, self.center_y, hour_x, hour_y, "│")

        # 分針を描画（長い）
        minute_radian = math.radians(minute_angle - 90)
        minute_x = self.center_x + int(
            self.clock_radius * 0.8 * math.cos(minute_radian) * 2
        )
        minute_y = self.center_y + int(
            self.clock_radius * 0.8 * math.sin(minute_radian)
        )
        self.draw_line(clock, self.center_x, self.center_y, minute_x, minute_y, "│")

        # 秒針を描画（最も長い、細い）
        second_radian = math.radians(second_angle - 90)
        second_x = self.center_x + int(
            self.clock_radius * 0.9 * math.cos(second_radian) * 2
        )
        second_y = self.center_y + int(
            self.clock_radius * 0.9 * math.sin(second_radian)
        )
        self.draw_line(clock, self.center_x, self.center_y, second_x, second_y, "│")

        # 中心点
        clock[self.center_y][self.center_x] = "●"

        # 文字列に変換
        return ["".join(row) for row in clock]

    def display_analog_clock(self, jst_time: datetime.datetime):
        """アナログ時計を表示"""
        hour = jst_time.hour
        minute = jst_time.minute
        second = jst_time.second

        clock_lines = self.create_clock_face(hour, minute, second)

        # ターミナル幅を取得して中央寄せ
        terminal_width = os.get_terminal_size().columns

        print(f"{self.BOLD}{self.BRIGHT_PURPLE}")
        for line in clock_lines:
            line_length = len(line)
            padding = (terminal_width - line_length) // 2
            print(f"{' ' * padding}{line}")
        print(self.RESET)

        # デジタル時刻も小さく表示
        time_str = jst_time.strftime("%H:%M:%S")
        padding = (terminal_width - len(time_str)) // 2
        print(f"{self.PURPLE}{' ' * padding}{time_str}{self.RESET}")

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
                self.display_analog_clock(jst_time)
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
