# GX 예약 시스템 HANDOVER

## 새 채팅 시작 문구
GX 예약 시스템 작업을 이어서 진행합니다.
docs/HANDOVER.md 참고해주세요.

## 작업 규칙
- 클선임(Claude)이 모든 코드 작성
- 명령어 실행 전 VS / PA 항상 명시
- push 전 python manage.py check 필수
- VS → git push → PA git reset --hard → Reload 순서

## 인프라
- VS: GitHub Codespaces (parkran-gx/gx-booking)
- PA: parkrangx.pythonanywhere.com
- PA 배포: cd ~/gx-booking && git fetch origin && git reset --hard origin/main && touch /var/www/parkrangx_pythonanywhere_com_wsgi.py

## 계정 정보
- GitHub: parkran-gx
- PythonAnywhere: parkrangx
- 강사 관리자 ID: parkran
- 강사 관리자 PW: parkran2025!
- 단지코드: LIVE2025

## 기술 스택
- Django 4.2 / Python 3.12
- Bootstrap 5.3 + Font Awesome 6.4
- DB: SQLite
- 개발: GitHub Codespaces
- 운영: PythonAnywhere

## 앱 구조
- classes: 수업 정의/일정/캘린더/출석
- bookings: 예약/출석/개인레슨
- accounts: 회원가입/로그인/프로필
- complexes: 단지관리/QR코드
- enrollments: 월별수강등록/우선접수/대기
- notices: 공지게시판
- messages_app: 쪽지

## 수업 구성
- 요가(임산부가능): 목 10:30~11:20 / 10명 / 30,000원
- 필라테스A: 월/목 17:00~17:50 / 10명 / 52,000원
- 필라테스B: 월/목 18:00~18:50 / 10명 / 52,000원

## 사용자 등급
- super_admin: 모든 관리 (parkran)
- complex_admin: 단지 관리자
- registered: 수강 등록 회원
- unregistered: 가입만 한 회원

## 완성된 기능
- 랜딩페이지 QR 단지인식
- 회원가입/로그인/비밀번호찾기
- 단지별 수업분리
- 수업예약 (내정보 자동입력)
- 마이페이지
- 월별 수강등록
- 우선접수/일반접수 기간설정
- 수동등록/취소/대기자 자동승격
- 우선접수 대상자 지정
- Excel/PDF/CSV 내보내기
- 관리사무소 명단 복사/출력/전송
- 상태 수동변경
- 공지게시판
- 쪽지 3단계 (비회원/회원/등록회원)
- QR코드 생성
- 관리자 대시보드
- 수업일정 자동생성 (주1/2/3회/직접입력)
- 서식 불러오기/수업명 직접입력
- 개별세션 수정/휴강/대강
- 출석체크/내 출석현황
- 역할별 드롭다운 네비게이션
- 수업관리 (추가/수정/정원변경)
- PA 보안설정 완료

## 다음 작업 후보
- ~~카카오 알림 연동~~ (제거)
- PWA → Play Store 등록
- 출석부 PDF 출력
- 회원 승인 관리 페이지
- 다중 단지 확장 테스트

## PA 주요 명령어
- 배포: cd ~/gx-booking && git fetch origin && git reset --hard origin/main && touch /var/www/parkrangx_pythonanywhere_com_wsgi.py
- migration: python manage.py migrate
- 정적파일: python manage.py collectstatic --noinput
- 패키지: pip3.12 install --user -r requirements.txt
