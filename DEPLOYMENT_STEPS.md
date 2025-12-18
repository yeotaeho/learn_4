# 🚀 FastAPI EC2 배포 단계별 가이드

이 문서는 실제 배포를 위한 단계별 체크리스트입니다.

## 📋 전체 배포 프로세스

```
로컬 설정 → GitHub 설정 → EC2 설정 → 첫 배포 → 테스트 → 완료
```

---

## 1️⃣ 로컬 설정 (Windows)

### 파일 확인

```powershell
# 필요한 파일들이 생성되었는지 확인
Get-ChildItem .github/workflows/deploy-api.yml
Get-ChildItem scripts/setup-ec2.sh
Get-ChildItem scripts/setup-systemd.sh
Get-ChildItem api/.env.example
```

✅ **완료 조건**: 위 4개 파일이 모두 존재

---

## 2️⃣ GitHub Secrets 설정

### 2-1. GitHub Repository 접속

1. https://github.com/yeotaeho/learn_4 접속
2. Settings → Secrets and variables → Actions 클릭

### 2-2. Secrets 추가

아래 3개의 Secret을 추가하세요:

#### Secret 1: `EC2_HOST`

```
ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com
```

#### Secret 2: `EC2_USER`

```
ubuntu
```

#### Secret 3: `EC2_SSH_KEY`

```powershell
# PowerShell에서 키 내용 복사
Get-Content Dovahkiin.pem | clip
```

복사한 내용을 Secret 값으로 붙여넣기 (전체 내용 포함)

✅ **완료 조건**: 3개의 Secret이 모두 추가됨

---

## 3️⃣ EC2 접속 및 초기 설정

### 3-1. SSH 접속

```powershell
ssh -i "Dovahkiin.pem" ubuntu@ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com
```

### 3-2. 초기 설정 스크립트 실행

```bash
# 스크립트 다운로드 및 실행
curl -o setup-ec2.sh https://raw.githubusercontent.com/yeotaeho/learn_4/master/scripts/setup-ec2.sh
chmod +x setup-ec2.sh
bash setup-ec2.sh
```

✅ **완료 조건**: 스크립트가 오류 없이 완료

---

## 4️⃣ 모델 파일 업로드

### 옵션 A: 로컬에서 직접 업로드 (권장)

```powershell
# PowerShell에서 실행
scp -i "Dovahkiin.pem" -r api/model_weights/* `
  ubuntu@ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:~/api/model_weights/
```

### 옵션 B: S3 사용

```bash
# EC2에서 실행
aws s3 sync s3://your-bucket/model_weights/ ~/api/model_weights/
```

### 모델 파일 확인

```bash
# EC2에서 실행
ls -lh ~/api/model_weights/
```

✅ **완료 조건**: config.json, model.safetensors 등 모델 파일 존재

---

## 5️⃣ 환경 변수 설정

### 5-1. .env 파일 생성

```bash
# EC2에서 실행
cd ~/api
cp .env.example .env
nano .env
```

### 5-2. .env 파일 내용 수정

```env
LLM_PROVIDER=local
LOCAL_MODEL_PATH=/home/ubuntu/api/model_weights
LOCAL_MODEL_DEVICE=cuda
DATABASE_URL=postgresql://neondb_owner:npg_pzP8wiQDH1sk@ep-autumn-boat-a1wcjk8g-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
DEBUG=false
```

저장: `Ctrl + X` → `Y` → `Enter`

✅ **완료 조건**: .env 파일이 올바르게 설정됨

---

## 6️⃣ systemd 서비스 설정

### 6-1. 서비스 설정 스크립트 다운로드

```bash
# EC2에서 실행
cd ~/api
curl -o setup-systemd.sh https://raw.githubusercontent.com/yeotaeho/learn_4/master/scripts/setup-systemd.sh
chmod +x setup-systemd.sh
```

### 6-2. 서비스 설치

```bash
sudo bash setup-systemd.sh
```

### 6-3. 서비스 상태 확인

```bash
sudo systemctl status fastapi.service
```

✅ **완료 조건**: 서비스가 `active (running)` 상태

---

## 7️⃣ 보안 그룹 설정

### 7-1. AWS Console 접속

1. EC2 대시보드 → Instances
2. 해당 인스턴스 선택 → Security 탭
3. Security groups 클릭

### 7-2. Inbound rules 편집

| Type       | Protocol | Port Range | Source    |
|------------|----------|------------|-----------|
| Custom TCP | TCP      | 8000       | 0.0.0.0/0 |

✅ **완료 조건**: 포트 8000이 열려있음

---

## 8️⃣ 첫 수동 배포 테스트

### 8-1. 로컬에서 코드 푸시

```powershell
git add .
git commit -m "Setup CI/CD pipeline"
git push origin master
```

### 8-2. GitHub Actions 확인

1. GitHub Repository → Actions 탭
2. "Deploy FastAPI to EC2" workflow 실행 확인
3. 로그 확인

✅ **완료 조건**: Workflow가 성공적으로 완료 (녹색 체크)

---

## 9️⃣ 서비스 테스트

### 9-1. 로컬에서 API 테스트

```powershell
# Health check
curl http://ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:8000/health

