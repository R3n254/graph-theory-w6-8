import sys

sys.setrecursionlimit(100000)

MOVES = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]


def knights_tour(cols, rows, start_x, start_y):
    """Return a list of (x, y) coordinates covering every square once, or None."""
    total = cols * rows
    if not (0 <= start_x < cols and 0 <= start_y < rows):
        return None

    visited = [[False] * rows for _ in range(cols)]

    def neighbors(x, y):
        result = []
        for dx, dy in MOVES:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows and not visited[nx][ny]:
                result.append((nx, ny))
        return result

    path = [(start_x, start_y)]
    visited[start_x][start_y] = True

    def solve(x, y):
        if len(path) == total:
            return True
        # Warnsdorff's rule: try squares with the fewest onward moves first
        candidates = sorted(neighbors(x, y), key=lambda p: len(neighbors(*p)))
        for nx, ny in candidates:
            visited[nx][ny] = True
            path.append((nx, ny))
            if solve(nx, ny):
                return True
            path.pop()          # backtrack
            visited[nx][ny] = False
        return False

    return path if solve(start_x, start_y) else None


def main():
    cols, rows = map(int, input().split())
    start_x, start_y = map(int, input().split())

    path = knights_tour(cols, rows, start_x, start_y)

    if path is None:
        print("path not found")
    else:
        for x, y in path:
            print(f"{x},{y}")


if __name__ == "__main__":
    main()
