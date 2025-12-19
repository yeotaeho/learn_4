# 🚀 FastAPI EC2 CI/CD 배포 단계별 가이드

이 문서는 GitHub Actions를 통해 FastAPI를 EC2에 자동 배포하는 단계별 가이드입니다.

## 📋 전체 배포 프로세스

```
GitHub Secrets 설정 → EC2 초기 설정 → 모델 업로드 → 환경 설정 → 서비스 설정 → 보안 그룹 → 첫 배포 → 테스트
```

---

## ✅ 사전 준비 완료 항목

다음 항목들은 이미 완료된 것으로 가정합니다:

- ✅ GitHub Secrets 설정 완료 (`EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`)
- ✅ EC2 인스턴스 접속 가능
- ✅ 로컬에 `api` 폴더 및 모델 파일 존재

---

## 1️⃣ EC2 초기 설정

### 1-1. EC2에 SSH 접속

**Windows PowerShell에서 실행:**

```powershell
ssh -i "Dovahkiin.pem" ubuntu@ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com
```

### 1-2. 초기 설정 스크립트 실행

**EC2 터미널에서 실행:**

```bash
# 초기 설정 스크립트 다운로드 및 실행
curl -o setup-ec2.sh https://raw.githubusercontent.com/yeotaeho/learn_4/master/scripts/setup-ec2.sh
chmod +x setup-ec2.sh
bash setup-ec2.sh
```

**이 스크립트가 수행하는 작업:**
- 시스템 패키지 업데이트
- Python3, pip, venv, git, rsync 설치
- `~/api/model_weights` 디렉토리 생성
- Python 가상환경 생성

**예상 소요 시간:** 2-3분

✅ **완료 조건**: 스크립트가 오류 없이 완료되고 "✅ 기본 설정 완료!" 메시지 표시

---

## 2️⃣ 모델 파일 업로드

### 2-1. 로컬에서 모델 파일 업로드

**Windows PowerShell에서 실행 (EC2 접속 종료 후):**

```powershell
# 모델 파일 업로드
scp -i "Dovahkiin.pem" -r api/model_weights/* `
  ubuntu@ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:~/api/model_weights/
```

**참고:** 파일 크기에 따라 업로드 시간이 다릅니다 (수백 MB ~ 수 GB).

### 2-2. 모델 파일 확인

**EC2 터미널에서 실행:**

```bash
# 모델 파일 목록 확인
ls -lh ~/api/model_weights/
```

✅ **완료 조건**: `config.json`, `model.safetensors` 등 모델 파일이 존재함

---

## 3️⃣ 환경 변수 설정

### 3-1. .env 파일 생성

**EC2 터미널에서 실행:**

```bash
cd ~/api
nano .env
```

### 3-2. .env 파일 내용 입력

다음 내용을 복사하여 붙여넣기:

```env
LLM_PROVIDER=local
LOCAL_MODEL_PATH=/home/ubuntu/api/model_weights
LOCAL_MODEL_DEVICE=cuda
DATABASE_URL=postgresql://neondb_owner:npg_pzP8wiQDH1sk@ep-autumn-boat-a1wcjk8g-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
DEBUG=false
```

**저장 방법:**
1. `Ctrl + X` 누르기
2. `Y` 입력
3. `Enter` 누르기

✅ **완료 조건**: `.env` 파일이 올바르게 생성되고 내용이 저장됨

---

## 4️⃣ systemd 서비스 설정

### 4-1. 서비스 설정 스크립트 다운로드

**EC2 터미널에서 실행:**

```bash
cd ~/api
curl -o setup-systemd.sh https://raw.githubusercontent.com/yeotaeho/learn_4/master/scripts/setup-systemd.sh
chmod +x setup-systemd.sh
```

### 4-2. 서비스 설치 및 시작

**EC2 터미널에서 실행:**

```bash
sudo bash setup-systemd.sh
```

이 스크립트는:
- systemd 서비스 파일 생성 (`/etc/systemd/system/fastapi.service`)
- 서비스 활성화 및 시작
- 로그 파일 생성

### 4-3. 서비스 상태 확인

**EC2 터미널에서 실행:**

```bash
sudo systemctl status fastapi.service
```

✅ **완료 조건**: 서비스가 `active (running)` 상태로 표시됨

**만약 서비스가 실패했다면:**

```bash
# 로그 확인
sudo journalctl -u fastapi.service -n 50

