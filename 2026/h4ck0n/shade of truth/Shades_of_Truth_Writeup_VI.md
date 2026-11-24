# Shades of Truth — Write-up

**Dạng bài:** Steganography, PNG metadata, low-bit planes, ASCII art và Caesar cipher.  
**File:** `chall.png`  
**Flag format:** `d4rk{...}`

> I was never a bright student but i still read between the lines

## 1. Ý tưởng tổng thể

Ảnh được cung cấp là một phong cảnh ban đêm. Nội dung cần tìm không nằm ở những đường núi hay vị trí các ngôi sao, mà nằm trong hai bit thấp nhất của kênh đỏ và xanh lá.

Chuỗi giải:

```text
chall.png
  → đọc metadata Charset = " .:-=+*#%@"
  → lấy hai bit thấp nhất của R và G
  → ghép index = ((R & 3) << 2) | (G & 3)
  → biểu diễn các index thành ảnh xám / ASCII art
  → đọc g4un{dvf11_o0y3}
  → Caesar dịch lùi 3 chữ cái
  → d4rk{asc11_l0v3}
```

Điểm quan trọng: phần trích xuất tạo ra **một hình có chữ**, không phải một chuỗi byte ASCII chứa trực tiếp `g4un{...}`.

## 2. Kiểm tra file và metadata

Dùng file gốc, không dùng ảnh chụp màn hình hoặc ảnh đã được resize/chuyển định dạng.

```bash
file chall.png
sha256sum chall.png
```

Kết quả trên file được cung cấp:

```text
chall.png: PNG image data, 900 x 250, 8-bit/color RGB, non-interlaced
268098946c8d197ef0f5b60b603964a723eedf7df637ed00fddb4114589c99d1
```

Kích thước file là **268280 byte**. Kiểm tra cấu trúc PNG cho thấy một chunk `tEXt` tại offset `0x21`, với payload:

```python
b'Charset\x00 .:-=+*#%@'
```

`\x00` phân cách tên metadata với giá trị. Dấu cách sau đó là phần tử đầu tiên của giá trị, không phải khoảng trắng thừa. Không có byte nào nối sau chunk `IEND` trong mẫu này.

Đọc metadata bằng Pillow:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install Pillow

python - <<'PY'
from PIL import Image

with Image.open("chall.png") as im:
    print("Size:", im.size)
    print("Mode:", im.mode)
    print("Metadata:", im.info)
    print("Charset:", repr(im.info["Charset"]))
    print("Length:", len(im.info["Charset"]))
PY
```

Output:

```text
Size: (900, 250)
Mode: RGB
Metadata: {'Charset': ' .:-=+*#%@'}
Charset: ' .:-=+*#%@'
Length: 10
```

Chuỗi này gợi ý một bảng ký tự dùng để biểu diễn các mức đậm nhạt:

```text
Index:      0       1   2   3   4   5   6   7   8   9
Character: [space]  .   :   -   =   +   *   #   %   @
```

Tên bài *Shades of Truth* và từ “bright” phù hợp với hướng phân tích độ sáng. “Read between the lines” cũng có thể liên hệ tới hình được dựng từ các dòng ASCII. Đây là cách diễn giải gợi ý; metadata và kết quả trích xuất mới là bằng chứng quyết định.

## 3. Tìm quy luật trong các bit thấp

Mỗi kênh màu của ảnh này là một số nguyên 8 bit. Hai bit thấp nhất lấy bằng:

```python
low2 = value & 0b11
```

Với số nguyên không âm, phép này tương đương:

```python
low2 = value % 4
```

Kiểm tra phân bố `R & 3`, `G & 3`, `B & 3` cho kết quả:

```text
R: {0: 218175, 1: 2750, 2: 4075}
G: {0: 216500, 1: 5050, 2: 1875, 3: 1575}
B: {0: 56327, 1: 56048, 2: 56207, 3: 56418}
```

Ở R và G, giá trị 0 chiếm phần lớn; B phân bố khá đều. Đây là dấu hiệu đáng thử ở R/G, chưa phải bằng chứng đủ để kết luận độc lập.

Metadata có 10 phần tử, tức index hợp lệ là `0..9`. Cần ít nhất 4 bit để chứa một index thuộc tập này. Một giả thuyết đơn giản là **ghép hai bit từ một kênh với hai bit từ kênh khác**.

Ta thử sáu cặp có thứ tự, với kênh thứ nhất cung cấp hai bit cao của index:

```python
from itertools import permutations
from PIL import Image

