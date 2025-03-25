import os
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
import pandas as pd
from zoneinfo import ZoneInfo
import datetime
import re

def send_slack_message(text, attachments=None):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("SLACK_WEBHOOK_URL not set.")
        return
    payload = {
        "text": text
    }
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
        weekday_map = {0:"월", 1:"화", 2:"수", 3:"목", 4:"금", 5:"토", 6:"일"}
        weekday_korean = weekday_map[today.weekday()]
        date_str = f"{month_str}.{day_str}({weekday_korean})"

        options = Options()
        options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options)
        driver.get(self.url)

        # 드롭다운에서 오늘 월 선택
        select = Select(driver.find_element(By.ID, "ddlMonth"))
        select.select_by_value(month_str)

        # 경기 일정 테이블 가져오기
        table = driver.find_element(By.CLASS_NAME, "tbl-type06")
        thead = table.find_element(By.TAG_NAME, "thead")
        header = thead.text.split()
        tbody = table.find_element(By.TAG_NAME, "tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        if len(rows) == 1:
            driver.quit()
            print("경기 일정이 없습니다.")
            return None

        lines = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            schedule_list = [cell.text for cell in cells]
            lines.append(schedule_list)

        # 날짜가 누락된 행 처리 (rowspan 문제 보정)
        data = []
        game_day = None
        for line in lines:
            if line[0].endswith(')'):
                game_day = line[0]
                data.append(line)
            else:
                line.insert(0, game_day)
                data.append(line)

        df = pd.DataFrame(data, columns=header)
        df = df.replace('', '-')

        # JSON으로 저장 (필요 시)
        os.makedirs('./app/game_schedule', exist_ok=True)
        df.to_json(f'./app/game_schedule/{month_str}m_calender.json', force_ascii=False, orient='records', indent=4)

        # 오늘 날짜에 해당하는 행만 필터링
        today_df = df[df['날짜'].str.startswith(f"{month_str}.{day_str}")]
        header_print = f"[{today.year} {today.month}/{today.day} ({weekday_korean}) KBO 정규리그 경기 일정/결과]"
        
        # 메시지 구성: 기본 헤더 추가
        message_lines = [header_print, ""]
        
        if today_df.empty:
            message_lines.append("오늘 경기 일정이 없습니다.")
        else:
            for _, row in today_df.iterrows():
                match_text = row['경기']
                # 결과가 있을 경우: 예시 "한화\n0 vs\n5\nLG"
                if 'vs' in match_text:
                    cleaned_text = re.sub(r'\s+', ' ', match_text.replace("\n", " ")).strip()
                    parts = cleaned_text.split("vs")
                    if len(parts) == 2:
                        left = parts[0].strip()
                        right = parts[1].strip()
                        # 경기 결과(스코어)가 포함된 경우와 아직 결과가 없는 경우를 구분
                        if any(char.isdigit() for char in cleaned_text):
                            message_lines.append(f"{left} : {right}")
                        else:
                            message_lines.append(f"{left} : 경기 예정")
                else:
                    message_lines.append(match_text)
        
        driver.quit()
        # 최종 메시지 문자열 생성
        final_message = "\n".join(message_lines)
        return final_message

if __name__ == "__main__":
    crawler = GameCalCrawler()
    slack_message = crawler.crawling()
    if slack_message:
        # 현재 시간에 따라 오전 9시(경기 일정)와 오후 11시(경기 결과)로 구분하여 메시지를 보낼 수 있습니다.
        now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
        # 예시: 오전 9시 이전이면 경기 일정만, 오후 11시 이후면 경기 결과(스코어 포함) 전송
        if now.hour < 12:
            # 오전에는 경기 결과가 없으므로 일정만 보냄
            send_slack_message("🏟️ [KBO 경기 일정 안내]", attachments=[{"text": slack_message}])
        else:
            # 오후 11시에는 경기 결과를 포함하여 보냄
            send_slack_message("📊 [KBO 경기 결과 안내]", attachments=[{"text": slack_message}])
