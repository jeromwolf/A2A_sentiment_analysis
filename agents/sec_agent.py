import uvicorn
import httpx
from fastapi import FastAPI
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
app = FastAPI()

SEC_API_USER_AGENT = os.getenv("SEC_API_USER_AGENT")
SUBMISSIONS_API_URL = "https://data.sec.gov/submissions/CIK{cik_number}.json"
FILING_URL_TEMPLATE = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number_no_dashes}/{primary_document}"

TICKER_TO_CIK = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "AMZN": "0001018724",
    "NVDA": "0001045810",
    "TSLA": "0001318605",
    "META": "0001326801",
}


async def analyze_form4(url: str, client: httpx.AsyncClient) -> str:
    """Form 4 공시의 XML을 분석하여 매수/매도 여부를 판단합니다."""
    try:
        print(f"   [SEC 에이전트 로그] Form 4 XML 분석 시작: {url}")
        response = await client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "xml")

        is_acquisition = soup.find("transactionCode", string="A") or soup.find(
            "transactionCode", string="P"
        )
        is_disposition = soup.find("transactionCode", string="D") or soup.find(
            "transactionCode", string="S"
        )

        if is_acquisition:
            return "내부자가 주식을 '매수'했다는 내용의 Form 4 공시가 확인되었습니다. 이는 경영진이 회사의 미래를 긍정적으로 보고 있다는 신호일 수 있습니다."
        elif is_disposition:
            return "내부자가 주식을 '매도'했다는 내용의 Form 4 공시가 확인되었습니다. 이는 단기적인 주가 변동성이나 경영진의 개인적인 자금 계획을 반영할 수 있습니다."
        else:
            return "최신 내부자 거래(Form 4) 공시가 확인되었으나, 거래 유형(매수/매도)을 특정할 수 없습니다."

    except Exception as e:
        print(f"❌ [SEC 에이전트] Form 4 XML 분석 오류: {e}")
        return "최신 내부자 거래(Form 4) 공시 내용을 분석하는 데 실패했습니다."


@app.post("/get_filings/{ticker}")
async def get_sec_filings(ticker: str):
    """SEC EDGAR API를 호출하여 최신 공시 정보를 심층 분석합니다."""
    if not SEC_API_USER_AGENT:
        return [
            {"source": "기업 공시", "text": "SEC_API_USER_AGENT가 설정되지 않았습니다."}
        ]

    cik_number = TICKER_TO_CIK.get(ticker.upper())
    if not cik_number:
        return [
            {
                "source": "기업 공시",
                "text": f"{ticker}에 대한 CIK 번호를 찾을 수 없습니다.",
            }
        ]

    headers = {"User-Agent": SEC_API_USER_AGENT}

    # [FIXED] httpx 클라이언트를 생성할 때 헤더를 기본값으로 설정합니다.
    async with httpx.AsyncClient(headers=headers) as client:
        try:
            request_url = SUBMISSIONS_API_URL.format(cik_number=cik_number)
            print(f"   [SEC 에이전트 로그] SEC EDGAR API 호출 시작 (CIK: {cik_number})")
            response = await client.get(
                request_url
            )  # 이제 모든 요청에 헤더가 자동으로 포함됩니다.
            response.raise_for_status()
            filings = response.json().get("filings", {}).get("recent", {})

            recent_forms = filings.get("form", [])
            accession_numbers = filings.get("accessionNumber", [])
            primary_documents = filings.get("primaryDocument", [])
            filing_dates = filings.get("filingDate", [])

            report_text = f"최신 공시: {filing_dates[0]}에 '{recent_forms[0]}' 제출됨."

            for i, form in enumerate(recent_forms[:5]):
                if form == "4":
                    print(
                        f"   [SEC 에이전트 로그] Form 4 발견! 심층 분석을 시작합니다."
                    )
                    accession_no_dashes = accession_numbers[i].replace("-", "")
                    cik_no_zeros = str(int(cik_number))
                    form4_xml_url = FILING_URL_TEMPLATE.format(
                        cik=cik_no_zeros,
                        accession_number_no_dashes=accession_no_dashes,
                        primary_document=primary_documents[i],
                    )
                    report_text = await analyze_form4(form4_xml_url, client)
                    break

            print(f"   [SEC 에이전트 로그] 최종 공시 분석 결과: {report_text}")
            return [
                {
                    "source": "기업 공시",
                    "text": report_text,
                    "log_message": f"➡️ [기업 공시] {report_text}",
                }
            ]

        except Exception as e:
            print(f"❌ [SEC 에이전트] API 호출 중 오류 발생: {e}")
            return [
                {
                    "source": "기업 공시",
                    "text": "최신 공시 정보를 가져오는 데 실패했습니다.",
                }
            ]
