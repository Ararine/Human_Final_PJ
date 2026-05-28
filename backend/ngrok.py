"""
로컬 백엔드를 ngrok으로 공개하는 독립 실행 스크립트.

사용법:
    1. backend/.env 에 NGROK_AUTHTOKEN 설정
    2. python ngrok.py 실행 → 콘솔에 출력된 https://xxxx.ngrok-free.app 복사
    3. Colab garim_colab_worker.py 의 BACKEND_URL 에 붙여넣기
"""
import os

from dotenv import load_dotenv
from pyngrok import ngrok

load_dotenv()

authtoken = os.getenv("NGROK_AUTHTOKEN", "")
if not authtoken:
    raise RuntimeError(
        "NGROK_AUTHTOKEN 이 설정되지 않았습니다. backend/.env 를 확인하세요."
    )

ngrok.kill()
ngrok.set_auth_token(authtoken)
tunnel = ngrok.connect(int(os.getenv("PORT", 8000)))
print(f"ngrok 공개 URL: {tunnel.public_url}")
print("Colab garim_colab_worker.py 의 BACKEND_URL 에 위 URL 을 입력하세요.")
