# 트럼프 관련 뉴스 자동 수집 및 분석 시스템

동아일보에서 트럼프 관련 뉴스를 자동으로 수집하고, OpenAI GPT를 활용해 분석한 후 Google 문서에 자동으로 정리하는 시스템입니다.

## 🚀 주요 기능

- **자동 뉴스 수집**: 동아일보에서 트럼프 관련 뉴스를 매일 자동 수집
- **AI 분석**: OpenAI GPT-4를 사용하여 뉴스 내용을 구조화된 JSON 형태로 분석
- **자동 문서화**: 분석 결과를 Google 문서에 자동으로 추가
- **스케줄링**: GitHub Actions를 통해 매일 자동 실행 (일요일 제외)
- **필터링**: 트럼프 미국 정책과 관련된 뉴스만 선별

## 📋 분석 항목

각 뉴스는 다음과 같은 구조로 분석됩니다:

```json
{
  "news-title": "기사 제목",
  "link": "기사 링크",
  "date": "발행일",
  "title": "정책 요약 제목",
  "korea": "한국에 미치는 영향 분석",
  "keywords": ["통상·경제", "외교"],
  "execute": "실행/예고 구분",
  "affectedCountries": [
    {
      "name": "국가명",
      "effect": "해당 국가에 미치는 영향"
    }
  ],
  "thumbnail_url": "썸네일 이미지 URL",
  "korea-level": "영향도 수준",
  "summary": "기사 요약"
}
```

## 🛠️ 설치 및 설정

### 1. Repository 클론

```bash
git clone <your-repository-url>
cd trump-issue-crawling
```

### 2. 필요한 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 3. Google Docs API 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트 생성
2. Google Docs API 활성화
3. 서비스 계정 생성 및 JSON 키 다운로드
4. 대상 Google 문서에 서비스 계정 이메일을 편집자로 공유

### 4. GitHub Secrets 설정

Repository Settings → Secrets and variables → Actions에서 다음 설정:

- `OPENAI_API_KEY`: OpenAI API 키
- `GOOGLE_CREDENTIALS`: 서비스 계정 JSON을 base64로 인코딩한 값

```bash
# base64 인코딩 방법
base64 -i path/to/service-account.json | tr -d '\n'
```

## 📅 스케줄링

- **실행 시간**: 매일 한국시간 오전 9시 (UTC 0시)
- **실행 요일**: 월요일 ~ 토요일 (일요일 제외)
- **자동 실행**: GitHub Actions를 통한 자동화
- **수동 실행**: GitHub Actions 탭에서 "Run workflow" 버튼으로 수동 실행 가능

## 🔧 로컬 테스트

### 방법 1: 환경변수 설정

```python
# test.py
import os

os.environ['OPENAI_API_KEY'] = 'your-openai-api-key'
# credentials.json 파일을 프로젝트 루트에 배치

from auto_enhanced import job

if __name__ == "__main__":
    print("로컬 테스트 시작...")
    job()
    print("로컬 테스트 완료!")
```

### 방법 2: 직접 실행

```bash
python auto_enhanced.py
```

## 📁 파일 구조

```
trump-issue-crawling/
├── .github/
│   └── workflows/
│       └── auto-news.yml          # GitHub Actions 워크플로우
├── auto_enhanced.py               # 메인 스크립트 (GitHub Actions용)
├── auto.py                       # 원본 스크립트
├── requirements.txt              # 의존성 패키지
├── test.py                      # 로컬 테스트용 스크립트
├── credentials.json             # Google 서비스 계정 키 (로컬용)
└── README.md                    # 프로젝트 문서
```

## ⚙️ 주요 설정값

### 대상 웹사이트
- **기본 URL**: `https://www.donga.com/news?ymd=YYYYMMDD`
- **선택자**: `#list_tab1 .desc_list li a`

### 필터링 조건
- 기사 본문에 "트럼프" 키워드 포함
- 제목에 "美" 또는 "트럼프" 포함
- 사설, 횡설수설, 오늘과 내일 제외

### Google 문서 업데이트
- **문서 ID**: `1T5HLtyZF0dQ4jceUP02Xx1nL3zMInndibLGlTx-VMwI`
- **추가 위치**: 문서 맨 아래
- **제목 형식**: "MMDD" (예: "0908")
- **내용 형식**: JSON 구조

## 🐛 문제 해결

### 일반적인 오류들

1. **OpenAI API 오류**
   - API 키 확인
   - 크레딧 잔액 확인

2. **Google API 오류**
   - 서비스 계정 권한 확인
   - 문서 공유 설정 확인

3. **크론 스케줄 오류**
   - UTC 시간 기준 확인 (한국시간 -9시간)

### 로그 확인

- GitHub Actions 실행 결과는 Actions 탭에서 확인
- 각 step별 상세 로그 제공
- 실패 시 오류 메시지 확인 가능

## 🔄 워크플로우

1. **뉴스 수집**: 동아일보에서 해당 날짜 뉴스 링크 수집
2. **필터링**: 트럼프 관련 뉴스만 선별
3. **내용 추출**: 기사 제목, 본문, 메타데이터 추출
4. **AI 분석**: OpenAI GPT-4로 구조화된 분석 수행
5. **문서 업데이트**: Google 문서에 결과 자동 추가

## 📊 키워드 분류

- **문화**: 문화 정책, 교육 관련
- **외교**: 외교 정책, 국제 관계
- **이민**: 이민 정책, 비자 관련
- **법·행정**: 법률, 행정 조치
- **통상·경제**: 무역, 경제 정책

## 🚨 주의사항

- OpenAI API 사용량에 따른 비용 발생 가능
- Google Docs API 할당량 제한 확인 필요
- GitHub Actions 무료 사용량 제한 (public repo: 월 2,000분)
- 웹사이트 구조 변경 시 선택자 업데이트 필요

## 📞 지원

문제가 발생하거나 개선사항이 있으면 이슈를 등록해주세요.

## 📄 라이선스

이 프로젝트는 개인 사용 목적으로 제작되었습니다.