# 수동 실행 테스트
cd ~/api
source venv/bin/activate
python run.py
```

---

## 5️⃣ 보안 그룹 설정 (포트 8000 열기)

### 5-1. AWS Console 접속

1. AWS Console → EC2 대시보드 접속
2. **Instances** 메뉴 클릭
3. 해당 EC2 인스턴스 선택
4. **Security** 탭 클릭
5. **Security groups** 링크 클릭

### 5-2. Inbound rules 편집

1. **Edit inbound rules** 버튼 클릭
2. **Add rule** 버튼 클릭
3. 다음 값 입력:
   - **Type**: Custom TCP
   - **Port range**: 8000
   - **Source**: 0.0.0.0/0 (또는 특정 IP로 제한)
4. **Save rules** 버튼 클릭

✅ **완료 조건**: 포트 8000이 Inbound rules에 추가됨

---

## 6️⃣ 첫 배포 테스트 (GitHub Actions)

### 6-1. 로컬에서 코드 푸시

**Windows PowerShell에서 실행:**

```powershell
# 프로젝트 루트 디렉토리에서
git add .
git commit -m "Setup CI/CD pipeline"
git push origin master
```

### 6-2. GitHub Actions 확인

1. https://github.com/yeotaeho/learn_4 접속
2. **Actions** 탭 클릭
3. **Deploy FastAPI to EC2** 워크플로우 실행 확인
4. 워크플로우 클릭하여 로그 확인

**예상 소요 시간:** 2-3분

**성공 시 표시:**
- ✅ 녹색 체크 표시
- "✅ Deployment completed!" 메시지

**실패 시 확인 사항:**
- GitHub Actions 로그에서 오류 메시지 확인
- EC2 SSH 접속 가능 여부 확인
- Secrets 설정 확인

✅ **완료 조건**: Workflow가 성공적으로 완료되고 녹색 체크 표시

---

## 7️⃣ API 테스트

### 7-1. Health Check

**Windows PowerShell에서 실행:**

```powershell
# Health check
curl http://ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:8000/health
```

**예상 응답:**
```json
{"status":"healthy"}
```

### 7-2. API 문서 확인

**브라우저에서 접속:**

```
http://ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:8000/docs
```

또는 PowerShell에서:

```powershell
Start-Process "http://ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:8000/docs"
```

### 7-3. 채팅 API 테스트

**Windows PowerShell에서 실행:**

```powershell
curl -X POST http://ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:8000/api/chat `
  -H "Content-Type: application/json" `
  -d '{"message":"안녕하세요","history":[]}'
```

✅ **완료 조건**: API가 정상 응답을 반환함

---

## 🔄 이후 자동 배포 프로세스

코드 변경 후 자동 배포:

**Windows PowerShell에서 실행:**

```powershell
git add .
git commit -m "Update API code"
git push origin master
```

**자동 배포 흐름:**
1. GitHub에 코드 푸시
2. GitHub Actions 워크플로우 자동 실행
3. `api` 폴더를 EC2에 rsync로 전송
4. EC2에서 의존성 설치 및 서비스 재시작
5. 약 2-3분 후 변경사항 반영

**주의사항:**
- `model_weights` 폴더는 배포에서 제외됨 (이미 EC2에 있음)
- `__pycache__`, `venv` 등도 제외됨

---

## 🛠️ 유용한 명령어

### 서비스 관리 (EC2에서 실행)

```bash
# 서비스 상태 확인
sudo systemctl status fastapi.service

# 서비스 재시작
sudo systemctl restart fastapi.service

# 서비스 중지
sudo systemctl stop fastapi.service

# 서비스 시작
sudo systemctl start fastapi.service
```

### 로그 확인 (EC2에서 실행)

```bash
# 실시간 로그 확인
sudo journalctl -u fastapi.service -f

# 최근 50줄 로그
sudo journalctl -u fastapi.service -n 50

# 로그 파일 확인
tail -f /var/log/fastapi.log

# 에러 로그 확인
tail -f /var/log/fastapi-error.log
```

### 수동 실행 테스트 (EC2에서 실행)

```bash
cd ~/api
source venv/bin/activate
python run.py
```

---

## 🆘 문제 해결

### 배포가 실패하는 경우

1. **GitHub Actions 로그 확인**
   - GitHub Repository → Actions → 실패한 워크플로우 클릭
   - 각 단계의 로그 확인

2. **EC2 SSH 접속 확인**
   ```powershell
   ssh -i "Dovahkiin.pem" ubuntu@ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com
   ```

3. **서비스 로그 확인**
   ```bash
   sudo journalctl -u fastapi.service -n 100
   ```

4. **수동 실행 테스트**
   ```bash
   cd ~/api
   source venv/bin/activate
   python run.py
   ```

### 서비스가 시작되지 않는 경우

```bash
# 포트 확인
sudo lsof -i :8000

# 프로세스 종료 (PID 확인 후)
sudo kill -9 <PID>

# 서비스 재시작
sudo systemctl restart fastapi.service

# 서비스 상태 확인
sudo systemctl status fastapi.service
```

### 모델 로딩 오류

```bash
# 모델 파일 확인
ls -lh ~/api/model_weights/

# 권한 확인 및 수정
chmod -R 755 ~/api/model_weights/

# .env 파일 확인
cat ~/api/.env
```

### API가 응답하지 않는 경우

1. **보안 그룹 확인**
   - AWS Console → EC2 → Security groups
   - 포트 8000이 열려있는지 확인

2. **서비스 상태 확인**
   ```bash
   sudo systemctl status fastapi.service
   ```

3. **포트 리스닝 확인**
   ```bash
   sudo netstat -tlnp | grep 8000
   ```

---

## ✅ 배포 완료 체크리스트

배포가 완료되었는지 확인하세요:

- [x] GitHub Secrets 설정 완료 (이미 완료됨)
- [ ] EC2 초기 설정 완료
- [ ] 모델 파일 업로드 완료
- [ ] .env 파일 설정 완료
- [ ] systemd 서비스 실행 중
- [ ] 보안 그룹 포트 8000 열림
- [ ] GitHub Actions workflow 성공
- [ ] API 정상 작동 확인
- [ ] 로그에 오류 없음

---

## 📞 추가 지원

문제가 계속되면:

1. 전체 로그 내용 확인
2. `EC2_CICD_DEPLOYMENT_GUIDE.md` 참고
3. GitHub Issues에 문의

---

**작성일**: 2024-12-18
**버전**: 2.0.0
**업데이트**: CI/CD 배포 순서에 맞춰 재구성
