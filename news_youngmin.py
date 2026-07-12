
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 텔레그램 설정 (환경 변수 또는 직접 입력)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "여기에_토큰_입력")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "여기에_챗ID_입력")

def send_telegram(text: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("텔레그램 설정(토큰 또는 챗ID)이 없습니다.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    MAX = 4000  # 텔레그램 메시지 최대 길이 제한
    
    for i in range(0, len(text), MAX):
        chunk = text[i:i + MAX]
        try:
            post_res = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk})
            post_res.raise_for_status()
        except Exception as e:
            print(f"텔레그램 전송 실패: {e}")

def run():
    # 1. 사이트 형식에 맞게 날짜 구하기 (예: 2026.07.10)
    today_str = datetime.now().strftime("%Y.%m.%d") 
    print(f"오늘 날짜 기준: {today_str}")

    url = "https://heisenberg.kr/latest/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        # [수정 완료 1] 게시글 목록을 감싸는 클래스
        articles = soup.select(".loop-list") 
        
        if not articles:
            print("게시글 목록을 찾을 수 없습니다. CSS 선택자를 확인하세요.")
            return

        found_today_news = False

        for article in articles:
            # [수정 완료 2] 날짜 클래스
            date_element = article.select_one(".date")
            if not date_element:
                continue
            
            article_date = date_element.text.strip()
            
            # 3. 날짜가 오늘(년월일)과 일치하는지 확인
            if today_str in article_date:
                found_today_news = True
                
                # [수정 완료 3] 게시글 링크 (h3 태그 중 title 클래스 안에 있는 a 태그)
                link_element = article.select_one("h3.title a")
                if not link_element:
                    continue
                
                article_url = link_element.get("href")
                if article_url.startswith("/"):
                    article_url = "https://heisenberg.kr" + article_url
                
                title = link_element.text.strip()
                print(f"오늘자 뉴스 발견: {title} ({article_url})")
                
                # 4. 해당 뉴스 링크로 들어가서 본문 가져오기
                detail_res = requests.get(article_url, headers=headers)
                detail_res.raise_for_status()
                detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                
                # [수정 완료 4] HTML 구조에 맞춘 정확한 본문 추출 로직
                content_element = detail_soup.select_one(".single-content")
                
                if content_element:
                    # 텔레그램 메시지가 지저분해지지 않도록 불필요한 위젯(프로필, 좋아요, 댓글, 문의하기, 태그) 강제 삭제
                    unwanted_classes = [
                        ".content-profile",   # 연구자 정보
                        ".content-like",      # 좋아요 버튼
                        ".content-reference", # 댓글 및 출처
                        ".content-contact",   # 문의하기 / 커피챗
                        ".content-tag"        # 하단 태그
                    ]
                    for unwanted in content_element.select(", ".join(unwanted_classes)):
                        unwanted.decompose() # 해당 태그를 HTML 트리에서 완전히 제거

                    # 깔끔해진 텍스트만 추출
                    content_text = content_element.text.strip()
                    
                    # 빈 줄이 너무 많지 않도록 정리 (선택 사항)
                    cleaned_lines = [line.strip() for line in content_text.splitlines() if line.strip()]
                    content_text = "\n\n".join(cleaned_lines)
                    
                    # 5. 텔레그램으로 전송
                    message = f"📰 [오늘의 뉴스]\n{title}\n{article_url}\n\n{content_text}"
                    send_telegram(message)
                else:
                    print(f"본문을 찾을 수 없습니다: {article_url}")

        if not found_today_news:
            print("오늘 날짜로 등록된 뉴스가 없습니다.")

    except Exception as e:
        print(f"크롤링 중 에러 발생: {e}")

if __name__ == "__main__":
    run()