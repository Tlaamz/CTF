# Paper — CTF Write-up

**Category:** Forensics / Steganography  
**Artifact:** `paper.pdf`  
**Flag format:** `d4rk{...}`  
**Flag đọc trực tiếp từ dữ liệu:** `d4rk{1t5_n0t_r8b?}` *(chưa xác nhận bằng submit)*

> **Description:** “Old tongues call picture a thousand words, Verily this scroll hath few words, yet it groaneth like a cart of stones”.

## 1. Nhận diện hướng giải

Đề nhấn mạnh hai chi tiết: tài liệu **ít chữ**, nhưng **nặng bất thường**. Vì vậy, trước hết phải phân tích cấu trúc PDF thay vì tìm acrostic hoặc giải mã tất cả đoạn văn cổ.

Chạy trên Kali Linux:

```bash
file paper.pdf
ls -lh paper.pdf
pdfinfo paper.pdf | grep -E 'Pages:|File size:|Producer:'
pdffonts paper.pdf
```

Kết quả:

- `paper.pdf` là PDF 1.4 với **5 trang**.
- Dung lượng thật: **122.413.927 byte** (~116,7 MiB).
- Được tạo bằng **ReportLab**.
- Chỉ có hai font: Helvetica và font TrueType nhúng `AAAAAA+IM_FELL_English_Roman`.

Các trang chứa một bài luận dài về kỹ thuật giấu thông tin, lẫn nhiều gợi ý giả. Vì PDF không có ảnh nhúng thông thường hay file attachment, font nhúng là đối tượng đáng kiểm tra.

## 2. Kiểm tra các object PDF

Dùng PyMuPDF (`fitz`) để liệt kê stream:

```python
import fitz
pdf = fitz.open('paper.pdf')
for i in range(1, pdf.xref_length()):
    try:
        print(i, len(pdf.xref_stream_raw(i)))
    except Exception:
        pass
```

Object **19 0** là `/FontFile2` của font TrueType, với stream dài **122.400.820 byte**. Đây chính là lý do tài liệu nặng.

Từ trang đầu tiên, `pdf[0].get_fonts(full=True)` cho biết font TrueType ở **xref 16**; `pdf.extract_font(16)[3]` trả về dữ liệu TTF đã được giải nén khỏi PDF.

Phân tích thư mục bảng của TrueType (mỗi entry dài 16 byte) cho thấy bảng lạ:

```text
Tag     Offset     Length
GSUX     59844      122323820
```

`GSUX` không phải bảng TrueType chuẩn; nội dung bất thường này nhiều khả năng là nơi tác giả giấu payload.

## 3. Phát hiện phép ROT-3 trên từng byte

Phần cuối PDF còn có **4 byte sau `%%EOF`**:

```bash
tail -c 4 paper.pdf
# urw3
```

Dịch Caesar −3 cho phần chữ cái của `urw3` nhận được `rot3`. Đây là chỉ dẫn giải mã.

6 byte đầu tiên của bảng `GSUX`:

```text
00 3a 7d 5b 5d 03
```

Trừ **3 cho mỗi byte** theo modulo 256:

```text
fd 37 7a 58 5a 00
```

Đây là **magic header của luồng nén XZ** (`FD 37 7A 58 5A 00`), xác nhận phép biến đổi vừa tìm được.

Đoạn code cốt lõi:

```python
lookup = bytes.maketrans(
    bytes(range(256)),
    bytes((n - 3) % 256 for n in range(256))
)
restored = encoded_chunk.translate(lookup)
```

Lưu ý: đây là **ROT-3 trên byte**, không phải chỉ Caesar đối với ký tự A–Z. Script `solve_paper.py` xử lý luồng nén theo từng khối 2 MiB để không cần giữ toàn bộ dữ liệu giải nén trong RAM.

## 4. Giải nén XZ và phân tích FITS

Sau khi đảo ROT-3, dùng `lzma.LZMADecompressor` giải nén luồng XZ, thu được file `hidden.fits` dài **614.520.000 byte** (~586 MiB).

**FITS** (*Flexible Image Transport System*) thường dùng để lưu ảnh và dữ liệu thiên văn. File có bốn HDU:

| HDU | Tên | Nội dung |
|---|---|---|
| 0 | PRIMARY | Header với `OBJECT='Lighthouse Nebula'` |
| 1 | `PREVIEW` | Ma trận float32 **1024 × 256** |
| 2 | `SCI` | Ma trận float32 **16512 × 9288** |
| 3 | `LOG` | Bảng 4 dòng, có `calibrate: skipped` |

Header của HDU `SCI` ghi rõ:

```text
BITPIX  = -32
NAXIS1  = 16512
NAXIS2  = 9288
EXTNAME = 'SCI'
BAYERPAT= 'GRBG'
ROWORDER= 'TOP-DOWN'
```

Ngoài ra còn có một dòng `COMMENT` chứa Base64:

```text
ZDRya3tuMWMzX3RyeV9idXRfbjB9
```

Giải mã ra `d4rk{n1c3_try_but_n0}`: đây là **flag giả** (“nice try but no”), không phải đáp án cần nộp. Không nên dừng ở text và metadata.

## 5. Tách Bayer GRBG và lọc nền

Vì HDU `SCI` là dữ liệu **Bayer GRBG**, không phải một ảnh RGB bình thường, mẫu mỗi ô 2×2 là:

```text
G R
B G
```

Cần tách các vị trí đúng kênh. Cụ thể, kênh xanh lá ở góc trên trái là `SCI[0::2, 0::2]`.

Dùng NumPy memory mapping để đọc ảnh rất lớn mà không tải hết vào RAM:

```python
import numpy as np

sci = np.memmap(
    'hidden.fits', dtype='>f4', mode='r',
    offset=1059840, shape=(9288, 16512)
)
green = sci[0::2, 0::2]   # 4644 x 8256
```

Quan sát phân bố giá trị ở kênh này nhận thấy phần lớn pixel chỉ thuộc **13 mức nền** theo công thức:

\[
v_k = (1.02+0.03k)^3,\quad k=0,\ldots,12.
\]

Giữ lại những pixel **không nằm trong palette 13 mức**:

```python
levels = (1.02 + 0.03 * np.arange(13)) ** 3
mask = np.ones(green.shape, dtype=bool)
for level in levels:
    mask &= ~np.isclose(green, level, atol=1e-5, rtol=0)
```

Có **33.487** pixel khác nền trên toàn kênh G, gồm nhiễu thưa và một vùng có mật độ điểm bất thường cao. Khi chia ảnh thành các ô 128×128, ô nổi bật nhất nằm tại gần **x=6272, y=2944** (tọa độ của kênh G đã tách), có **983** điểm khác palette.

Cắt vùng này, chọn các hàng/cột có nhiều điểm bất thường, nhị phân hóa và phóng to 3 lần theo phương pháp *nearest-neighbor* sẽ thấy chữ rõ ràng. Bounding box ảnh kết quả nằm quanh:

```text
G-channel x = 6104..6430
G-channel y = 2997..3045
```

![Flag khôi phục từ kênh G của ảnh SCI](flag_recovered.png)

## 6. Kết quả

Vùng ảnh được khôi phục hiển thị:

```text
d4rk{1t5_n0t_r8b?}
```

Đây là **chuỗi flag được xác minh bằng trích xuất trực tiếp từ pixel**, khác với mồi nhử trong FITS metadata. Tuy nhiên, do không truy cập trang CTF và không submit, mình **chưa xác minh máy chấm chấp nhận chuỗi này**.

## 7. Tái hiện toàn bộ bằng một script

Script đi kèm tự động đọc font, tìm bảng GSUX, giải mã ROT−3, giải nén XZ, xác định HDU SCI và tạo hình flag. Không cần vào website CTF.

```bash
sudo apt update
sudo apt install -y python3 python3-venv poppler-utils
python3 -m venv .venv
source .venv/bin/activate
pip install pymupdf numpy pillow
python3 solve_paper.py paper.pdf
```

Sau khi chạy, kết quả nằm trong:

```text
paper_output/
├── hidden.fits          # file trung gian khoảng 586 MiB
└── flag_recovered.png   # ảnh chứa chuỗi flag
```

**Tóm tắt chain:** PDF nặng bất thường → FontFile2 → bảng TTF `GSUX` → `urw3` ở EOF → ROT−3 từng byte → XZ → FITS → SCI/Bayer GRBG → G0 → loại 13 mức nền → ảnh flag.