with Image.open("chall.png") as im:
    data = im.tobytes()
    charset = im.info["Charset"]

channels = [data[i::3] for i in range(3)]
for a, b in permutations(range(3), 2):
    values = [
        ((x & 3) << 2) | (y & 3)
        for x, y in zip(channels[a], channels[b])
    ]
    invalid = sum(value >= len(charset) for value in values)
    print("RGB"[a] + "RGB"[b], min(values), max(values), invalid)
```

Kết quả:

| Cặp kênh | Miền giá trị quan sát | Số index nằm ngoài `0..9` |
|---|---|---:|
| RG | 0–9 | 0 |
| RB | 0–11 | 2035 |
| GR | 0–13 | 1575 |
| GB | 0–15 | 2498 |
| BR | 0–14 | 57441 |
| BG | 0–15 | 57229 |

Trong sáu cách ghép này, chỉ **RG** cho toàn bộ index nằm trong bảng Charset. Khi dựng lại ảnh, RG cũng tạo thành chữ đọc được, xác nhận hướng này.

Không được dùng `% 10` hay ép những giá trị lớn hơn 9 về 9 để làm một giả thuyết sai có vẻ hợp lệ.

## 4. Giải thích công thức ghép

Công thức đúng là:

```python
index = ((R & 3) << 2) | (G & 3)
```

Tương đương:

```python
index = 4 * (R % 4) + (G % 4)
```

Nếu hai bit thấp của R là `r1r0` và của G là `g1g0`, index có biểu diễn:

```text
r1 r0 g1 g0
```

Dịch trái hai bit đưa phần R sang vị trí cao. Hai phần không chồng bit, nên OR ở đây có cùng kết quả với phép cộng.

**Ví dụ thật trong ảnh**, tại `(x=705, y=90)`, tọa độ bắt đầu từ 0:

```text
RGB = (46, 33, 76)

R = 46 = 00101110₂ → R & 3 = 10₂ = 2
G = 33 = 00100001₂ → G & 3 = 01₂ = 1

index = (2 << 2) | 1
      = 1001₂
      = 9

Charset[9] = '@'
```

Kênh B không cần dùng để phục hồi lớp nội dung này. Điều đó không phải khẳng định đã kiểm tra mọi phương pháp giấu tin có thể có trên B.

## 5. Khôi phục ảnh và ASCII art

Giữ nguyên tọa độ từng pixel. Tại mỗi vị trí, tính index rồi chọn một trong hai cách biểu diễn.

**ASCII art:** ghi `Charset[index]`. Mỗi hàng ảnh trở thành một dòng văn bản.

**Ảnh grayscale:** biến index thành độ sáng bằng `index * 255 // 9`. Khi đó `0` là đen và `9` là trắng. Đây là cách trực quan hóa các index, không phải lấy grayscale thông thường của ảnh phong cảnh.

Script trích xuất ngắn:

```python
from pathlib import Path
from PIL import Image

with Image.open("chall.png") as im:
    width, height = im.size
    charset = im.info["Charset"]  # Giữ cả dấu cách đầu tiên.
    rgb = im.tobytes()

indices = bytes(
    ((rgb[i] & 3) << 2) | (rgb[i + 1] & 3)
    for i in range(0, len(rgb), 3)
)
assert max(indices) < len(charset)

rows = [
    "".join(charset[v] for v in indices[y * width:(y + 1) * width])
    for y in range(height)
]
Path("hidden-ascii.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")

gray = bytes(v * 255 // (len(charset) - 1) for v in indices)
Image.frombytes("L", (width, height), gray).save("extracted.png")
```

Ảnh khôi phục:

![Lớp nội dung trích xuất từ hai bit thấp của R và G](extracted.png)

Đọc được:

