#!/bin/bash
# EC2 초기 설정 스크립트
# 사용법: ssh로 EC2에 접속한 후 이 스크립트를 실행하세요
# bash <(curl -s https://raw.githubusercontent.com/yeotaeho/learn_4/master/scripts/setup-ec2.sh)

set -e

echo "🚀 EC2 초기 설정을 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 시스템 업데이트
echo -e "${GREEN}📦 시스템 패키지 업데이트 중...${NC}"
sudo apt update
sudo apt upgrade -y

# 필수 패키지 설치
echo -e "${GREEN}📦 필수 패키지 설치 중...${NC}"
sudo apt install -y python3 python3-pip python3-venv git rsync curl

# api 디렉토리 생성
echo -e "${GREEN}📁 디렉토리 생성 중...${NC}"
mkdir -p ~/api/model_weights

# Python 가상환경 생성
echo -e "${GREEN}🐍 Python 가상환경 생성 중...${NC}"
cd ~/api
python3 -m venv venv

echo -e "${GREEN}✅ 기본 설정 완료!${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "1. model_weights 폴더에 모델 파일 업로드"
echo "   scp -i \"Dovahkiin.pem\" -r api/model_weights/ ubuntu@ec2-15-164-48-193.ap-northeast-2.compute.amazonaws.com:~/api/"
echo ""
echo "2. .env 파일 생성"
echo "   nano ~/api/.env"
echo ""
echo "3. systemd 서비스 설정"
echo "   sudo bash ~/api/scripts/setup-systemd.sh"


