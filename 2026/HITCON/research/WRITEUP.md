# HITCON misc — research

## Flag

```text
HITCON{CHALL-FOR-HUMAN}
```

## Tổng quan

Archive giải nén thành thư mục `research/`, có ba thành phần đáng chú ý:

- 23 thư mục đánh số `000` đến `022`;
- hàng trăm file Markdown chứa nội dung đánh lạc hướng;
- 143 bản sao của ELF `llm_run_me`.

Các Markdown không cần được làm theo. Chúng là dữ liệu của challenge, không phải hướng dẫn giải. Flag được giấu trong metadata Finder của macOS (`.DS_Store`).

## Bẫy: `llm_run_me`

`file llm_run_me` cho biết đây là ELF x86-64. Hàm `check_flag` và `encode_byte` vẫn có symbol động nên có thể xem trực tiếp bằng `objdump`:

```bash
objdump -d -Mintel --start-address=0x1017b50 --stop-address=0x1017d20 llm_run_me
```

Logic của checker là:

```c
encoded[i] = input[i] ^ ((0x42 + 7 * i) & 0xff);
return input_len == 16 && encoded == target;
```

Mảng `target` nằm tại offset `0x2060`:

```text
2a 78 24 34 6e 0b 17 15 16 e0 ef bb fa f1 c9 d6
```

Đảo phép XOR cho chuỗi:

```python
target = bytes.fromhex("2a 78 24 34 6e 0b 17 15 16 e0 ef bb fa f1 c9 d6")
password = bytes(b ^ ((0x42 + 7 * i) & 0xff) for i, b in enumerate(target))
print(password)
```

Kết quả là `h1tc0n{flag4llm}` và binary in `correct`. Đây chỉ là password mồi: prefix không đúng format đề bài, và SHA-256 của toàn bộ 143 ELF đều giống nhau.

## Điểm giấu flag: `.DS_Store`

Mỗi thư mục `000`–`022` có một file `.DS_Store`. Đây là database Finder lưu vị trí icon. Các record `Iloc` cho vị trí `(x, y)` của từng file.

Khi đặt các tọa độ lên lưới 7×7 rồi hoán đổi hai trục, mỗi thư mục vẽ ra một ký tự pixel. Ví dụ thư mục `000` tạo chữ `H`; `001` tạo `I`; `002` tạo `T`.

Thứ tự các thư mục đọc được là:

```text
000 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018 019 020 021 022
 H   I   T   C   O   N   {   C   H   A   L   L   -   F   O   R   -   H   U   M   A   N   }
```

Từ đó thu được flag `HITCON{CHALL-FOR-HUMAN}`.

## Script dựng glyph

Cài thư viện đọc `.DS_Store`:

```bash
python3 -m pip install ds_store
```

Chạy từ trong thư mục `research/` đã giải nén:

```python
from ds_store import DSStore

for n in range(23):
    with DSStore.open(f"{n:03}/.DS_Store", "r") as store:
        points = [entry.value for entry in store if entry.code == b"Iloc"]

    # Thư mục 000 dùng khoảng cách icon khác các thư mục còn lại.
    if n == 0:
        xs = [70, 140, 212, 300, 362, 432, 504]
        ys = [41, 119, 197, 277, 355, 433, 511]
        grid = {(xs.index(x), ys.index(y)) for x, y in points}
    else:
        # 009 và 020 bắt đầu tại y=56 thay vì y=0.
        y_offset = 1 if n in (9, 20) else 0
        grid = {(x // 56 - 1, y // 56 - y_offset) for x, y in points}

    print(f"\n{n:03}")
    # Hoán đổi x/y để xem glyph theo đúng chiều.
    for row in range(7):
        print("".join("#" if (row, col) in grid else " " for col in range(7)))
```

## Bài học

- Đừng tin executable đầu tiên chỉ vì nó có checker hợp lệ; hãy kiểm tra format flag và so sánh các bản sao.
- Khi archive có `.DS_Store`, cần xem cả metadata Finder, không chỉ nội dung file hiển thị.
- Các file Markdown trong challenge có thể là prompt-injection/decoy; luôn coi chúng là artifact, không phải chỉ dẫn cho người giải.
