import requests
from bs4 import BeautifulSoup
import json
from openai import OpenAI
from datetime import datetime, timedelta
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle

# Google Docs API 설정
SCOPES = ['https://www.googleapis.com/auth/documents']
DOCUMENT_ID = '1T5HLtyZF0dQ4jceUP02Xx1nL3zMInndibLGlTx-VMwI'

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_google_docs_service():
    """Google Docs API 서비스 객체 반환"""
    creds = None
    
    # GitHub Actions에서 실행되는 경우
    if os.getenv('GOOGLE_CREDENTIALS'):
        import tempfile
        import base64
        
        # base64로 인코딩된 credentials를 디코드
        creds_data = base64.b64decode(os.getenv('GOOGLE_CREDENTIALS'))
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            temp_file.write(creds_data)
            temp_file_path = temp_file.name
        
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            temp_file_path, scopes=SCOPES)
        
        os.unlink(temp_file_path)
    
    # 로컬에서 실행되는 경우 (개발용)
    else:
        from google.oauth2 import service_account
        
        # 로컬에 credentials.json 파일이 있는 경우
        if os.path.exists('credentials.json'):
            creds = service_account.Credentials.from_service_account_file(
                'credentials.json', scopes=SCOPES)
        else:
            raise FileNotFoundError("Google credentials not found. Set GOOGLE_CREDENTIALS environment variable or place credentials.json file.")
    
    service = build('docs', 'v1', credentials=creds)
    return service

def get_target_date():
    today = datetime.now()
    return today.strftime('%Y%m%d'), today.strftime('%m%d')

def fetch_links(date_str):
    """특정 날짜의 뉴스 링크들을 가져옴"""
    base_url = "https://www.donga.com"
    url = f"{base_url}/news?ymd={date_str}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    links = []
    for a in soup.select("#list_tab1 .desc_list li a"):
        href = a.get("href")
        if not href:
            continue
        if href.startswith("javascript"):
            continue
        if href.startswith("/"):
            links.append(base_url + href)
        elif href.startswith("http"):
            links.append(href)

    return links

