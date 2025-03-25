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

    def crawling(self, mode="schedule"):
        """
        mode:
          - "schedule": 중계 일정 메시지 포맷
          - "result": 경기 결과 메시지 포맷
        """
        # 한국 기준 오늘 날짜 구하기
        now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
        month_str = f"{now.month:02d}"
        day_str = f"{now.day:02d}"
        weekday_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
        weekday_korean = weekday_map[now.weekday()]

        options = Options()
        options.binary_location = "/usr/bin/chromium-browser"  # 수정된 Chromium 바이너리 경로
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options)
        driver.get(self.url)

        # 드롭다운에서 현재 월 선택
        select = Select(driver.find_element(By.ID, "ddlMonth"))
        select.select_by_value(month_str)

        # 경기 일정 테이블 가져오기
        table = driver.find_element(By.CLASS_NAME, "tbl-type06")
        # 테이블 헤더(컬럼명)가 "날짜", "시간", "경기", ... 라고 가정합니다.
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
            # 각 행의 텍스트를 리스트로 저장
            lines.append([cell.text for cell in cells])

        # rowspan 문제 보정: 날짜가 누락된 경우 이전 행의 날짜를 채워 넣음
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

        # 오늘 날짜에 해당하는 행 필터링 (날짜 형식이 "MM.DD(요일)"로 시작한다고 가정)
        today_df = df[df['날짜'].str.startswith(f"{month_str}.{day_str}")]
        if mode == "result":
            # 경기 결과 메시지 포맷
            header_msg = f"[{now.year} {now.month}/{now.day} ({weekday_korean}) KBO 정규리그 경기 결과]"
            game_lines = []
            # 결과가 있는 경우(숫자 포함)만 출력
            for _, row in today_df.iterrows():
                game_text = row.get("경기", "")
                # 만약 경기 텍스트에 숫자가 포함되어 있으면 결과로 간주
                if any(char.isdigit() for char in game_text):
                    cleaned = re.sub(r'\s+', ' ', game_text.replace("\n", " ")).strip()
                    # 예상 포맷: "한화 0 vs 5 LG" → "한화 0 : 5 LG"
                    parts = cleaned.split("vs")
                    if len(parts) == 2:
                        left = parts[0].strip()
                        right = parts[1].strip()
                        game_lines.append(f"{left} : {right}")
            if not game_lines:
                game_lines.append("오늘 경기 결과가 없습니다.")
            return header_msg + "\n\n" + "\n".join(game_lines)
        else:
            # 경기 중계 일정 메시지 포맷
            header_msg = f"[{now.year} KBO 정규리그 경기 중계 일정]"
            subheader = f"{int(month_str)}월 {int(day_str)}일 {weekday_korean}요일 KBO 리그 인터넷/모바일 생중계는 TVING 에서!"
            game_lines = []
            for _, row in today_df.iterrows():
                # "시간"과 "경기" 컬럼을 사용 (예: "13:00"과 "NC 다이노스 VS LG 트윈스")
                time_info = row.get("시간", "").strip()
                game_info = row.get("경기", "").strip()
                if game_info:
                    game_lines.append(f"{time_info} {game_info}")
            if not game_lines:
                game_lines.append("오늘 경기 일정이 없습니다.")
            return header_msg + "\n" + subheader + "\n\n" + "\n".join(game_lines)

def main():
    crawler = GameCalCrawler()
    now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
    # 오전 9시 이전은 중계 일정, 그 이후는 경기 결과 (예시)
    if now.hour < 12:
        mode = "schedule"
    else:
        mode = "result"
    slack_message = crawler.crawling(mode=mode)
    if slack_message:
        if mode == "schedule":
            send_slack_message("", attachments=[{"text": slack_message}])
        else:
            send_slack_message("", attachments=[{"text": slack_message}])
    else:
        print("크롤링 결과가 없습니다.")

if __name__ == '__main__':
    main()