# API 문서
Start-Process "http://ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:8000/docs"
```

### 9-2. 채팅 테스트

```powershell
curl -X POST http://ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:8000/api/chat `
  -H "Content-Type: application/json" `
  -d '{"message":"안녕하세요","history":[]}'
```

✅ **완료 조건**: API가 정상 응답을 반환

---

## 🔟 모니터링 및 로그

### 로그 확인

```bash
# EC2에서 실행

# 실시간 로그
sudo journalctl -u fastapi.service -f

# 최근 50줄
sudo journalctl -u fastapi.service -n 50

# 로그 파일
tail -f /var/log/fastapi.log
```

### 서비스 관리

```bash
# 서비스 시작
sudo systemctl start fastapi.service

# 서비스 중지
sudo systemctl stop fastapi.service

# 서비스 재시작
sudo systemctl restart fastapi.service

# 서비스 상태
sudo systemctl status fastapi.service
```

✅ **완료 조건**: 로그에서 오류가 없음

---

## ✅ 배포 완료 체크리스트

- [ ] GitHub Secrets 설정 완료
- [ ] EC2 초기 설정 완료
- [ ] 모델 파일 업로드 완료
- [ ] .env 파일 설정 완료
- [ ] systemd 서비스 실행 중
- [ ] 보안 그룹 포트 8000 열림
- [ ] GitHub Actions workflow 성공
- [ ] API 정상 작동 확인
- [ ] 로그에 오류 없음

---

## 🔄 이후 배포 프로세스

코드 변경 후:

```powershell
git add .
git commit -m "Update API code"
git push origin master
```

→ GitHub Actions가 자동으로 배포 진행
→ 약 2-3분 후 변경사항 반영

---

## 🆘 문제 해결

### 배포 실패 시

1. GitHub Actions 로그 확인
2. EC2 SSH 접속 가능한지 확인
3. 서비스 로그 확인: `sudo journalctl -u fastapi.service -n 100`
4. 수동으로 테스트: `cd ~/api && source venv/bin/activate && python run.py`

### 서비스가 시작되지 않을 때

```bash
# 포트 확인
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 <PID>

# 서비스 재시작
sudo systemctl restart fastapi.service
```

### 모델 로딩 오류

```bash
# 모델 파일 확인
ls -lh ~/api/model_weights/

# 권한 확인
chmod -R 755 ~/api/model_weights/
```

---

## 📞 지원

문제가 계속되면:
1. 로그 전체 내용 확인
2. `EC2_CICD_DEPLOYMENT_GUIDE.md` 참고
3. GitHub Issues에 문의

---

**작성일**: 2024-12-18
**버전**: 1.0.0

