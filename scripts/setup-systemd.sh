#!/bin/bash
# systemd 서비스 설정 스크립트
# 사용법: sudo bash scripts/setup-systemd.sh

set -e

SERVICE_FILE="/etc/systemd/system/fastapi.service"
USER="ubuntu"
WORK_DIR="/home/ubuntu/api"

echo "🔧 systemd 서비스 파일 생성 중..."

# 서비스 파일 생성
cat > $SERVICE_FILE << 'EOF'
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
StandardOutput=append:/var/log/fastapi.log
StandardError=append:/var/log/fastapi-error.log

[Install]
WantedBy=multi-user.target
EOF

# 로그 파일 생성
echo "📝 로그 파일 생성 중..."
touch /var/log/fastapi.log
touch /var/log/fastapi-error.log
chown $USER:$USER /var/log/fastapi.log
chown $USER:$USER /var/log/fastapi-error.log

# 서비스 활성화
echo "✅ 서비스 활성화 중..."
systemctl daemon-reload
systemctl enable fastapi.service
systemctl start fastapi.service

# 상태 확인
echo ""
echo "✅ systemd 서비스 설정 완료!"
echo ""
systemctl status fastapi.service

echo ""
echo "유용한 명령어:"
echo "  서비스 시작:    sudo systemctl start fastapi.service"
echo "  서비스 중지:    sudo systemctl stop fastapi.service"
echo "  서비스 재시작:  sudo systemctl restart fastapi.service"
echo "  서비스 상태:    sudo systemctl status fastapi.service"
echo "  로그 확인:      sudo journalctl -u fastapi.service -f"
echo "  로그 파일:      tail -f /var/log/fastapi.log"

