"""
main.py - 🧠 Mini NPU Simulator (Codyssey E1-3)

NPU(AI 전용 칩)가 하는 핵심 계산인 MAC(곱하고 더하기)을
파이썬 반복문으로 직접 흉내 내 보는 프로그램.

실행: python3 main.py
  1. 사용자 입력 (3x3)
  2. data.json 분석

외부 라이브러리(NumPy 등) 없이 표준 라이브러리만 사용한다.
"""

import json
import os
import re
import time

# ----------------------------------------------------------------
# 상수 (프로그램 전체에서 쓰는 약속)
# ----------------------------------------------------------------
EPSILON = 1e-9      # 두 점수 차이가 이것보다 작으면 '같다(동점)'고 본다
REPEAT = 10         # 시간 측정 반복 횟수 (최소 10회)
CROSS = "Cross"     # 표준 라벨 1
X = "X"             # 표준 라벨 2
UNDECIDED = "UNDECIDED"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

# 여러 가지 모양으로 들어오는 라벨을 표준 라벨(Cross / X)로 바꾸는 표
LABEL_MAP = {
    "+": CROSS,
    "cross": CROSS,
    "x": X,
}
PERF_SIZES = [3, 5, 13, 25]
LINE = "#" + "-" * 39


# ================================================================
# 1. 데이터 구조: N×N 2차원 리스트
# ================================================================
def create_matrix(n, value=0.0):
    """n×n 크기의 2차원 리스트를 만든다. (모든 칸 = value)"""
    return [[value for _ in range(n)] for _ in range(n)]


def get_value(matrix, row, col):
    """(row, col) 위치의 값을 읽는다."""
    return matrix[row][col]


def set_value(matrix, row, col, value):
    """(row, col) 위치에 값을 저장한다."""
    matrix[row][col] = value


def check_matrix(matrix):
    """정사각 숫자 행렬인지 검사한다.

    돌려주는 값: (N, None)       -> 정상, N×N
               (None, "이유")   -> 문제 있음
    """
    if not isinstance(matrix, list) or len(matrix) == 0:
        return None, "2차원 리스트가 아닙니다"
    n = len(matrix)
    for row_index, row in enumerate(matrix):
        if not isinstance(row, list):
            return None, f"{row_index + 1}행이 리스트가 아닙니다"
        if len(row) != n:
            return None, f"정사각형이 아닙니다 ({n}행인데 {row_index + 1}행의 열이 {len(row)}개)"
        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return None, f"숫자가 아닌 값이 있습니다: {value!r}"
    return n, None


# ================================================================
# 2. MAC 연산 (Multiply-Accumulate: 같은 위치끼리 곱해서 모두 더하기)
# ================================================================
def mac(pattern, filter_matrix):
    """2차원 패턴과 필터의 MAC 점수를 계산한다. (이중 for 문 → N×N 번 곱셈)"""
    n = len(pattern)
    total = 0.0
    for row in range(n):
        for col in range(n):
            total += pattern[row][col] * filter_matrix[row][col]
    return total


# ================================================================
# 3. 판정 (epsilon 기반 비교)
# ================================================================
def judge(score_a, score_b, label_a, label_b, tie_label):
    """두 점수를 비교해 더 큰 쪽 라벨을 돌려준다.

    부동소수점 오차 때문에 0.9 와 0.8999999999999999 처럼
    '사실상 같은' 값이 생길 수 있으므로, 차이가 EPSILON 보다 작으면 동점(tie_label)으로 본다.
    """
    if abs(score_a - score_b) < EPSILON:
        return tie_label
    if score_a > score_b:
        return label_a
    return label_b


# ================================================================
# 4. 시간 측정
# ================================================================
def measure_ms(func, first, second, repeat=REPEAT):
    """func(first, second) 를 repeat 번 실행한 평균 시간(ms)을 돌려준다.

    입력/출력/파일 읽기는 빼고, '연산 함수 호출 구간'만 잰다.
    """
    func(first, second)  # 워밍업 1회 (측정에서 제외)
    start = time.perf_counter()
    for _ in range(repeat):
        func(first, second)
    end = time.perf_counter()
    return (end - start) / repeat * 1000


