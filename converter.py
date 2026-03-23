"""
파일명 포맷 컨버터 (Mac → Windows)
macOS NFD 유니코드를 Windows NFC 유니코드로 변환하여
파일명 깨짐 문제를 해결합니다.
"""

import unicodedata
import os
import re


# Windows에서 파일명에 사용할 수 없는 문자
WINDOWS_FORBIDDEN_CHARS = re.compile(r'[<>:"/\\|?*]')
# Windows 예약 파일명
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}
# Windows 최대 파일명 길이
WINDOWS_MAX_FILENAME_LENGTH = 255


def normalize_filename(filename: str) -> str:
    """NFD(macOS) → NFC(Windows) 유니코드 정규화"""
    return unicodedata.normalize("NFC", filename)


def replace_forbidden_chars(filename: str, replacement: str = "_") -> str:
    """Windows 금지 문자를 대체 문자로 변환"""
    return WINDOWS_FORBIDDEN_CHARS.sub(replacement, filename)


def fix_reserved_name(name: str) -> str:
    """Windows 예약 파일명 처리"""
    stem, ext = os.path.splitext(name)
    if stem.upper() in WINDOWS_RESERVED_NAMES:
        return f"_{stem}{ext}"
    return name


def strip_trailing_dots_spaces(name: str) -> str:
    """Windows에서 허용하지 않는 파일명 끝의 마침표/공백 제거"""
    # 확장자를 보존하면서 stem 부분의 끝 마침표/공백 제거
    # "test.." → splitext → ("test.", ".") 문제를 방지하기 위해
    # 마지막 유효 확장자만 분리
    stripped = name.rstrip(". ")
    if not stripped:
        return "_"
    # 원본에서 유효한 확장자 추출 (stripped 기준)
    stem, ext = os.path.splitext(stripped)
    if not stem:
        stem = "_"
    return f"{stem}{ext}"


def truncate_filename(name: str, max_length: int = WINDOWS_MAX_FILENAME_LENGTH) -> str:
    """파일명이 Windows 최대 길이를 초과하면 잘라냄"""
    if len(name.encode("utf-8")) <= max_length:
        return name
    stem, ext = os.path.splitext(name)
    ext_bytes = len(ext.encode("utf-8"))
    max_stem = max_length - ext_bytes
    while len(stem.encode("utf-8")) > max_stem:
        stem = stem[:-1]
    return f"{stem}{ext}"


def convert_filename(filename: str) -> str:
    """macOS 파일명을 Windows 호환 파일명으로 변환"""
    result = normalize_filename(filename)
    result = replace_forbidden_chars(result)
    result = fix_reserved_name(result)
    result = strip_trailing_dots_spaces(result)
    result = truncate_filename(result)
    return result


def convert_file(filepath: str) -> tuple[str, str, bool]:
    """
    파일명을 변환하고 실제로 이름을 변경합니다.

    Returns:
        (원래 파일명, 새 파일명, 변경 여부)
    """
    dirpath = os.path.dirname(filepath)
    old_name = os.path.basename(filepath)
    new_name = convert_filename(old_name)

    if old_name == new_name:
        return old_name, new_name, False

    new_path = os.path.join(dirpath, new_name)

    # 같은 이름의 파일이 이미 존재하면 숫자 붙이기
    if os.path.exists(new_path):
        stem, ext = os.path.splitext(new_name)
        counter = 1
        while os.path.exists(new_path):
            new_name = f"{stem} ({counter}){ext}"
            new_path = os.path.join(dirpath, new_name)
            counter += 1

    os.rename(filepath, new_path)
    return old_name, new_name, True
