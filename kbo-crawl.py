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

def send_slack_message(text, attachments=None):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("SLACK_WEBHOOK_URL not set.")
        return
    payload = {"text": text}
    if attachments:
        payload["attachments"] = attachments
    try:
        response = requests.post(webhook_url, json=payload)
        print("Slack response:", response.text)
    except Exception as e:
        print("Failed to send Slack message:", str(e))

class GameCalCrawler:
    url = "https://www.koreabaseball.com/Schedule/Schedule.aspx"

    def crawling(self):
        # 한국 기준 오늘 날짜 구하기
        today = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
        month_str = f"{today.month:02d}"
        day_str = f"{today.day:02d}"
        weekday_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
        weekday_korean = weekday_map[today.weekday()]

        options = Options()
        options.binary_location = "/usr/bin/chromium-browser"  # 수정된 바이너리 경로
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
        rows = table.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        if len(rows) == 1:
            driver.quit()
            print("경기 일정이 없습니다.")
            return None

        lines = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            lines.append([cell.text for cell in cells])

        # rowspan 문제 보정: 날짜가 누락된 경우 이전 행의 날짜로 채움
        data = []
        game_day = None
        for line in lines:
            if line[0].endswith(')'):
                game_day = line[0]
                data.append(line)
            else:
                line.insert(0, game_day)
                data.append(line)

        df = pd.DataFrame(data, columns=header).replace('', '-')

        # 오늘 날짜에 해당하는 행 필터링
        today_df = df[df['날짜'].str.startswith(f"{month_str}.{day_str}")]
        header_print = f"[{today.year} {today.month}/{today.day} ({weekday_korean}) KBO 정규리그 경기 일정/결과]"

        message_lines = [header_print, ""]
        if today_df.empty:
            message_lines.append("오늘 경기 일정이 없습니다.")
        else:
            for _, row in today_df.iterrows():
                match_text = row['경기']
                if 'vs' in match_text:
                    cleaned_text = re.sub(r'\s+', ' ', match_text.replace("\n", " ")).strip()
                    parts = cleaned_text.split("vs")
                    if len(parts) == 2:
                        left, right = parts[0].strip(), parts[1].strip()
                        if any(char.isdigit() for char in cleaned_text):
                            message_lines.append(f"{left} : {right}")
                        else:
                            message_lines.append(f"{left} : 경기 예정")
                else:
                    message_lines.append(match_text)
        driver.quit()
        return "\n".join(message_lines)

def main():
    crawler = GameCalCrawler()
    slack_message = crawler.crawling()
    if slack_message:
        now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
        if now.hour < 12:
            send_slack_message("[KBO 경기 일정 안내]", attachments=[{"text": slack_message}])
        else:
            send_slack_message("[KBO 경기 결과 안내]", attachments=[{"text": slack_message}])
    else:
        print("크롤링 결과가 없습니다.")

if __name__ == '__main__':
    main()
