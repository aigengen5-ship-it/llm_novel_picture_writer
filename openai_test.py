from openai import OpenAI

# 1. 클라이언트 설정, 8081: MI50
client = OpenAI(
    base_url="http://localhost:8081/v1",
    api_key="llama"
)

# 2. 클라이언트 설정, 8082: Gemma
client2 = OpenAI(
    base_url="http://localhost:8082/v1",
    api_key="llama"
)

# 2. 대화 기록을 저장할 리스트 초기화 (System 프롬프트 포함)
messages_history = [
    {"role": "system", "content": "당신은 친절하고 똑똑한 AI 비서입니다."}
]

print("대화를 시작합니다. (종료하려면 'exit' 입력)")

while True:
    # 3. 사용자 입력 받기
    user_input = input("\nUser: ")
    
    if user_input.lower() in ["exit", "quit", "종료"]:
        break

    # 4. 사용자 입력을 대화 기록에 추가
    messages_history.append({"role": "user", "content": user_input})

    # 5. API 요청 (전체 기록 messages_history 전송)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # Llama server에서는 무시됨
        messages=messages_history, # ★ 핵심: 지금까지의 대화 기록을 통째로 보냄
        temperature=0.7,
        stream=True  # 타자 치듯 나오게 하기 위해 스트리밍 사용
    )

    # 6. 답변 출력 및 내용 수집
    print("AI: ", end="")
    full_response = ""
    
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)
            full_response += content # 답변을 조각조각 모음

    print() # 줄바꿈

    # 7. ★ 중요: AI의 답변도 대화 기록에 추가 (그래야 다음 턴에서 기억함)
    messages_history.append({"role": "assistant", "content": full_response})

    # 8. Gemma translate
    messages_history2 = [
        {"role": "system", "content": "당신은 친절하고 똑똑한 AI 번역가입니다. 아래 문장을 한글로 번역하세요. 츤데레 스타일로 말해서 독자들을 즐겁게 해 주세요\n"}
    ]
    messages_history2.append({"role": "user", "content": full_response})

    # 5. API 요청 (전체 기록 messages_history 전송)
    response2 = client2.chat.completions.create(
        model="gpt-3.5-turbo", # Llama server에서는 무시됨
        messages=messages_history2, # ★ 핵심: 지금까지의 대화 기록을 통째로 보냄
        temperature=0.7,
        stream=True  # 타자 치듯 나오게 하기 위해 스트리밍 사용
    )

    # 6. 답변 출력 및 내용 수집
    print("Gemma: ", end="")
    full_response2 = ""
    
    for chunk in response2:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)
            full_response2 += content # 답변을 조각조각 모음


