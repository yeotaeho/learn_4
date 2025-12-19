# FastAPI EC2 CI/CD 배포 가이드

GitHub Actions를 통해 FastAPI를 EC2에 자동 배포하는 전체 가이드입니다.

## 📋 목차

1. [GitHub Repository 설정](#1-github-repository-설정)
2. [모델 파일 처리 전략](#2-모델-파일-처리-전략)
3. [GitHub Actions Workflow 파일](#3-github-actions-workflow-파일)
4. [EC2 서버 초기 설정](#4-ec2-서버-초기-설정)
5. [보안 그룹 설정](#5-보안-그룹-설정)
6. [환경 변수 설정](#6-환경-변수-설정)
7. [배포 플로우](#7-배포-플로우)
8. [고급 전략](#8-고급-전략-선택사항)
9. [문제 해결](#9-문제-해결)
10. [비용 최적화](#10-비용-최적화)

---

## 1. GitHub Repository 설정

### Secrets 설정 (필수)

GitHub Repository → Settings → Secrets and variables → Actions에 다음을 추가:

```
EC2_HOST: ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com
EC2_USER: ubuntu
EC2_SSH_KEY: [Dovahkiin.pem 파일의 전체 내용]
```

#### EC2_SSH_KEY 추가 방법

```bash
# Windows PowerShell
Get-Content Dovahkiin.pem | clip

# Mac/Linux
cat Dovahkiin.pem | pbcopy
# 또는
cat Dovahkiin.pem
```

복사한 내용을 GitHub Secrets에 붙여넣기

---

## 2. 모델 파일 처리 전략

### 문제점

`model_weights/*.safetensors` 파일은 `.gitignore`에 있어 Git에 업로드되지 않음

### 해결 방법 (하나를 선택)

#### 옵션 A: S3 사용 (권장)

**장점**: 버전 관리, 빠른 다운로드, 여러 EC2 인스턴스 공유

```bash
# EC2에서 한 번만 실행
aws s3 cp model_weights/ s3://your-bucket/model_weights/ --recursive

# GitHub Actions workflow에서 다운로드
aws s3 sync s3://your-bucket/model_weights/ ~/api/model_weights/
```

**필요한 추가 설정**:
- AWS IAM 사용자 생성
- GitHub Secrets에 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` 추가

#### 옵션 B: EC2에 미리 업로드 (간단함)

**장점**: 설정 간단, 추가 비용 없음

```bash
# 로컬에서 한 번만 실행
scp -i "Dovahkiin.pem" -r api/model_weights/ \
  ubuntu@ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:~/api/
```

#### 옵션 C: Git LFS 사용

**장점**: Git으로 버전 관리

```bash
# .gitignore에서 model_weights 제외
# Git LFS 설치 및 추적
git lfs install
git lfs track "api/model_weights/*.safetensors"
git add .gitattributes
git commit -m "Add Git LFS for model files"
```

**단점**: GitHub LFS 용량 제한 및 비용

---

## 3. GitHub Actions Workflow 파일

### 파일 생성

**파일 위치**: `.github/workflows/deploy-api.yml`

```yaml
name: Deploy FastAPI to EC2

on:
  push:
    branches:
      - master  # 또는 main
    paths:
      - 'api/**'  # api 폴더 변경 시에만 배포
  workflow_dispatch:  # 수동 실행 가능

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Setup SSH
      uses: webfactory/ssh-agent@v0.8.0
      with:
        ssh-private-key: ${{ secrets.EC2_SSH_KEY }}

    - name: Add EC2 to known hosts
      run: |
        mkdir -p ~/.ssh
        ssh-keyscan -H ${{ secrets.EC2_HOST }} >> ~/.ssh/known_hosts

    - name: Deploy to EC2
      env:
        EC2_USER: ${{ secrets.EC2_USER }}
        EC2_HOST: ${{ secrets.EC2_HOST }}
      run: |
        # api 폴더를 EC2로 전송 (model_weights 제외)
        rsync -avz --exclude 'model_weights' --exclude '__pycache__' \
          --exclude '*.pyc' --exclude '.pytest_cache' \
          ./api/ $EC2_USER@$EC2_HOST:~/api/

    - name: Install dependencies and restart service
      env:
        EC2_USER: ${{ secrets.EC2_USER }}
        EC2_HOST: ${{ secrets.EC2_HOST }}
      run: |
        ssh $EC2_USER@$EC2_HOST << 'EOF'
          cd ~/api

          # 가상환경이 없으면 생성
          if [ ! -d "venv" ]; then
            python3 -m venv venv
          fi

          # 패키지 설치
          source venv/bin/activate
          pip install -r requirements.txt

          # systemd 서비스 재시작 (또는 pm2)
          sudo systemctl restart fastapi.service
          # 또는 pm2 사용 시: pm2 restart fastapi
        EOF
```

### S3 사용 시 추가 단계

```yaml
    - name: Download model from S3
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        AWS_REGION: ap-northeast-2
      run: |
        ssh ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} << 'EOF'
          cd ~/api
          aws s3 sync s3://your-bucket/model_weights/ model_weights/
        EOF
```

---

## 4. EC2 서버 초기 설정

### A. SSH 접속

```bash
ssh -i "Dovahkiin.pem" ubuntu@ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com
```

### B. 필수 패키지 설치

```bash
# 시스템 업데이트
sudo apt update
sudo apt upgrade -y

# Python 및 pip 설치
sudo apt install -y python3 python3-pip python3-venv

# Git 설치 (필요 시)
sudo apt install -y git

# rsync 설치 (보통 기본 설치됨)
sudo apt install -y rsync
```

### C. GPU 사용 시 CUDA 설치

```bash
# NVIDIA 드라이버 설치 (g4dn 인스턴스)
sudo apt install -y ubuntu-drivers-common
sudo ubuntu-drivers autoinstall

# CUDA 설치
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda-repo-ubuntu2004-11-8-local_11.8.0-520.61.05-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2004-11-8-local_11.8.0-520.61.05-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2004-11-8-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda

# 재부팅
sudo reboot
```

### D. systemd 서비스 생성 (자동 재시작용)

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/fastapi.service
```

**파일 내용**:

```ini
[Unit]
Description=FastAPI RAG Chatbot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/api
Environment="PATH=/home/ubuntu/api/venv/bin"
ExecStart=/home/ubuntu/api/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**서비스 활성화**:

```bash
# 서비스 리로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable fastapi.service

# 서비스 시작
sudo systemctl start fastapi.service

# 상태 확인
sudo systemctl status fastapi.service

# 로그 확인
sudo journalctl -u fastapi.service -f
```

### E. 대안: PM2 사용 (Node.js 기반)

```bash
# Node.js 및 npm 설치
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# PM2 설치
sudo npm install -g pm2

# FastAPI 시작
cd ~/api
source venv/bin/activate
pm2 start run.py --name fastapi --interpreter venv/bin/python

# 자동 시작 설정
pm2 startup
pm2 save

# 상태 확인
pm2 status
pm2 logs fastapi
```

---

## 5. 보안 그룹 설정

### EC2 보안 그룹에서 포트 열기

AWS Console → EC2 → Security Groups → 해당 보안 그룹 선택 → Inbound rules 편집

| Type       | Protocol | Port Range | Source    | Description      |
|------------|----------|------------|-----------|------------------|
| Custom TCP | TCP      | 8000       | 0.0.0.0/0 | FastAPI Server   |
| SSH        | TCP      | 22         | My IP     | SSH Access       |

**보안 강화**:
- FastAPI는 0.0.0.0/0 대신 특정 IP만 허용 권장
- SSH는 반드시 My IP 또는 특정 IP만 허용
- HTTPS (443) 사용 시 Nginx 역방향 프록시 설정

---

## 6. 환경 변수 설정

### EC2에서 .env 파일 생성

```bash
cd ~/api
nano .env
```

**파일 내용**:

```env
# LLM 설정
LLM_PROVIDER=local
LOCAL_MODEL_PATH=/home/ubuntu/api/model_weights
LOCAL_MODEL_DEVICE=cuda

# 데이터베이스
DATABASE_URL=postgresql://neondb_owner:npg_pzP8wiQDH1sk@ep-autumn-boat-a1wcjk8g-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

# 디버그 모드
DEBUG=false
```

### 환경 변수 보안 강화

민감한 정보는 AWS Systems Manager Parameter Store 사용 권장:

```bash
# Parameter Store에 저장
aws ssm put-parameter --name "/fastapi/database-url" \
  --value "postgresql://..." --type "SecureString"

# Python에서 읽기
import boto3
ssm = boto3.client('ssm')
db_url = ssm.get_parameter(Name='/fastapi/database-url', WithDecryption=True)['Parameter']['Value']
```

---

## 7. 배포 플로우

### 전체 흐름

```
코드 수정 → Git Commit → Git Push → GitHub Actions 실행 → EC2 배포 → 서비스 재시작 → 완료
```

### 트리거 조건

1. **자동 트리거**: `master` 브랜치에 푸시 + `api/**` 폴더 변경 시
2. **수동 트리거**: GitHub Actions 페이지에서 "Run workflow" 클릭

### 배포 확인

```bash
# 배포 후 서버 상태 확인
ssh -i "Dovahkiin.pem" ubuntu@ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com

# 서비스 상태
sudo systemctl status fastapi.service

# 로그 확인
sudo journalctl -u fastapi.service -n 50

# API 테스트
curl http://localhost:8000/health
```

---

## 8. 고급 전략 (선택사항)

### A. 블루-그린 배포

**개념**: 두 개의 환경을 유지하며 무중단 배포

```bash
# 디렉토리 구조
~/api-blue/
~/api-green/

# Nginx 설정으로 트래픽 전환
upstream backend {
    server 127.0.0.1:8000;  # blue
    # server 127.0.0.1:8001;  # green
}
```

**GitHub Actions 수정**:

```yaml
- name: Deploy to alternate environment
  run: |
    ssh $EC2_USER@$EC2_HOST << 'EOF'
      if [ -f ~/current_env ]; then
        CURRENT=$(cat ~/current_env)
        if [ "$CURRENT" = "blue" ]; then
          DEPLOY_TO="green"
        else
          DEPLOY_TO="blue"
        fi
      else
        DEPLOY_TO="blue"
      fi

      echo "Deploying to $DEPLOY_TO"
      rsync -avz ./api/ ~/api-$DEPLOY_TO/

      # 서비스 재시작 및 전환
      sudo systemctl restart fastapi-$DEPLOY_TO.service
      echo $DEPLOY_TO > ~/current_env
    EOF
```

### B. 헬스 체크

```yaml
- name: Health Check
  run: |
    sleep 10
    response=$(curl -s -o /dev/null -w "%{http_code}" http://${{ secrets.EC2_HOST }}:8000/health)
    if [ $response != "200" ]; then
      echo "Health check failed"
      exit 1
    fi
    echo "Health check passed"
```

### C. 롤백 전략

```bash
# 이전 버전 백업
~/api-backup-$(date +%Y%m%d-%H%M%S)/

# 롤백 스크립트
ssh $EC2_USER@$EC2_HOST << 'EOF'
  LATEST_BACKUP=$(ls -t ~/api-backup-* | head -1)
  cp -r $LATEST_BACKUP ~/api/
  sudo systemctl restart fastapi.service
EOF
```

### D. 로그 모니터링

**CloudWatch Logs 연동**:

```bash
# CloudWatch Logs Agent 설치
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# 설정 파일 생성
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/config.json
```

**로그 파일 설정**:

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/fastapi.log",
            "log_group_name": "/fastapi/application",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

---

## 9. 문제 해결

### 배포 실패 시 체크리스트

#### 1. SSH 연결 문제

```bash
# 테스트
ssh -i "Dovahkiin.pem" ubuntu@ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com

# 권한 문제
chmod 600 Dovahkiin.pem

# Known hosts 문제
ssh-keygen -R ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com
```

#### 2. 보안 그룹 확인

- 포트 8000이 열려있는가?
- SSH 포트 22가 열려있는가?

#### 3. 모델 파일 누락

```bash
# EC2에서 확인
ls -lh ~/api/model_weights/
```

#### 4. Python 가상환경 문제

```bash
# 가상환경 재생성
cd ~/api
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 5. 포트 충돌

```bash
# 포트 사용 확인
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 <PID>
```

### 로그 확인 방법

```bash
# systemd 로그
sudo journalctl -u fastapi.service -f

# pm2 로그
pm2 logs fastapi

# 직접 실행하여 오류 확인
cd ~/api
source venv/bin/activate
python run.py
```

### 일반적인 오류 및 해결

| 오류 | 원인 | 해결 방법 |
|------|------|-----------|
| ModuleNotFoundError | 패키지 미설치 | `pip install -r requirements.txt` |
| CUDA out of memory | GPU 메모리 부족 | 인스턴스 타입 변경 또는 CPU 모드 사용 |
| Connection refused | 서비스 미실행 | `sudo systemctl start fastapi.service` |
| Permission denied | 권한 문제 | `chmod +x run.py` |

---

## 10. 비용 최적화

### EC2 인스턴스 타입 선택

| 용도 | 권장 인스턴스 | vCPU | 메모리 | GPU | 월 예상 비용 |
|------|---------------|------|--------|-----|--------------|
| 테스트 | t3.medium | 2 | 4GB | - | ~$30 |
| 프로덕션 (CPU) | t3.xlarge | 4 | 16GB | - | ~$120 |
| 프로덕션 (GPU) | g4dn.xlarge | 4 | 16GB | T4 | ~$400 |

### 비용 절감 팁

1. **예약 인스턴스**: 1년/3년 약정 시 최대 72% 할인
2. **스팟 인스턴스**: 최대 90% 할인 (중단 가능)
3. **오토 스케일링**: 사용량에 따라 자동 조정
4. **S3 스토리지 클래스**: 모델 파일을 Glacier로 저장

### 모니터링

```bash
# AWS CloudWatch로 비용 모니터링
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-xxxxx \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

---

## 📌 빠른 시작 체크리스트

- [ ] GitHub Secrets 설정 (EC2_HOST, EC2_USER, EC2_SSH_KEY)
- [ ] `.github/workflows/deploy-api.yml` 파일 생성
- [ ] EC2에 모델 파일 업로드
- [ ] EC2에 Python 및 필수 패키지 설치
- [ ] systemd 서비스 또는 PM2 설정
- [ ] 보안 그룹에서 포트 8000 열기
- [ ] `.env` 파일 생성
- [ ] 코드 푸시하여 배포 테스트

---

## 📚 추가 참고 자료

- [GitHub Actions 공식 문서](https://docs.github.com/en/actions)
- [AWS EC2 사용자 가이드](https://docs.aws.amazon.com/ec2/)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [systemd 서비스 관리](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

## 🆘 지원

문제가 발생하면:
1. 로그 확인 (`sudo journalctl -u fastapi.service -f`)
2. GitHub Actions 로그 확인
3. EC2에 SSH 접속하여 수동 실행 테스트
4. 보안 그룹 및 네트워크 설정 확인

---

**마지막 업데이트**: 2024-12-18
**작성자**: AI Assistant
**버전**: 1.0.0


