# ⚾ KBO 경기 일정 및 결과 Slack 알림 봇

> Selenium과 GitHub Actions를 활용하여 KBO 리그의 **경기 일정 및 결과**를 크롤링하고 Slack으로 전송하는 자동화 프로젝트입니다.

<br/>

## 🔍 프로젝트 소개

이 프로젝트는 매일 자동으로 KBO 홈페이지에서 그날의 **경기 일정**과 **경기 결과**를 크롤링하여 지정된 Slack 채널로 전송하는 기능을 구현한 개인 프로젝트입니다. **GitHub Actions**를 활용하여 서버 비용 없이 완전 자동화로 운영할 수 있도록 하였습니다.

- 웹 크롤링 및 데이터 처리 자동화
- CI/CD 및 작업 자동화 (GitHub Actions)
- Slack API를 활용한 알림 메시지 발송
- 셀레니움 헤드리스(Headless) 브라우저 자동화

<br/>

## 🖥️ 기술 스택

<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=Python&logoColor=white"/> <img src="https://img.shields.io/badge/Selenium-43B02A?style=flat-square&logo=Selenium&logoColor=white"/> <img src="https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=Pandas&logoColor=white"/> <img src="https://img.shields.io/badge/Requests-FF8C00?style=flat-square&logo=Python&logoColor=white"/> <img src="https://img.shields.io/badge/Slack-4A154B?style=flat-square&logo=Slack&logoColor=white"/> <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=GitHubActions&logoColor=white"/>

<br/>

## 📌 주요 기능

- **KBO 공식 홈페이지**에서 당일 경기 일정 및 결과 크롤링
- 매일 오전 9시 (경기 일정) / 오후 10시 (경기 결과) 자동 실행
- Slack API(Webhook)를 활용한 메시지 발송
- 별도의 서버 없이 GitHub Actions 활용한 완전 자동화

<br/>

## 📬 Slack 알림 메시지 예시

### 📅 경기 일정 알림 (오전 9시)

```
[2025 KBO 정규리그 경기 중계 일정]
3월 26일 수요일 KBO 리그 인터넷/모바일 생중계는 TVING 에서!

18:30 한화 vs LG
18:30 롯데 vs SSG
18:30 NC vs 삼성
18:30 두산 vs KT
18:30 키움 vs KIA
```

### 📊 경기 결과 알림 (오후 10시)

```
[2025 3/26 (수) KBO 정규리그 경기 결과]

한화 0 : 5 LG
롯데 3 : 2 SSG
NC 5 : 14 삼성
두산 3 : 8 KT
키움 6 : 11 KIA
```

<br/>

## ⚙️ 프로젝트 구조

```
kbo-score/
├── .github/
│   └── workflows/
│       └── kbo_crawler.yml     # GitHub Actions 워크플로우 파일
├── kbo-crawl.py                # 크롤링 및 Slack 메시지 전송 스크립트
├── README.md                   # 프로젝트 설명 및 문서
└── requirements.txt            # 의존성 목록
```

<br/>

## 🚀 사용 방법

### 1. Repository 클론하기
```bash
git clone https://github.com/your-username/kbo-score.git
cd kbo-score
```

### 2. Python 의존성 설치
```bash
pip install -r requirements.txt
```

`requirements.txt` 예시:
```
selenium
requests
pandas
```

### 3. Slack Webhook 설정
Slack에서 Incoming Webhook URL 생성 후  
**GitHub Repository → Settings → Secrets and variables → Actions**에서  
Secret으로 `SLACK_WEBHOOK_URL` 등록

### 4. GitHub Actions 설정
리포지토리에 포함된 `.github/workflows/kbo_crawler.yml` 파일이 자동으로 작동하여 매일 크롤링 작업을 실행합니다.

<br/>

## 📌 프로젝트를 통해 배운 점
- **Selenium**을 이용한 웹 페이지 자동 크롤링 경험
- **GitHub Actions**를 이용한 CI/CD 자동화 및 무료 서버리스 자동화 구성
- 다양한 Python 라이브러리(`requests`, `pandas`) 활용 및 데이터 가공 기술
- Slack API를 활용한 메시지 전송 자동화 구현

<br/>

## 🔖 참고 자료
- [Selenium 공식 문서](https://www.selenium.dev/documentation/)
- [GitHub Actions 공식 문서](https://docs.github.com/actions)
- [Slack API 사용법](https://api.slack.com/messaging/webhooks)

<br/>

## 📌 라이선스
이 프로젝트는 MIT 라이선스를 준수합니다.
