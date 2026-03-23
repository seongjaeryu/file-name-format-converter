# 파일명 포맷 컨버터 (Mac → Windows)

macOS에서 생성한 파일을 Windows 사용자에게 전달할 때 파일명이 깨지는 문제를 해결하는 변환 도구입니다.

## 왜 파일명이 깨질까?

macOS는 유니코드 **NFD**(Normalization Form Decomposition)를 사용하고, Windows는 **NFC**(Normalization Form Composition)를 사용합니다.

예를 들어 "한글.txt"를 macOS에서 저장하면:
- macOS (NFD): `ㅎ + ㅏ + ㄴ + ㄱ + ㅡ + ㄹ.txt` (자모를 분리하여 저장)
- Windows (NFC): `한글.txt` (완성형으로 저장)

이 차이로 인해 macOS에서 만든 파일을 Windows로 보내면 파일명이 깨져 보입니다.

## 기능

- **NFD → NFC 유니코드 정규화** (핵심 변환)
- Windows 금지 문자 자동 대체 (`< > : " / \ | ? *`)
- Windows 예약 파일명 처리 (CON, PRN, AUX 등)
- 파일명 끝 마침표/공백 제거
- 파일명 길이 제한 처리 (255바이트)

## 사용 방법

### 방법 1: 데스크톱 앱 (tkinter GUI)

```bash
# 의존성 설치 (드래그앤드롭 지원)
pip install tkinterdnd2

# 앱 실행
python app.py
```

파일을 드래그앤드롭하거나 파일 선택 버튼으로 추가 → "변환 실행" 클릭

### 방법 2: 웹 버전 (브라우저)

```bash
# 추가 의존성 없이 실행 가능
python web.py
```

브라우저가 자동으로 열리며, 파일/폴더 경로를 입력하여 변환합니다.
로컬 서버로 동작하므로 파일이 직접 변환됩니다 (재다운로드 아님).

## 파일 구조

```
├── converter.py   # 파일명 변환 핵심 로직
├── app.py         # 데스크톱 GUI (tkinter)
├── web.py         # 웹 버전 (로컬 서버)
└── requirements.txt
```

## 사용 흐름

1. 파일 추가 (드래그앤드롭 / 경로 입력)
2. 변환 전/후 파일명 미리보기 확인
3. "변환 실행" 클릭
4. 변환된 파일을 메일, 구글 드라이브, USB 등으로 전달