# ================================================================
# 5. 라벨 정규화
# ================================================================
def normalize_label(raw):
    """'+', 'cross', 'x', 'X', ' Cross ' 등을 표준 라벨 Cross / X 로 바꾼다.

    모르는 라벨이면 None 을 돌려준다.
    """
    if not isinstance(raw, str):
        return None
    key = raw.strip().lower()  # 앞뒤 공백 제거 + 소문자로 통일
    return LABEL_MAP.get(key)


# ================================================================
# 6. 패턴 생성기 (N×N 십자가 / X 자동 생성)
# ================================================================
def generate_cross(n):
    """가운데 행과 가운데 열이 1 인 N×N 십자가(+) 패턴"""
    matrix = create_matrix(n)
    center = n // 2
    for i in range(n):
        set_value(matrix, center, i, 1.0)
        set_value(matrix, i, center, 1.0)
    return matrix


def generate_x(n):
    """두 대각선이 1 인 N×N X 패턴"""
    matrix = create_matrix(n)
    for i in range(n):
        set_value(matrix, i, i, 1.0)
        set_value(matrix, i, n - 1 - i, 1.0)
    return matrix


# ================================================================
# 7. 출력 도우미
# ================================================================
def print_header(title):
    print(LINE)
    print(f"# {title}")
    print(LINE)


def format_score(score):
    """점수를 보기 좋게: 정수처럼 딱 떨어지면 5.0, 아니면 오차가 보이게 그대로"""
    return repr(float(score))


def print_matrix(matrix):
    for row in matrix:
        print("   " + " ".join(f"{value:g}" for value in row))


# ================================================================
# 8. 모드 1: 사용자 입력 (3×3)
# ================================================================
def parse_row(line, n):
    """한 줄을 숫자 n 개짜리 리스트로 바꾼다. 실패하면 None.

    '0 1 0' (공백 구분) 이 기본이고, 편의상 '010' 처럼 붙여 쓴 0/1 도 받아준다.
    """
    parts = line.split()
    if len(parts) == 1 and len(parts[0]) == n and all(ch in "01" for ch in parts[0]):
        parts = list(parts[0])  # '010' -> ['0', '1', '0']
    if len(parts) != n:
        return None
    try:
        return [float(part) for part in parts]
    except ValueError:
        return None


def read_matrix(name, n=3):
    """name 행렬을 한 줄씩 n 줄 입력받는다. 잘못된 줄은 그 줄만 다시 입력받는다."""
    print(f"\n{name} ({n}줄 입력, 공백 구분)")
    matrix = create_matrix(n)
    row = 0
    while row < n:
        line = input(f"  [{row + 1}/{n}] ").strip()
        values = parse_row(line, n)
        if values is None:
            print(f"  ⚠️ 입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.")
            continue
        for col in range(n):
            set_value(matrix, row, col, values[col])
        row += 1
    return matrix


def run_user_mode():
    """모드 1: 필터 A, B 입력 → 저장 확인 → 패턴 입력 → MAC → 판정 → 성능(3×3)"""
    print_header("[1] 필터 입력")
    filter_a = read_matrix("필터 A")
    filter_b = read_matrix("필터 B")
    print("\n✓ 필터 저장 완료")
    print(" 필터 A:")
    print_matrix(filter_a)
    print(" 필터 B:")
    print_matrix(filter_b)

    print()
    print_header("[2] 패턴 입력")
    pattern = read_matrix("패턴")

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    elapsed = measure_ms(mac, pattern, filter_a)
    result = judge(score_a, score_b, "A", "B", "판정 불가")

    print()
    print_header("[3] MAC 결과")
    print(f"A 점수: {format_score(score_a)}")
    print(f"B 점수: {format_score(score_b)}")
    print(f"연산 시간(평균/{REPEAT}회): {elapsed:.4f} ms")
    if result == "판정 불가":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {result}")

    print()
    print_performance("[4] 성능 분석 (3×3)", [3], {3: (pattern, filter_a)})