def filter_article(url):
    """기사 필터링 및 정보 추출 (기존 코드와 동일)"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    article_body = soup.select_one(".news_view")
    if not article_body:
        return None

    for ad in article_body.select(".ad"):
        ad.decompose()

    content = article_body.get_text(separator=" ", strip=True)

    if not ("트럼프" in content):
        return None

    title_tag = soup.select_one("meta[property='og:title']")
    title = title_tag["content"] if title_tag else ""

    if not ("美" in title or "트럼프" in title):
        return None
    if ("사설" in title or "횡설수설" in title or "오늘과 내일" in title):
        return None

    thumbnail_tag = soup.select_one("meta[property='og:image']")
    thumbnail_url = thumbnail_tag["content"] if thumbnail_tag else ""

    date_tag = soup.select_one("meta[property='og:pubdate']")
    date = date_tag.get_text(strip=True) if date_tag else ""

    return {
        "link": url,
        "news-title": title,
        "date": date,
        "thumbnail_url": thumbnail_url,
        "content": content
    }

def process_article(info):
    """기사 처리 (기존 코드와 동일)"""
    prompt = f"""
        입력:
        뉴스 제목: {info["news-title"]}
        링크: {info["link"]}
        날짜: {info["date"]}
        인네일: {info["thumbnail_url"]}
        기사 본문:
        \"\"\"
        {info["content"]}
        \"\"\"

        먼저 기사 본문을 파악해서 만약 이 기사가 트럼프의 미국 정책과 무관하다면, JSON을 생성하지 말고 '무관'이라고만 답해줘.
        하지만 기사 본문이 트럼프의 미국 정책에 관한 내용이라면 입력 내용을 바탕으로 아래의 규칙과 형식에 맞춰 **논리적이고 압축적**인 스타일로 JSON 데이터를 생성해줘.
        
        ## 예시 1:
        입력 기사: https://www.donga.com/news/Inter/article/all/20250305/131152223/2
        
        출력 JSON:
        {{
            "news-title": "‛車수출 절반 美의존' 한국 비상… 美 "4월 2일부터 車관세"",
            "link": "https://www.donga.com/news/Inter/article/all/20250217/131042059/2",
            "date": "2025-02-17",
            "title": "수입 자동차에 대한 관세 부과 결정으로 글로벌 자동차 업계 긴장",
            "korea": "한국 자동차 업계는 전체 수출의 절반 가까이를 미국에 보내고 있어, 이번 자동차 관세 부과가 현실화되면 생산·수출 전반에 큰 충격이 예상됨. 현대차·기아 등 완성차 기업뿐 아니라, 30만 명 이상이 종사하는 부품 협력업체들까지 타격을 받을 수 있음. 특히 미국 현지 공장을 보유하지 않은 중소 브랜드는 가격 경쟁력을 잃고 시장 철수 위기에 놓일 수도 있음. 정부와 업계는 현지 생산 확대나 외교적 예외 협상 등을 검토 중이나, 단기간 대응은 쉽지 않을 전망임.",
            "keywords": [
                "통상·경제",
                "외교"
            ],
            "execute": "예고",
            "affectedCountries": [
                {{
                    "name": "일본",
                    "effect": "미국 자동차 시장에 대한 의존도가 높은 국가 중 하나. 특히 일본은 트럼프 1기 당시부터 자동차 관세 압박을 반복적으로 받아온 경험이 있어, 이번 조치가 본격화될 경우 다시 한 번 미일 무역 마찰이 격화될 가능성이 있음. 일본 기업들도 현지 공장 가동률을 끌어올리거나, 멕시코 공장을 통한 우회 수출 방식에 제약이 생길 수 있음."
                }},
                {{
                    "name": "독일",
                    "effect": "이미 전기차 전환 부담을 안고 있는 독일 자동차 산업은 가격 인상, 수익성 악화, 북미 전략 수정 등 복합적 대응이 불가피할 전망임. EU 차원에서는 WTO 제소나 맞대응 관세 검토 가능성도 거론되고 있음."
                }}
            ],
            "thumbnail_url": "https://dimg.donga.com/wps/NEWS/IMAGE/2025/02/17/131042307.1.jpg",
            "korea-level": "직접적",
            "summary": "트럼프 미국 대통령이 오는 4월 2일부터 수입 자동차에 대해 25%의 관세를 부과하겠다고 밝혔다. 한국 자동차 업계는 전체 수출의 절반 이상이 미국에 집중돼 있어 타격이 불가피하다는 우려가 제기됐다."
        }}
        
        **주의사항 및 작성 규칙**:
        1. 모든 본문 내용은 '~함, ~임'의 보고체로 작성할 것. 단, summary는 신문기사체로 2~3문장.
        2. 'title'의 첫 단어는 '미국', '트럼프' 등이 오지 않도록 주의.
        3. 'korea'와 'effect'는 수치, 기업명, 정책명 등을 포함한 구체적인 영향을 서술할 것.
        4. 'affectedCountries'는 미국 포함 최대 5개까지. 근거 있는 실질적 영향을 반드시 400~450 byte로 작성. 정보가 부족할 경우 관련 정보를 국내외 기사에서 찾아보고 보충할 것.
        5. 'keywords'는 다음 중 복수 선택: 문화, 외교, 이민, 법·행정, 통상·경제
        6. 'execute'는 실제 실행 여부에 따라 '실행' 또는 '예고'로 구분.
        7. 'summary'는 반드시 기사에 나온 내용만 작성할 것.
        8. 한글의 문법과 맞춤법에 유의하여 작성할 것.
        형식: {{
                "news-title": "",
                "link": "",
                "date": "",
                "title": "",
                "korea": "",
                "keywords": [],
                "execute": "",
                "affectedCountries": [
                    {{
                    "name": "",
                    "effect": ""
                    }}
                ],
                "thumbnail_url": "",
                "summary": ""
            }}
    """

    role = "당신은 트럼프 대통령 및 미국 정책에 대한 뉴스를 분석하는 전문 분석가입니다. 기사 내용을 정확히 파악하고, 그 정책의 배경과 국제적 파급력, 한국에 미치는 영향 등을 객관적인 보고체로 정리할 수 있습니다. 기사에 따라 중요한 영향을 미칠 국가를 선정하고, 경제, 외교, 문화, 법·행정 등의 키워드를 분류하는 데에도 능숙합니다. 논리적, 체계적, 압축적으로 서술해 주세요."

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    content = response.choices[0].message.content.strip()

    if content == "무관":
        return None
    else:
        return json.loads(content)

def update_google_doc(date_display, json_results):
    """Google 문서 업데이트 - 문서 맨 아래에 추가"""
    service = get_google_docs_service()
    
    # 문서 내용 가져오기
    doc = service.documents().get(documentId=DOCUMENT_ID).execute()
    
    # 문서의 끝 인덱스 찾기
    content = doc.get('body').get('content')
    end_index = content[-1].get('endIndex') - 1  # 마지막 문자 바로 앞
    
    # 제목과 내용 준비
    title_text = f"\n{date_display}\n"  # 제목1로 설정될 텍스트
    content_text = ""
    
    # JSON 결과들을 문자열로 변환
    for result in json_results:
        content_text += json.dumps(result, ensure_ascii=False, indent=2) + ",\n\n"
    
    # 문서 맨 아래에 삽입할 요청 준비
    requests_body = [
        # 1. 먼저 제목 텍스트 삽입
        {
            'insertText': {
                'location': {'index': end_index},
                'text': title_text
            }
        },
        # 2. 제목을 제목1 스타일로 변경
        {
            'updateParagraphStyle': {
                'range': {
                    'startIndex': end_index + 1,  # \n 다음부터
                    'endIndex': end_index + len(title_text) - 1  # 마지막 \n 전까지
                },
                'paragraphStyle': {
                    'namedStyleType': 'HEADING_1'
                },
                'fields': 'namedStyleType'
            }
        },
        # 3. 그 다음에 내용 삽입
        {
            'insertText': {
                'location': {'index': end_index + len(title_text)},
                'text': content_text
            }
        }
    ]
    
    # 문서 업데이트 실행
    service.documents().batchUpdate(
        documentId=DOCUMENT_ID,
        body={'requests': requests_body}
    ).execute()
    
    print(f"Google 문서가 성공적으로 업데이트되었습니다.")
    print(f"제목: {date_display}")
    print(f"추가된 기사 수: {len(json_results)}개")

def job():
    """메인 실행 함수"""
    today = datetime.now()
    if today.weekday() == 6:
        print("일요일엔 실행하지 않습니다.")
        return
    
    full_date, display_date = get_target_date()
    
    print(f"처리 날짜: {full_date} (표시: {display_date})")
    
    links = fetch_links(full_date)
    seen_links = set()
    json_results = []
    
    for link in links:
        if link in seen_links:
            continue
        seen_links.add(link)

        article_info = filter_article(link)
        if article_info:
            try:
                json_data = process_article(article_info)
                if json_data:
                    json_results.append(json_data)
                    print(f"처리 완료: {link}")
            except Exception as e:
                print(f"처리 오류 {link}: {e}")
    
    if json_results:
        # Google 문서 업데이트
        update_google_doc(display_date, json_results)
        print(f"총 {len(json_results)}개 기사가 처리되었습니다.")
    else:
        print("처리할 기사가 없습니다.")

if __name__ == "__main__":
    job()