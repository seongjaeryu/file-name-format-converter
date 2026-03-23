# 📁 파일명 포맷 컨버터

### Mac 한글 파일명 깨짐 해결

&nbsp;

> Mac에서 받은 파일 이름이 `ㅎㅏㄴㄱㅡㄹ.txt`처럼 깨져 보이나요?
> Mac에서 Windows 사용자에게 파일을 보내야 하나요?

&nbsp;

파일 이름만 바꿔주는 간단한 도구입니다. **파일 내용은 전혀 건드리지 않습니다.**

설치가 필요 없습니다. 아래 링크를 Chrome 또는 Edge로 열면 바로 사용할 수 있습니다.

<a href="https://seongjaeryu.github.io/file-name-format-converter/" target="_blank"><strong>바로 사용하기 👉 seongjaeryu.github.io/file-name-format-converter</strong></a>

&nbsp;

---

&nbsp;

## 🎯 이럴 때 사용하세요

- **Windows에서** — Mac에서 받은 파일 이름이 깨져 보일 때, 정상으로 고쳐줍니다.

- **Mac에서** — Windows 사용자에게 보내기 전에, 미리 파일 이름을 변환해둡니다.

&nbsp;

## 📖 사용법

1. 위 링크를 **Chrome** 또는 **Edge**로 엽니다.

2. 파일이나 폴더를 화면에 **끌어다 놓습니다** (드래그앤드롭).

3. **"전체 변환"** 을 누르면 끝!

&nbsp;

> 💡 처음 사용 시 브라우저가 "이 사이트가 파일을 수정하려고 합니다" 같은 경고를 표시할 수 있습니다.
> **"허용"을 눌러주세요.** 파일 이름을 바꾸려면 이 권한이 필요합니다.

&nbsp;

### Mac과 Windows의 차이

| | Mac (macOS) | Windows |
| --- | --- | --- |
| 드롭 방식 | **폴더만** 드래그 & 드롭 | 파일 또는 폴더 모두 가능 |
| 이유 | Mac에서 개별 파일 드롭 시 브라우저가 파일명을 자동 변환하여 감지 불가 | 제한 없음 |

> 앱에서 자동으로 OS를 감지하여 안내합니다.

&nbsp;

---

&nbsp;

## 🔒 안전한가요?

- **파일 내용은 절대 바뀌지 않습니다.** 이름표만 바꾸는 것과 같습니다.

- **내 컴퓨터 안에서만 처리됩니다.** 파일이 인터넷으로 전송되지 않습니다.

- **변환 전에 미리보기**로 어떻게 바뀌는지 확인할 수 있습니다.

- 코드가 모두 공개된 오픈소스입니다.

&nbsp;

---

&nbsp;

## ⚠️ 혹시 오류가 나면?

변환 중 오류가 나면 화면에 원인이 표시됩니다. 흔한 원인:

| 오류 메시지 | 해결 방법 |
| --- | --- |
| 파일이 사용 중 | 해당 파일을 열고 있는 프로그램을 닫고 다시 시도 |
| 쓰기 권한 거부 | 브라우저가 묻는 권한 요청에서 "허용" 클릭 |
| 디스크 공간 부족 | 저장 공간 확보 후 다시 시도 |

&nbsp;

오류가 나면 파일 이름 끝에 `~nfc`가 붙은 상태로 남아 있을 수 있습니다.

### 복구하는 법

1. 파일 탐색기(Windows) 또는 Finder(Mac)에서 `~nfc`를 검색합니다.

2. 찾은 파일의 이름에서 끝부분 `~xx~nfc`를 지우면 원래 이름으로 돌아갑니다.
   - 예: `보고서.pdf~a7~nfc` → `보고서.pdf`

3. 이후 변환을 다시 시도하세요.

&nbsp;

---

&nbsp;

## 📚 더 알아보기

&nbsp;

<details>
<summary><strong>왜 파일명이 깨질까? (기술 배경)</strong></summary>

&nbsp;

> macOS는 유니코드 **NFD**(자모 분리형)를, Windows는 **NFC**(완성형)를 사용합니다.
>
> - macOS (NFD): `ㅎ + ㅏ + ㄴ + ㄱ + ㅡ + ㄹ.txt`
> - Windows (NFC): `한글.txt`
>
> 같은 글자를 저장하는 방식이 다르기 때문에, Mac에서 만든 파일을 Windows에서 열면 이름이 깨져 보입니다.
>
> 이 도구는 Mac 방식(NFD)을 Windows 방식(NFC)으로 변환합니다.

&nbsp;

</details>

&nbsp;

<details>
<summary><strong>변환 방식 상세 (개발자용)</strong></summary>

&nbsp;

> **APFS와 NTFS의 유니코드 처리 차이**
>
> |   | APFS (macOS) | NTFS (Windows) |
> | --- | --- | --- |
> | NFD/NFC 구분 | 같은 파일명으로 취급 | 다른 파일명으로 취급 |
> | 직접 rename 가능 여부 | 불가 (동일 이름으로 인식) | 가능 |
>
> APFS에서 `한글.txt`(NFD)를 `한글.txt`(NFC)로 직접 rename하면 "같은 이름"으로 인식되어 실패합니다.

&nbsp;

> **해결: 임시 이름 경유 move 2회**
>
> ```text
> 한글.txt(NFD) → 한글.txt~a7~nfc → 한글.txt(NFC)
> ```
>
> 완전히 다른 이름(임시)을 경유하면 APFS도 다른 파일로 인식합니다.
>
> File System Access API의 `FileSystemFileHandle.move()`를 사용하며 (Chrome 110+),
> 파일 내용 복사 없이 이름만 변경하므로 대용량 파일도 즉시 처리됩니다.
>
> 실패 시 `*~nfc`로 검색하면 중간 상태 파일을 찾을 수 있습니다.
>
> Windows(NTFS)에서도 동일한 로직으로 동작합니다.

&nbsp;

> **브라우저의 파일명 정규화 주의**
>
> 개별 파일을 드래그앤드롭하면 브라우저가 `FileSystemFileHandle.name`을 NFC로 정규화하여 전달합니다.
> 이 경우 원본(NFD)과 변환 결과(NFC)가 동일하게 보여 변환 필요 여부를 감지할 수 없습니다.
>
> **폴더째로 드롭하면** 디렉토리 핸들의 `values()`를 순회하면서
> 파일시스템의 실제 NFD 이름을 읽으므로 정상 감지됩니다.
>
> 이 제한은 macOS에만 해당하며, Windows(NTFS)에서는 개별 파일 드롭도 정상 동작합니다.

&nbsp;

> **변환 항목**
>
> - NFD → NFC 유니코드 정규화 (핵심)
> - Windows 금지 문자 대체 (`< > : " / \ | ? *` → `_`)
> - Windows 예약 파일명 처리 (CON, PRN, AUX 등)
> - 파일명 끝 마침표/공백 제거
> - 파일명 길이 제한 (255바이트)

&nbsp;

</details>

&nbsp;

---

&nbsp;

Made by [Doribear](https://doribear.com) · Knowledge management with [Bind.ly](https://bind.ly)
