# Write-up — Solve the Maze

## 1. Đề bài và ý tưởng

> eazyyyyyy! Solve the maze for the flag :))

Đề cung cấp ảnh `d4rkmaze.png`, kích thước **2048 × 332 pixel**, với điểm **START** ở góc dưới bên trái và **FINISH** ở góc dưới bên phải.

Ý tưởng là giải mê cung, sau đó quan sát hình dạng của đường đi. Trong bài này, **chính đường đi từ START đến FINISH tạo thành các chữ cái của thông điệp**.

Quy trình:

```text
Ảnh gốc → nhận diện lưới → dựng đồ thị các ô
        → BFS → truy vết đường đi → đọc chữ → định dạng flag
```

## 2. Chuyển ảnh thành đồ thị

### Nhận diện lưới

Chuyển ảnh sang grayscale: giá trị gần **0** là tường đen, gần **255** là nền trắng có thể đi qua.

Mê cung có các đường kẻ cách nhau khoảng **7–8 pixel**. Thay vì chia cứng theo bước 8 pixel và bị lệch dần, cộng độ tối `255 - gray` theo từng cột và từng hàng, rồi tìm các đỉnh bằng `find_peaks`.

```python
x_score = (255 - gray[9:298, :]).sum(axis=0)
y_score = (255 - gray[:304, 9:2039]).sum(axis=1)

xs = find_peaks(x_score, distance=5, prominence=2500)[0]
ys = find_peaks(y_score, distance=5, prominence=5000)[0]
```

Các vùng lấy mẫu loại phần chú thích ở dưới và hạn chế ảnh hưởng của lề ngoài. Tham số được chọn cho **đúng ảnh gốc của bài**, không phải cấu hình chung cho mọi mê cung.

Kết quả nhận diện được **259 vị trí đường kẻ dọc** và **38 vị trí đường kẻ ngang**, tương ứng **258 cột × 37 hàng = 9546 ô**.

Lấy trung điểm giữa hai đường kẻ liên tiếp làm tâm mỗi ô:

```python
cx = (xs[:-1] + xs[1:]) // 2
cy = (ys[:-1] + ys[1:]) // 2
```

### Xác định các ô thông nhau

Mỗi ô là một đỉnh. Chỉ xét bốn ô kề theo hướng lên, xuống, trái, phải. Hai ô được nối khi toàn bộ đoạn pixel giữa hai tâm không có tường; trong script, điều kiện là:

```python
segment.min() > 190
```

Kiểm tra cả đoạn nối thay vì chỉ màu của hai tâm: hai tâm đều trắng vẫn có thể bị ngăn bởi một bức tường.

**Lưu ý quan trọng:** cả START và FINISH đều mở ở cạnh dưới. Nếu tìm đường trên toàn ảnh mà cho phép đi vào nền trắng bên ngoài, thuật toán có thể đi vòng dưới mê cung. Đồ thị ở đây chỉ chứa các ô bên trong khung nên loại được đường tắt này.

## 3. Tìm đường bằng BFS

Dùng tọa độ **(hàng, cột)**, đánh số từ 0:

```python
start = (36, 0)
goal  = (36, 257)
```

BFS dùng một hàng đợi để mở rộng các ô đi tới được. Mỗi khi phát hiện ô mới, lưu `parent[ô_mới] = ô_hiện_tại`. Khi tới FINISH, lần ngược các giá trị `parent` về START rồi đảo danh sách để khôi phục đường đi.

Do mỗi lần sang ô kề có cùng chi phí, BFS tìm được đường có số bước ít nhất trong đồ thị này. Kết quả chạy trên ảnh gốc là **2236 ô trên đường đi**, tức **2235 lần chuyển ô**.

## 4. Script tái hiện

Cài thư viện và chạy:

```bash
python3 -m pip install pillow numpy scipy
python3 solve_maze.py d4rkmaze.png -o out
```

Dùng ảnh gốc, **không resize trước khi chạy**. Lưu phần sau thành `solve_maze.py`:

