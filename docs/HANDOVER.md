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
- PA: jihyepark.pythonanywhere.com
- PA 배포: cd ~/gx-booking && git fetch origin && git reset --hard origin/main && touch /var/www/jihyepark_pythonanywhere_com_wsgi.py

## 계정 정보
- GitHub: parkran-gx
- PythonAnywhere: jihyepark
- 강사 관리자 ID: parkran
- 강사 관리자 PW: parkran2025!
- 단지코드: LIVE2025

## 기술 스택
- Django 4.2 / Python 3.12
- Bootstrap 5.3 + Font Awesome 6.4
- Pretendard 폰트
- DB: SQLite / 개발: GitHub Codespaces / 운영: PythonAnywhere

## 앱 구조
- classes: 수업/일정/캘린더/출석/QR/매뉴얼
- bookings: 예약/출석/개인레슨
- accounts: 회원가입/로그인/프로필/회원관리
- complexes: 단지관리/QR코드
- enrollments: 월별수강등록/우선접수/대기
- notices: 공지게시판 (클래스별)
- messages_app: 쪽지 (수신/발신/답장)

## 완성된 기능 (전체)
### 회원 기능
- 랜딩페이지 QR 단지인식
- 회원가입/로그인/비밀번호찾기/변경
- 마이페이지 4탭 (수강관리·캘린더·공지·쪽지)
- 수업 예약·대기신청·변경요청
- 수강 등록 신청·현황 확인
- 회원용 캘린더 (목록/달력·스와이프·출석이모티콘)
- 출석 사전 등록·결석 사유 입력
- 공지 클래스별 게시판·수강생 글쓰기
- 쪽지 수신·발신·보낸쪽지함
- 강사님께 쪽지 보내기
- 모바일 하단 탭 (수업·공지·캘린더·쪽지·내정보)

### 관리자 기능
- 관리자 대시보드 (알림배너·오늘수업·통계·이번주일정·빠른메뉴)
- 월별 수강등록 (우선/일반접수·대기자 자동승격)
- 우선접수 대상자 지정
- Excel/PDF/CSV 명단 내보내기
- 관리사무소 명단 복사/출력/전송
- 수업 일정 자동생성 (주1/2회·직접입력)
- 개별세션 수정·휴강·대강
- 강사용 원터치 출석체크·전체출석·출석부PDF
- 회원 승인·등급 변경·삭제
- 수업 추가·수정·정원 변경
- 관리자 쪽지 발송·수신함·답장
- 공지 작성·전체공지·수업별공지·상단고정
- QR코드 생성·다운로드 (검정색)
- 운영 매뉴얼 (컬러 섹션별 정리)
- PA 보안설정 완료

## 디자인 시스템
- 컬러: 크림·모브로즈 (C팔레트)
  --rose: #7A5A54 / --rose-lt: #C4968A / --rose-bg: #FDF9F7
- 폰트: Pretendard
- 회원용: 우아·여성스러운 크림·모브로즈
- 관리자용: 실용·가시성 중심 (밝은 배경·굵은 텍스트·컬러 섹션)

## 주요 URL
- / : 랜딩
- /classes/ : 수업예약
- /accounts/dashboard/ : 마이페이지 (4탭)
- /my-calendar/ : 회원용 캘린더
- /my-attendance-check/<id>/ : 출석 사전 등록
- /enrollments/ : 수강등록
- /notices/ : 공지사항
- /messages/inbox/ : 쪽지함
- /messages/send/ : 쪽지 보내기
- /admin-dashboard/ : 관리자 대시보드
- /enrollments/admin/ : 수강등록 관리
- /calendar/ : 관리자 캘린더
- /calendar/schedule/create/ : 일정 등록
- /calendar/session/<id>/attendance/ : 출석체크
- /accounts/members/ : 회원관리
- /messages/admin/send/ : 관리자 쪽지발송
- /notices/create/ : 공지작성
- /qr/ : QR코드
- /manual/ : 운영매뉴얼

## 다음 작업 후보
1. 7월 수업 일정 등록 (즉시 필요)
2. 출석체크 페이지 모바일 최적화
3. 월별 수강 통계 리포트
4. PWA 홈화면 추가
5. 비밀번호 찾기 이메일 실제 발송 설정

## PA 주요 명령어
- 배포: cd ~/gx-booking && git fetch origin && git reset --hard origin/main && touch /var/www/parkrangx_pythonanywhere_com_wsgi.py
- migration: python manage.py migrate
- 정적파일: python manage.py collectstatic --noinput
- 패키지: pip3.12 install --user -r requirements.txt
