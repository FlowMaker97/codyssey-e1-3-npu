"""
main.py - 🧠 Mini NPU Simulator (Codyssey E1-3)

NPU(AI 전용 칩)가 하는 핵심 계산인 MAC(곱하고 더하기)을
파이썬 반복문으로 직접 흉내 내 보는 프로그램.

실행: python3 main.py
  1. 사용자 입력 (3x3)

외부 라이브러리(NumPy 등) 없이 표준 라이브러리만 사용한다.
"""

import time

# ----------------------------------------------------------------
# 상수 (프로그램 전체에서 쓰는 약속)
# ----------------------------------------------------------------
EPSILON = 1e-9      # 두 점수 차이가 이것보다 작으면 '같다(동점)'고 본다
REPEAT = 10         # 시간 측정 반복 횟수 (최소 10회)
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
                print("🚧 아직 준비 중인 기능입니다.")
            elif choice == "0":
                print("👋 시뮬레이터를 종료합니다.")
                break
            else:
                print("⚠️ 잘못된 선택입니다. 메뉴 번호를 입력하세요.")
    except (KeyboardInterrupt, EOFError):
        print("\n\n⚠️ 입력이 중단되어 안전하게 종료합니다.")


if __name__ == "__main__":
    main()