```python
#!/usr/bin/env python3
"""Solve the supplied 2048x332 d4rk maze; write an overlay and path-only image."""
import argparse
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.signal import find_peaks


def solve(source: Path, output: Path) -> None:
    with Image.open(source) as image:
        rgb = image.convert("RGB")
    if rgb.size != (2048, 332):
        raise ValueError("Use the original 2048x332 image; do not resize it first.")
    gray = np.asarray(rgb.convert("L"), dtype=np.int16)

    # Sum darkness by column/row, excluding the footer and outside margins.
    x_score = (255 - gray[9:298, :]).sum(axis=0)
    y_score = (255 - gray[:304, 9:2039]).sum(axis=1)
    xs = find_peaks(x_score, distance=5, prominence=2500)[0]
    ys = find_peaks(y_score, distance=5, prominence=5000)[0]
    if len(xs) != 259 or len(ys) != 38:
        raise ValueError("Unexpected grid: check the source image and thresholds.")

    # Nodes are cell centers, not wall intersections.
    cx = (xs[:-1] + xs[1:]) // 2
    cy = (ys[:-1] + ys[1:]) // 2
    rows, cols = len(cy), len(cx)
    start, goal = (rows - 1, 0), (rows - 1, cols - 1)

    def passage(r: int, c: int, nr: int, nc: int) -> bool:
        """Every pixel between adjacent centers must be brighter than 190."""
        if r == nr:
            segment = gray[cy[r], min(cx[c], cx[nc]):max(cx[c], cx[nc]) + 1]
        else:
            segment = gray[min(cy[r], cy[nr]):max(cy[r], cy[nr]) + 1, cx[c]]
        return bool(segment.min() > 190)

    parent = {start: None}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        if (r, c) == goal:
            break
        for dr, dc in ((0, 1), (1, 0), (-1, 0), (0, -1)):
            nr, nc = r + dr, c + dc
            node = (nr, nc)
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if node in parent or not passage(r, c, nr, nc):
                continue
            parent[node] = (r, c)
            queue.append(node)

    if goal not in parent:
        raise RuntimeError("No route found; check the input and wall threshold.")

    cells = []
    node = goal
    while node is not None:
        cells.append(node)
        node = parent[node]
    cells.reverse()

    points = [(int(cx[c]), int(cy[r])) for r, c in cells]
    # Extend the route through the two openings in the bottom border.
    points = [(points[0][0], 300)] + points + [(points[-1][0], 300)]
    output.mkdir(parents=True, exist_ok=True)
    overlay = rgb.copy()
    ImageDraw.Draw(overlay).line(points, fill=(211, 25, 57), width=5)
    overlay.save(output / "maze-solved.png")
    path_only = Image.new("RGB", rgb.size, "white")
    ImageDraw.Draw(path_only).line(points, fill="black", width=5)
    path_only.save(output / "maze-path-only.png")

    print(f"Image: {rgb.width} x {rgb.height}")
    print(f"Grid: {rows} rows x {cols} columns = {rows * cols} cells")
    print(f"Start (row, col): {start}; goal: {goal}")
    print(f"Path: {len(cells)} cells, {len(cells) - 1} moves")
    print(f"Saved: {output / 'maze-solved.png'}")
    print(f"Saved: {output / 'maze-path-only.png'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("-o", "--out", type=Path, default=Path("out"))
    args = parser.parse_args()
    try:
        solve(args.image, args.out)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Error: {error}\n")
```

Output từ lần chạy kiểm tra:

```text
Image: 2048 x 332
Grid: 37 rows x 258 columns = 9546 cells
Start (row, col): (36, 0); goal: (36, 257)
Path: 2236 cells, 2235 moves
```

Script xuất `out/maze-solved.png` để xem đường đi trên mê cung và `out/maze-path-only.png` để xem riêng đường đi. Script không hardcode thông điệp và không tự nhận dạng chữ; nội dung được đọc từ hình kết quả.

## 5. Đọc thông điệp và lấy flag

Ảnh đường đi chồng lên mê cung:

![Đường đi trên mê cung](out/maze-solved.png)

Khi bỏ lớp tường, thông điệp hiện rõ hơn:

![Chỉ giữ đường đi](out/maze-path-only.png)

Đọc từ trái sang phải:

```text
D4RK HOW WAS THE MAZE
```

Chú thích dưới ảnh gốc đưa ví dụ:

```text
d4rk hello world → d4rk{hello_world}
```

Làm theo ví dụ: `d4rk` là tiền tố bên ngoài dấu ngoặc; phần còn lại chuyển sang chữ thường và nối các từ bằng dấu `_`.

```text
HOW WAS THE MAZE → how_was_the_maze
```

**Flag:**

```text
d4rk{how_was_the_maze}
```

Điểm mấu chốt của bài là **đường đi cũng chính là dữ liệu cần đọc**. Giải xong mê cung chưa phải bước cuối; tách đường đi khỏi những bức tường mới làm lộ thông điệp.
