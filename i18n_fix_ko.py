#!/usr/bin/env python3
"""Fix Korean (ko) translation terminology to align with MDN Korean and Python glossary Korean.

Categories of fixes:
1. Critical: garbled/corrupted text (Thai chars, Chinese chars, mixed scripts)
2. Major: wrong word choices (원소→요소, 디모→데모, 캐머→카메라, 카이프→칩, etc.)
3. Major: systematic 새로고침 truncation
4. Minor: typos (메서이드→메서드, 기다일→기다릴, 막하고자→막고자, etc.)
5. Consistency: 디코레이터→데코레이터, fixture terminology, transliteration fixes
"""

import re

filepath = 'website/translations/ko.csv'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

original = content

# ============================================================================
# 1. CRITICAL: Garbled/corrupted text
# ============================================================================

# Thai character corruption: [ือ] prefix → remove brackets and Thai chars
# Line 49: zaือzeug → zauberzeug
content = content.replace('zaือzeug', 'zauberzeug')
# Lines 1835, 2073, 2084, 2607, 2745, 2922: [ือ] prefix on Korean text → remove it
content = content.replace('[ือ] ', '')

# Chinese character corruption: 을裸 → 을
# Line 2066: "값을裸 변수에" → "값을 변수에"
content = content.replace('값을裸 변수에', '값을 변수에')

# Mixed Korean/English: 스lide → 슬라이드
# Line 1503: "스lide 액션" → "슬라이드 액션"
content = content.replace('스lide', '슬라이드')

# Truncated English: Qu등 → Quasar 등
# Line 2366: "Qu등의 이벤트" → "Quasar 등의 이벤트"
content = content.replace('Qu등의', 'Quasar 등의')

# ============================================================================
# 2. MAJOR: Wrong word choices
# ============================================================================

# 원소 → 요소 (chemical element → UI element)
# MDN Korean uses 요소 for HTML/UI elements
content = content.replace('메뉴를 표시할 원소 내부에', '메뉴를 표시할 요소 내부에')
content = content.replace('사용자가 원소를 오른쪽 클릭하면', '사용자가 요소를 오른쪽 클릭하면')
content = content.replace('다이얼로그 원소에', '다이얼로그 요소에')
content = content.replace('다이얼로그는 원소입니다', '다이얼로그는 요소입니다')
content = content.replace('``ui.item`` 원소 내부에', '``ui.item`` 요소 내부에')

# 디모 → 데모 (incorrect transliteration of "demo")
# Standard Korean transliteration: 데모
content = content.replace('디모', '데모')

# 캐머 → 카메라 (incorrect transliteration of "camera")
content = content.replace('캐머의', '카메라의')

# 카이프 → 칩 (incorrect for "chip")
# English source: "when the chip is clicked"
content = content.replace('카이프가 클릭될', '칩이 클릭될')

# 그래픽 사용 인터페이스 → 그래픽 사용자 인터페이스 (missing 자 in GUI)
content = content.replace('그래픽 사용 인터페이스', '그래픽 사용자 인터페이스')

# 가이지 → 게이지 (incorrect transliteration of "gauge")
content = content.replace('가이지', '게이지')

# 웹서리얼 → 웹 시리얼 (Webserial)
content = content.replace('웹서리얼', '웹 시리얼')

# 웹소켓스 → 웹소켓 (Websockets — no need for plural marker in Korean)
content = content.replace('웹소켓스', '웹소켓')

# ============================================================================
# 3. MAJOR: Systematic 새로고침 truncation fixes
# ============================================================================

# The word 새로고침 (refresh) has been systematically truncated to 새로고 in many places.
# Fix each pattern carefully to preserve grammar.

# 새로고르기(decorator) → 새로고침(decorator)  (lines 2055, 2056)
content = content.replace('새로고르기(decorator)', '새로고침(decorator)')
# 새로고릴 수 있는 → 새로고칠 수 있는  (line 2055)
content = content.replace('새로고릴 수 있는', '새로고칠 수 있는')

# 새로고입니다 → 새로고칩니다 (line 956)
content = content.replace('새로고입니다', '새로고칩니다')

# 새로고될 수 있습니다 → 새로고침될 수 있습니다 (line 1027)
content = content.replace('새로고될 수 있습니다', '새로고침될 수 있습니다')

# 새로고 일 수 있는 → 새로고침할 수 있는 (line 2135)
content = content.replace('새로고 일 수 있는', '새로고침할 수 있는')