```text
g4un{dvf11_o0y3}
```

Bản phóng to phần chữ:

![Phần chữ được phóng to bằng nearest-neighbor](payload-crop.png)

Trong mẫu này, mọi index được lặp thành khối **5×5** đồng nhất. Sau khi xác minh tính chất đó, có thể lấy một giá trị trên mỗi khối để xuất bản ASCII gọn **180×50**. Script đầy đủ tự kiểm tra điều kiện này trước khi tạo `hidden-ascii-compact.txt`.

Đây cũng là lý do không nhất thiết thu được plaintext bằng cách ghép mỗi tám bit rồi đọc thành byte ASCII: dữ liệu đang mô tả **hình dạng chữ**, chứ không lưu trực tiếp các mã byte của chuỗi chữ đó.

## 6. Giải lớp Caesar

Chuỗi vừa đọc bắt đầu bằng `g4un{`, trong khi định dạng yêu cầu là `d4rk{`:

```text
g → d   dịch lùi 3
4 → 4   giữ nguyên
u → r   dịch lùi 3
n → k   dịch lùi 3
```

Thử dịch lùi 3 đối với toàn bộ chữ cái, giữ nguyên chữ số và các dấu:

```text
g4un{dvf11_o0y3}
        ↓ Caesar -3
d4rk{asc11_l0v3}
```

Code:

```python
ciphertext = "g4un{dvf11_o0y3}"  # Chép lại từ ảnh khôi phục.
result = []

for c in ciphertext:
    if "a" <= c <= "z":
        result.append(chr((ord(c) - ord("a") - 3) % 26 + ord("a")))
    elif "A" <= c <= "Z":
        result.append(chr((ord(c) - ord("A") - 3) % 26 + ord("A")))
    else:
        result.append(c)

print("".join(result))
```

Output:

```text
d4rk{asc11_l0v3}
```

`asc11_l0v3` gợi cách viết “ASCII love”, phù hợp với bảng ký tự và lớp hình ẩn đã tìm thấy. Ý nghĩa này là bước đối chiếu bổ sung, không thay cho việc trích xuất.

## 7. Tái hiện bằng script đầy đủ

File `solve.py` đi kèm kiểm tra nguồn, đọc Charset, tạo ảnh/ASCII art, ghi thống kê và thử các khóa Caesar với prefix `d4rk{`.

```bash
python solve.py chall.png -o out
```

Mở `out/extracted.png` để đọc chuỗi. Sau đó:

```bash
python solve.py chall.png -o out --ciphertext 'g4un{dvf11_o0y3}'
```

Phần cuối output:

```text
Manual transcription: g4un{dvf11_o0y3}
Caesar backward shift: 3
Flag: d4rk{asc11_l0v3}
```

`--ciphertext` là phần chữ được người giải đọc từ ảnh; script không dùng OCR và không tự nhận diện chữ từ pixel. Kết quả trích xuất đã được chạy lại trên file gốc và đối chiếu; không có thao tác nộp flag lên máy chủ cuộc thi.

## 8. Kết luận

**Flag:**

```text
d4rk{asc11_l0v3}
```

Mấu chốt của bài là nhận ra metadata `Charset` mô tả 10 mức ký tự; tìm được bốn bit index phân bố trên R/G; giữ nguyên cấu trúc hai chiều để nhìn thấy chữ; rồi dùng prefix đã biết để xác định phép Caesar.

Các bẫy cần tránh: bỏ dấu cách đầu Charset, sửa/resize ảnh trước khi trích bit, đảo thứ tự R/G, ép mọi index về `0..9`, hoặc cho rằng mọi bài LSB đều phải ra một luồng byte plaintext.

## Phụ lục: bằng chứng và mã nguồn

Các số liệu của mẫu được ghi trong `evidence.txt`; output của lần chạy được lưu ở `run.txt`. Các file `hidden-ascii.txt` và `hidden-ascii-compact.txt` là dữ liệu trích xuất, không phải nội dung được vẽ lại thủ công.

### Mã nguồn solve.py

