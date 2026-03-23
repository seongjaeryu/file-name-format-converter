# 파일명 포맷 컨버터 - Mac 한글 파일명 깨짐 해결

> Mac에서 받은 파일의 한글 이름이 `ㅎㅏㄴㄱㅡㄹ.txt`처럼 자모가 분리되어 보이나요?

macOS와 Windows의 유니코드 처리 방식 차이(NFD vs NFC)로 인해 한글 파일명이 깨지는 문제를 해결하는 변환 도구입니다. 설치 없이 브라우저에서 바로 사용할 수 있습니다.

## 이런 상황에서 사용하세요

1. **Windows에서 파일 사용 전** — Mac에서 받은 파일의 한글 이름이 깨져 보일 때, 파일명을 정상으로 복원합니다.
2. **Mac에서 Windows 사용자에게 파일 보내기 전** — 파일명을 미리 Windows 호환 포맷으로 변환하여 상대방이 정상적으로 볼 수 있게 합니다.

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

### 방법 1: 온라인 웹 버전 (설치 불필요, 권장)

<https://seongjaeryu.github.io/file-name-format-converter/>

브라우저에서 바로 사용 가능합니다. 모든 처리는 브라우저에서 이루어지며, 파일이 서버로 전송되지 않습니다.

두 가지 모드를 지원합니다:

- **로컬 파일 직접 변환** (Chrome/Edge): 파일이나 폴더를 드래그앤드롭하면 로컬 파일명을 직접 변환합니다. File System Access API를 사용하며, 파일 복사 없이 이름만 변경합니다.
- **다운로드 방식** (모든 브라우저): 파일을 드래그앤드롭하면 변환된 파일명으로 다운로드됩니다.

### 방법 2: 데스크톱 앱 (tkinter GUI)

```bash
# 의존성 설치 (드래그앤드롭 지원)
pip install tkinterdnd2

# 앱 실행
python app.py
```

파일을 드래그앤드롭하거나 파일 선택 버튼으로 추가 → "변환 실행" 클릭

### 방법 3: 로컬 웹 버전 (브라우저)

```bash
# 추가 의존성 없이 실행 가능
python web.py
```

브라우저가 자동으로 열리며, 파일/폴더 경로를 입력하여 변환합니다.
로컬 서버로 동작하므로 파일이 직접 변환됩니다 (재다운로드 아님).

## 사용 흐름

1. 파일 추가 (드래그앤드롭 / 폴더 선택 / 경로 입력)
2. 변환 전/후 파일명 미리보기 확인
3. "변환 실행" 클릭 (개별 또는 전체)
4. 변환된 파일을 메일, 구글 드라이브, USB 등으로 전달

## 파일 구조

```text
├── docs/index.html  # 온라인 웹 버전 (GitHub Pages)
├── converter.py     # 파일명 변환 핵심 로직
├── app.py           # 데스크톱 GUI (tkinter)
├── web.py           # 로컬 웹 버전 (로컬 서버)
└── requirements.txt
```

## 기술 노트

### 파일명 변환 방식 (온라인 웹 버전 - 로컬 파일 직접 변환)

macOS(APFS)는 NFD/NFC를 같은 파일명으로 취급하여 직접 rename이 불가능합니다.
이를 해결하기 위해 임시 이름을 경유하는 move 2회 방식을 사용합니다:

```text
한글.txt(NFD) → 한글.txt~a7~nfc → 한글.txt(NFC)
```

- 파일 내용 복사 없이 이름만 변경하므로 대용량 파일도 즉시 처리됩니다.
- 변환 중 실패 시 파일이 `~nfc`로 끝나는 임시 이름으로 남을 수 있습니다. `*~nfc`로 검색하여 찾을 수 있습니다.
- Windows(NTFS)에서도 동일한 로직으로 동작합니다.

---

Made by [Doribear](https://doribear.com) | Knowledge management with [Bind.ly](https://bind.ly)
