from pyngrok import ngrok

token = "3Dk5LL7nsb9bncuy3Ox2JLu8wY1_4VT3htFnncAkGrqhQ3KWq"
ngrok.kill()  # 기존 ngrok 프로세스 종료

ngrok.set_auth_token(token)

tunnel = ngrok.connect(8000)

print(tunnel.public_url)