```python
#!/usr/bin/env python3
"""Shades of Truth: recover the hidden image and decode a manual transcription.

Dependency: Pillow
The ciphertext must be read from extracted.png (this script does not use OCR).
"""

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, UnidentifiedImageError


def caesar_decode(text: str, shift: int) -> str:
    """Shift ASCII letters backward; preserve digits and punctuation."""
    result = []
    for char in text:
        if "a" <= char <= "z":
            result.append(chr((ord(char) - ord("a") - shift) % 26 + ord("a")))
        elif "A" <= char <= "Z":
            result.append(chr((ord(char) - ord("A") - shift) % 26 + ord("A")))
        else:
            result.append(char)
    return "".join(result)


def extract(source: Path, output: Path) -> None:
    raw = source.read_bytes()
    with Image.open(source) as image:
        if image.format != "PNG" or image.mode != "RGB":
            raise ValueError("Expected the original RGB PNG challenge image.")
        image.load()
        charset = image.info.get("Charset")
        if not isinstance(charset, str) or len(charset) != 10:
            raise ValueError("Missing/incorrect Charset: use the original chall.png.")
        width, height = image.size
        rgb = image.tobytes()
        pixels = zip(rgb[0::3], rgb[1::3], rgb[2::3])

    # R supplies the upper two bits; G supplies the lower two bits.
    indices = bytes(((r & 3) << 2) | (g & 3) for r, g, _ in pixels)
    counts = Counter(indices)
    if max(indices) >= len(charset):
        raise ValueError("Some indices fall outside Charset; check the source file.")

    output.mkdir(parents=True, exist_ok=True)
    ascii_rows = [
        "".join(charset[value] for value in indices[y * width:(y + 1) * width])
        for y in range(height)
    ]
    (output / "hidden-ascii.txt").write_text("\n".join(ascii_rows) + "\n", encoding="utf-8")

    # Render index 0 as black and index 9 as white.
    grayscale = bytes(value * 255 // (len(charset) - 1) for value in indices)
    recovered = Image.frombytes("L", (width, height), grayscale)
    recovered.save(output / "extracted.png")

    report = [
        f"SHA-256: {hashlib.sha256(raw).hexdigest()}",
        f"File size: {len(raw)} bytes",
        f"Image: {width} x {height}, RGB",
        f"Charset: {charset!r}",
        f"Index values: {sorted(counts)}",
        f"Index counts: {dict(sorted(counts.items()))}",
        "Out-of-range indices: 0",
    ]

    # The payload in this challenge repeats every value in a 5x5 block.
    block = 5
    uniform_blocks = width % block == 0 and height % block == 0
    if uniform_blocks:
        uniform_blocks = all(
            indices[y * width + x]
            == indices[(y // block * block) * width + (x // block * block)]
            for y in range(height) for x in range(width)
        )
    if uniform_blocks:
        compact = [row[::block] for row in ascii_rows[::block]]
        (output / "hidden-ascii-compact.txt").write_text(
            "\n".join(compact) + "\n", encoding="utf-8"
        )
        report.append("Payload: uniform 5x5 blocks; compact ASCII = 180 x 50")

    report.append(f"Recovered image: {output / 'extracted.png'}")
    (output / "analysis.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Original chall.png")
    parser.add_argument("-o", "--output", type=Path, default=Path("out"))
    parser.add_argument(
        "--ciphertext", help="Text manually transcribed from extracted.png (not OCR)"
    )
    args = parser.parse_args()
    try:
        extract(args.image, args.output)
    except (OSError, UnidentifiedImageError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if args.ciphertext is None:
        print("Read extracted.png, then rerun with --ciphertext 'TEXT_FROM_IMAGE'.")
        return 0

    matches = [
        (shift, caesar_decode(args.ciphertext, shift)) for shift in range(26)
        if caesar_decode(args.ciphertext, shift).startswith("d4rk{")
    ]
    if not matches:
        print("No Caesar shift matches d4rk{. Check the transcription.", file=sys.stderr)
        return 2
    for shift, plaintext in matches:
        print(f"Manual transcription: {args.ciphertext}")
        print(f"Caesar backward shift: {shift}")
        print(f"Flag: {plaintext}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```
