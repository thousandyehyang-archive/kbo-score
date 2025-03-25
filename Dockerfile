FROM python:3.9-slim

# 필수 패키지 업데이트 및 설치
RUN apt-get update && apt-get install -y wget gnupg unzip curl

# Chromium 및 Chromedriver 설치
RUN apt-get install -y chromium-driver chromium

# 환경 변수 설정 (Selenium이 Chromium을 찾도록)
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .

CMD ["python", "kbo-crawl.py"]