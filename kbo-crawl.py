import os
import datetime
import re
from zoneinfo import ZoneInfo

import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


def send_slack_message(message):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("SLACK_WEBHOOK_URL not set.")
        return
    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload)
        print("Slack response:", response.text)
    except Exception as e:
        print("Failed to send Slack message:", str(e))


class GameCalCrawler:
    url = "https://www.koreabaseball.com/Schedule/Schedule.aspx"

    def crawling(self, mode="schedule"):
        now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
        month_str = f"{now.month:02d}"
        day_str = f"{now.day:02d}"
        weekday_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
        weekday_korean = weekday_map[now.weekday()]

        options = Options()
        options.binary_location = "/usr/bin/chromium-browser"
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)
        driver.get(self.url)

        # 드롭다운에서 현재 월 선택
        select = Select(driver.find_element(By.ID, "ddlMonth"))
        select.select_by_value(month_str)

        # 경기 일정 테이블 가져오기
        table = driver.find_element(By.CLASS_NAME, "tbl-type06")
        header = table.find_element(By.TAG_NAME, "thead").text.split()
        tbody = table.find_element(By.TAG_NAME, "tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        if len(rows) == 1:
            driver.quit()
            print("경기 일정이 없습니다.")
            return None

        lines = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            lines.append([cell.text for cell in cells])

        # rowspan 문제 보정
        data = []
        game_day = None
        for line in lines:
            if line[0].endswith(')'):
                game_day = line[0]
                data.append(line)
            else:
                line.insert(0, game_day)
                data.append(line)

        driver.quit()

        try:
            df = pd.DataFrame(data, columns=header).replace('', '-')
        except Exception as e:
            print("DataFrame 생성 오류:", e)
            return None

        # 오늘 날짜 필터
        today_df = df[df['날짜'].str.startswith(f"{month_str}.{day_str}")]
        if today_df.empty:
            return f"[{now.year} {now.month}/{now.day} ({weekday_korean})] 경기 정보가 없습니다."

        if mode == "result":
            # 경기 결과 모드
            header_msg = f"[{now.year} {now.month}/{now.day} ({weekday_korean}) KBO 정규리그 경기 결과]"
            game_lines = []

            for _, row in today_df.iterrows():
                game_text = row.get("경기", "").strip()

                # 유효성 검사
                if not isinstance(game_text, str):
                    continue
                if "vs" not in game_text:
                    continue
                if not any(char.isdigit() for char in game_text):
                    continue

                try:
                    cleaned = re.sub(r'\s+', ' ', game_text.replace("\n", " ")).strip()
                    parts = cleaned.split("vs")
                    if len(parts) == 2:
                        left = parts[0].strip()
                        right = parts[1].strip()
                        left = re.sub(r'(\D)(\d)', r'\1 \2', left)
                        right = re.sub(r'(\d)(\D)', r'\1 \2', right)
                        game_lines.append(f"{left} : {right}")
                except Exception as e:
                    print(f"[⚠️ 파싱 에러] '{game_text}' / {e}")
                    continue

            if not game_lines:
                game_lines.append("오늘 경기 결과가 없습니다.")
            return header_msg + "\n\n" + "\n".join(game_lines)

        else:
            # 중계 일정 모드
            header_msg = f"[{now.year} KBO 정규리그 경기 중계 일정]"
            subheader = f"{int(month_str)}월 {int(day_str)}일 {weekday_korean}요일 KBO 리그 인터넷/모바일 생중계는 TVING 에서!"
            game_lines = []

            for _, row in today_df.iterrows():
                time_info = row.get("시간", "").strip()
                game_info = row.get("경기", "").strip()
                if not game_info or "vs" not in game_info:
                    continue
                game_info = re.sub(r'\s*vs\s*', ' vs ', game_info)
                game_lines.append(f"{time_info} {game_info}")

            if not game_lines:
                game_lines.append("오늘 경기 일정이 없습니다.")
            return header_msg + "\n" + subheader + "\n\n" + "\n".join(game_lines)


def main():
    crawler = GameCalCrawler()
    now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
    mode = "schedule" if now.hour < 12 else "result"
    slack_message = crawler.crawling(mode=mode)
    if slack_message:
        send_slack_message(slack_message)
    else:
        print("크롤링 결과가 없습니다.")


if __name__ == '__main__':
    main()