# ================================================================
# 9. 모드 2: data.json 분석
# ================================================================
def load_json(path):
    """JSON 파일을 읽는다. 실패하면 (None, 오류 메시지)."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file), None
    except FileNotFoundError:
        return None, f"파일이 없습니다: {path}"
    except json.JSONDecodeError as error:
        return None, f"JSON 형식 오류: {error}"
    except OSError as error:
        return None, f"파일을 읽을 수 없습니다: {error}"


def load_filters(raw_filters):
    """filters 를 읽어서 {N: {"Cross": 행렬, "X": 행렬}} 로 정리한다.

    필터 키('cross', 'x')도 표준 라벨로 정규화한다.
    문제가 있는 크기는 건너뛰고 이유를 출력한다. (프로그램은 멈추지 않음)
    """
    filters = {}
    if not isinstance(raw_filters, dict):
        print("✗ filters 항목이 없거나 형식이 잘못되었습니다.")
        return filters

    for size_key, group in raw_filters.items():
        if not isinstance(size_key, str) or not size_key.startswith("size_") or not size_key[5:].isdigit():
            print(f"✗ {size_key}: 필터 키 형식 오류 (size_N 이어야 함)")
            continue
        n = int(size_key[5:])
        if not isinstance(group, dict):
            print(f"✗ {size_key}: 필터 묶음이 dict 가 아닙니다")
            continue

        loaded = {}
        problem = None
        for raw_label, matrix in group.items():
            label = normalize_label(raw_label)
            if label is None:
                problem = f"알 수 없는 필터 라벨 {raw_label!r}"
                break
            size, reason = check_matrix(matrix)
            if size is None:
                problem = f"{label} 필터 형식 오류 ({reason})"
                break
            if size != n:
                problem = f"{label} 필터 크기 불일치 (키는 {n}×{n}, 실제 {size}×{size})"
                break
            loaded[label] = matrix
        if problem is None and (CROSS not in loaded or X not in loaded):
            problem = "Cross 와 X 필터가 둘 다 있어야 합니다"
        if problem is not None:
            print(f"✗ {size_key} 필터 로드 실패: {problem}")
            continue

        filters[n] = loaded
        print(f"✓ {size_key} 필터 로드 완료 ({CROSS}, {X})")
    return filters


def report_fail(reason):
    """[FAIL] 사유를 출력하고 (False, 사유) 를 돌려준다."""
    print(f"[FAIL] {reason}")
    return False, reason


def analyze_pattern(key, item, filters):
    """패턴 1개를 검사/판정한다.

    돌려주는 값: (PASS 여부 True/False, 실패 사유 또는 None)
    어떤 문제가 있어도 예외로 멈추지 않고 FAIL + 사유를 돌려준다.
    """
    print(f"--- {key} ---")

    # (1) 키에서 N 추출: size_{N}_{idx}
    match = re.fullmatch(r"size_(\d+)_(\d+)", str(key))
    if match is None:
        return report_fail("키 형식 오류 (size_{N}_{idx} 형태가 아님)")
    n = int(match.group(1))

    # (2) 항목 구조 확인
    if not isinstance(item, dict) or "input" not in item or "expected" not in item:
        return report_fail("스키마 오류 (input / expected 가 없음)")

    # (3) expected 라벨 정규화
    expected = normalize_label(item["expected"])
    if expected is None:
        return report_fail(f"expected 라벨 오류 ({item['expected']!r} 은 Cross/X 로 바꿀 수 없음)")

    # (4) 해당 크기 필터가 있는지
    if n not in filters:
        return report_fail(f"size_{n} 필터가 없음")

    # (5) 패턴 형식/크기 검증
    size, reason = check_matrix(item["input"])
    if size is None:
        return report_fail(f"패턴 형식 오류 ({reason})")
    if size != n:
        return report_fail(f"크기 불일치 (패턴 {size}×{size}, 필터 size_{n} = {n}×{n})")

    # (6) MAC 연산 + 판정
    pattern = item["input"]
    cross_score = mac(pattern, filters[n][CROSS])
    x_score = mac(pattern, filters[n][X])
    result = judge(cross_score, x_score, CROSS, X, UNDECIDED)
    print(f"Cross 점수: {format_score(cross_score)}")
    print(f"X 점수: {format_score(x_score)}")

    if result == UNDECIDED:
        print(f"판정: {UNDECIDED} | expected: {expected} | FAIL (동점 규칙)")
        return False, f"동점(UNDECIDED) 처리 규칙에 따라 FAIL (|차이| = {abs(cross_score - x_score):.3g} < {EPSILON})"
    if result == expected:
        print(f"판정: {result} | expected: {expected} | PASS")
        return True, None
    print(f"판정: {result} | expected: {expected} | FAIL")
    return False, f"판정 불일치 (판정 {result}, expected {expected})"



def run_json_mode():
    """모드 2: 필터 로드 → 패턴 분석 → 성능 분석 → 결과 요약"""
    data, error = load_json(DATA_FILE)
    if data is None:
        print(f"⚠️ data.json 을 불러오지 못했습니다. ({error})")
        print("   main.py 와 같은 폴더에 data.json 이 있는지 확인하세요.")
        return
    if not isinstance(data, dict):
        print("⚠️ data.json 최상위 구조가 dict({...}) 가 아닙니다.")
        return

    print_header("[1] 필터 로드")
    filters = load_filters(data.get("filters"))

    print()
    print_header("[2] 패턴 분석 (라벨 정규화 적용)")
    patterns = data.get("patterns")
    if not isinstance(patterns, dict):
        print("✗ patterns 항목이 없거나 형식이 잘못되었습니다.")
        patterns = {}

    results = []  # (키, PASS 여부, 사유) 를 모아 둔다
    for key, item in patterns.items():
        try:
            passed, reason = analyze_pattern(key, item, filters)
        except Exception as error:  # 예상 못 한 오류도 그 케이스만 FAIL 로 처리 (프로그램은 계속)
            passed, reason = report_fail(f"예상치 못한 오류: {error}")
        results.append((key, passed, reason))

    print()
    perf_inputs = {}
    for n in PERF_SIZES:
        if n in filters:
            perf_inputs[n] = (generate_cross(n), filters[n][CROSS])   # data.json 필터 사용
        else:
            perf_inputs[n] = (generate_cross(n), generate_x(n))       # 없으면 생성기로 (예: 3×3)
    print_performance("[3] 성능 분석", PERF_SIZES, perf_inputs)

    print()
    print_summary(results)


# ================================================================
# 10. 성능 분석
# ================================================================
def print_performance(title, sizes, inputs):
    """크기별 평균 MAC 시간(ms)과 연산 횟수(N²) 표를 출력한다."""
    print_header(f"{title} (평균/{REPEAT}회)")
    print(f"{'크기':<8}{'평균 시간(ms)':>14}{'연산 횟수(N²)':>14}")
    print("-" * 40)
    for n in sizes:
        pattern, filter_matrix = inputs[n]
        ms = measure_ms(mac, pattern, filter_matrix)
        print(f"{f'{n}×{n}':<8}{ms:>14.4f}{n * n:>14}")


# ================================================================
# 11. 결과 요약
# ================================================================
def print_summary(results):
    """전체/통과/실패 수와 실패 케이스 목록을 출력한다."""
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = [(key, reason) for key, ok, reason in results if not ok]

    print_header("[4] 결과 요약")
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {len(failed)}개")
    if failed:
        print("실패 케이스:")
        for key, reason in failed:
            print(f"  - {key}: {reason}")
    else:
        print("실패 케이스 없음 (라벨 정규화 + epsilon 비교 정책 덕분)")
    print("\n(상세 원인 분석 및 복잡도 설명은 README.md 의 '결과 리포트' 섹션 참고)")


# ================================================================
# 메인: 모드 선택
# ================================================================
def main():
    try:
        while True:
            print("\n=== Mini NPU Simulator ===\n")
            print("[모드 선택]")
            print("1. 사용자 입력 (3x3)")
            print("2. data.json 분석")
            print("0. 종료")
            choice = input("선택: ").strip()
            if choice == "1":
                run_user_mode()
            elif choice == "2":
                run_json_mode()
            elif choice == "0":
                print("👋 시뮬레이터를 종료합니다.")
                break
            else:
                print("⚠️ 잘못된 선택입니다. 메뉴 번호를 입력하세요.")
    except (KeyboardInterrupt, EOFError):
        print("\n\n⚠️ 입력이 중단되어 안전하게 종료합니다.")


if __name__ == "__main__":
    main()
