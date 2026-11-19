"""
main.py - 🧠 Mini NPU Simulator (Codyssey E1-3)

NPU(AI 전용 칩)가 하는 핵심 계산인 MAC(곱하고 더하기)을
파이썬 반복문으로 직접 흉내 내 보는 프로그램.

실행: python3 main.py
  1. 사용자 입력 (3x3)

외부 라이브러리(NumPy 등) 없이 표준 라이브러리만 사용한다.
"""


# ----------------------------------------------------------------
# 상수 (프로그램 전체에서 쓰는 약속)
# ----------------------------------------------------------------


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
# 메인: 모드 선택
# ================================================================
def main():
    print("=== Mini NPU Simulator === (준비 중)")
    demo_a = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    demo_b = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
    print("MAC(십자가, 십자가) =", mac(demo_a, demo_a))
    print("MAC(십자가, X)     =", mac(demo_a, demo_b))


if __name__ == "__main__":
    main()
