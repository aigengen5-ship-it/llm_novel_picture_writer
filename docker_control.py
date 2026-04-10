import subprocess
import time
import requests

# 설정
CONTAINER_NAME = "mi50_docker"
PORT = 8081

def check_container_port_free():
    """도커 내부에서 8081 포트가 진짜로 비었는지 확인"""
    # netstat이 도커에 없을 수 있으므로, lsof나 /proc/net/tcp를 확인하는 게 정확하지만
    # 간단하게 'pkill -0'으로 프로세스 존재 여부를 확인하는 방식을 추천

    # "llama-server"라는 이름의 프로세스가 살아있는지 확인 (exit code 0이면 살아있음)
    result = subprocess.run(
        f"docker exec {CONTAINER_NAME} pkill -0 -f llama-server",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    # 프로세스가 없으면(1) 포트도 빈 것으로 간주
    return result.returncode != 0

def switch_model(run_model, gpu_layers=99, context_size=32768):
    print(f"🔄 Switching to model: {run_model}...")

    if run_model == "gemma-3-27b" or run_model.find("gemma") > -1:
        run_script = "./llama.cpp/build/bin/llama-server -m /models/mlabonne/gemma-3-27b-it/gemma-3-27b-it-abliterated.q8_0.gguf -c 65536 -ngl 999 -fa on --host 0.0.0.0 --port 8081 --temp 0.9 --top-p 0.9 --repeat-penalty 1.1 -ts 1,1 --no-mmap --swa-full"
    elif run_model == "glm-4.6v":
        run_script = "./llama.cpp/build/bin/llama-server -m /models/huihui-ai/Huihui-GLM-4.6V-abliterated-GGUF/Huihui-GLM-4.6V-abliterated-Q4_K_M-00001-of-00008.gguf -c 32768 -ngl 37 -fa on --host 0.0.0.0 --port 8081 --temp 0.8 --top-p 0.9 --repeat-penalty 1.1 -n -1 --no-mmap"
    elif run_model == "glm-4.5a":
        run_script = "./llama.cpp/build/bin/llama-server -m /models/bartowski/ArliAI_GLM-4.5-Air-Derestricted-GGUF/ArliAI_GLM-4.5-Air-Derestricted-Q5_K_M-00001-of-00003.gguf  -c 32768 -ngl 33 -fa on --host 0.0.0.0 --port 8081 --temp 0.8 --top-p 0.9 --repeat-penalty 1.1 -n -1 --no-mmap  -ctk f16 -ctv f16"
    elif run_model == "gpt-oss-120b":
        run_script = "./llama.cpp/build/bin/llama-server -m /models/bartowski/gpt-oss-120b/huizimao_gpt-oss-120b-uncensored-bf16-MXFP4_MOE-00001-of-00002.gguf -c 25565 -ngl 33 -fa on --host 0.0.0.0 --port 8081 -ts 1,1 --no-mmap  --temp 0.8 --top-p 0.9 --min-p 0.05 --repeat-penalty 1.05 --swa-full"        
    elif run_model == "hyperclovax":
        run_script = "./llama.cpp/build/bin/llama-server -m /models/naver/hyperclovax/HyperCLOVAX-SEED-Think-32B-heretic2.Q8_0.gguf -c 65536 -ngl 999 -fa on -ctk q8_0 -ctv q8_0 --host 0.0.0.0 --port 8081 --temp 1.0 --top-p 0.9 --repeat-penalty 1.1 -n -1 --no-mmap"
    elif run_model == "midnight-miqu":
        run_script = "./llama.cpp/build/bin/llama-server -m /models/Midnight-Miqu/MQ/temp.gguf -c 25565 -ngl 999 -fa on -ctk q8_0 -ctv q8_0 --host 0.0.0.0 --port 8081 --temp 1.0 --top-p 0.9 --repeat-penalty 1.1 -n -1"
    else:
        print("✅ No model is founded")
        exit()

    # 1. 기존 llama-server 프로세스 죽이기 (도커 내부)
    kill_cmd = f"docker exec {CONTAINER_NAME} pkill llama-server -9"
    subprocess.run(kill_cmd, shell=True)
    time.sleep(30) # 프로세스 정리 대기
    print("✅ Killing process is done and waiting port is ready.")

    for _ in range(10):
        if check_container_port_free():
            print("✅ Port 8081 is free.")
            break
        time.sleep(1)
        print(".", end="", flush=True)
    else:
        print("\n❌ Error: Old process is stuck. Cannot switch model.")
        return False    

    # 2. 새 모델로 서버 실행 (백그라운드 실행)
    # nohup을 써야 도커 exec가 안 멈추고 바로 돌아옴
    start_cmd = (
        f"docker exec {CONTAINER_NAME} /bin/bash -c 'export HSA_OVERRIDE_GFX_VERSION=9.0.6 && export HIP_VISIBLE_DEVICES=0,1 && nohup {run_script} > /llama_log.txt 2>&1 &'"
    )

    subprocess.run(start_cmd, shell=True)

    print("⏳ Waiting for server to start...")
    for i in range(600): # 최대 60초
        # (A) 서버 응답 확인
        try:
            res = requests.get(f"http://localhost:{PORT}/health", timeout=1)
            if res.status_code == 200:
                print("\n✅ New model loaded successfully!")
                return True
        except:
            pass
            
        # (B) ★핵심★ 서버 프로세스가 죽었는지 확인 (Early Exit)
        if check_container_port_free(): 
            # 포트가 비어있다는 건 = 방금 킨 서버가 죽었다는 뜻
            print(f"\n❌ Server crashed immediately! Check logs.")
            # 로그 출력해서 원인 보여주기
            subprocess.run(f"docker exec {CONTAINER_NAME} tail -n 5 /llama_log.txt", shell=True)
            return False
            
        time.sleep(1)
        print(".", end="", flush=True)

    print("\n❌ Timeout.")
    return False

#switch_model("gemma-3-27b")