# 새로고 메서드 → 새로고침 메서드 (line 2136)
content = content.replace('새로고 메서드', '새로고침 메서드')

# 새로고 없이 → 새로고침 없이 (line 2402)
content = content.replace('새로고 없이', '새로고침 없이')

# 새로고 싶습니다 → 새로고치고 싶습니다 (lines 2727, 2733)
content = content.replace('새로고 싶습니다', '새로고치고 싶습니다')

# 비동기 새로고 작업 → 비동기 새로고침 작업 (line 2738)
content = content.replace('비동기 새로고 작업', '비동기 새로고침 작업')

# 새로고 작업은 → 새로고침 작업은 (line 2739)
content = content.replace('새로고 작업은', '새로고침 작업은')

# 새로고 가능한 → 새로고침 가능한 (lines 2740-2743, 4132)
content = content.replace('새로고 가능한', '새로고침 가능한')

# 새로고기 가능 → 새로고침 가능 (line 3177)
content = content.replace('새로고기 가능', '새로고침 가능')

# 새로고를 유도하지 → 새로고침을 유도하지 (line 3101)
content = content.replace('페이지 새로고를 유도하지', '페이지 새로고침을 유도하지')

# 새로고 있는 함수 → 새로고침 가능한 함수 (lines 4123, 4127)
# Context: "refreshable function" = 새로고침 가능한 함수
content = content.replace('새로고 있는 함수를', '새로고침 가능한 함수를')

# 새로고 있는 UI → 새로고침 가능한 UI (lines 4124, 4128)
content = content.replace('새로고 있는 UI는', '새로고침 가능한 UI는')

# 새로고 됩니다 → 새로고침됩니다 (line 4124)
content = content.replace('새로고 됩니다', '새로고침됩니다')

# "새로고" 버튼 → "새로고침" 버튼 (lines 4126, 4130)
content = content.replace('""새로고""', '""새로고침""')

# 비동기 새로고 함수 → 비동기 새로고침 함수 (line 4137)
content = content.replace('비동기 새로고 함수', '비동기 새로고침 함수')

# 새로고 중인 → 새로고침 중인 (line 4138)
content = content.replace('새로고 중인', '새로고침 중인')

# ============================================================================
# 4. MINOR: Typos
# ============================================================================

# 메서이드 → 메서드 (line 4545)
content = content.replace('메서이드', '메서드')

# 기다일 → 기다릴 (6 occurrences)
content = content.replace('기다일 수', '기다릴 수')

# 기다이기 → 기다리기 (line 3780)
content = content.replace('기다이기', '기다리기')

# 막하고자 → 막고자 (line 4713)
content = content.replace('막하고자', '막고자')

# 풀리됩니다 → 풀립니다 (line 668 — "is unwrapped automatically")
content = content.replace('풀리됩니다', '풀립니다')

# ============================================================================
# 5. CONSISTENCY: Terminology standardization
# ============================================================================

# 디코레이터 → 데코레이터 (standardize transliteration per Korean IT convention)
# MDN Korean and Python Korean docs use 데코레이터
content = content.replace('디코레이터', '데코레이터')

# pytest fixture: 테스트 장치 → 테스트 픽스처
# "장치" means "device/apparatus", incorrect for pytest fixtures
# Korean developer community standard: 픽스처 (transliteration)
content = content.replace('테스트 장치', '테스트 픽스처')

# screen 테스트 요소 → `screen` 픽스처
# "테스트 요소" (test element) is incorrect for pytest fixture
content = content.replace('`screen` 테스트 요소는 실제(헤드리스)', '`screen` 픽스처는 실제(헤드리스)')
content = content.replace('`screen` 테스트 요소는 내부적으로', '`screen` 픽스처는 내부적으로')

# ============================================================================
# Verify and write
# ============================================================================

changes = 0
for i, (a, b) in enumerate(zip(original, content)):
    if a != b:
        changes += 1

if content == original:
    print('No changes were made.')
else:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    # Count specific fixes
    fixes = []
    # Re-read and count line diffs
    orig_lines = original.splitlines()
    new_lines = content.splitlines()
    diff_lines = 0
    for ol, nl in zip(orig_lines, new_lines):
        if ol != nl:
            diff_lines += 1

    print(f'Successfully applied fixes to {filepath}')
    print(f'Lines modified: {diff_lines}')
    print(f'Character-level changes: {changes}')
