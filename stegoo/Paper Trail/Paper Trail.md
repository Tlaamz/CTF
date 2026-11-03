# Paper Trail

**Thể loại:** Forensics / Giấu tin (PDF)  **Flag:** `hiCTF{n3w_ar34_fOr_hid!ng_d4t4_n4m3d_TJ}`

> Tài liệu đã qua vòng duyệt cuối mà không gây nghi ngờ. Bản được nộp trông đầy đủ và không có gì khác thường. Nhưng bản lưu trữ lại kể một câu chuyện khác. Một số thay đổi không để lại dấu vết nhìn thấy. Nhiệm vụ của bạn: điều tra artifact được cung cấp và khôi phục flag.

Tệp: `paper-trail.zip` → `chall.pdf` (một bài báo học thuật đã xuất bản, 6 trang)

## Lời giải

### 1. Những điểm có vẻ sai nhưng không phải đáp án

- Metadata XMP ghi 13 trang, nhưng PDF có 6 trang.
- Có một mục `/ActualText` và một phông chữ có bảng mã `/Differences` tùy chỉnh, trong đó có `braceleft`.

Cả hai hướng đều không dẫn tới đáp án.

### 2. So sánh với bản lưu trữ gốc

Gợi ý nói “bản lưu trữ lại kể một câu chuyện khác”, nên tôi lấy bài báo gốc từ Wayback Machine và so sánh hai tệp. Phần chữ nhìn thấy **giống hệt nhau**. PDF thử thách có nhiều hơn 7 object (183 so với 176). Sau khi ghép các object theo nội dung (số object đã bị xáo lại), khác biệt thực sự duy nhất là **bốn content stream được thêm vào trang** (object 179–182).

### 3. Nội dung các stream

Mỗi stream thêm vào đều vẽ chữ ở **render mode `3 Tr` (vô hình)**, và mọi chuỗi được vẽ đều rỗng (`()`). Vì thế, trang không hiện gì; toàn bộ dữ liệu nằm trong **các số điều chỉnh khoảng cách chữ của mảng `TJ`**:

```
3 Tr ... [ 24 () 24 () 174 () 4 () 89 () 136 () ... ] TJ
```

Chính đoạn “data named TJ” trong flag chỉ về vị trí này.

- Trong 3 stream, một hàng TJ dài hơn hẳn các hàng khác và chỉ chứa giá trị từ 0–255.
- Bỏ hai số đầu của mỗi hàng dài sẽ còn 21 + 21 + 22 = **64 byte**, tương đương bốn khối AES.
- Các hàng ngắn và toàn bộ stream thứ tư là dữ liệu lấp chỗ.

### 4. Giải mã

Khóa và IV đến từ lịch sử của chính PDF, trong mảng `/ID` ở trailer:

| | Giá trị |
|---|---|
| Khóa AES-128 | `/ID[0]` = `e3b51a3ba231502d79c55593eb522037` |
| IV cho CBC | `/ID[1]` = `6749db1175e3e659a640695dcc830c82` |

Tôi tìm được khóa bằng cách thử các giá trị `/ID` từ hai bản PDF, giải ECB trên các khối 2–4 rồi tìm văn bản đọc được. IV là phần tử `/ID` còn lại. Plaintext là:

```
'CTF1' 00 28 | hiCTF{n3w_ar34_fOr_hid!ng_d4t4_n4m3d_TJ} | tag 8 byte | padding
 magic    len=40
```

## Các tệp

- `solve/solve.py` giải nén PDF bằng `mutool`, tìm các stream `3 Tr`, lấy các số TJ và giải mã bằng hai giá trị ID trong trailer.
- `artifacts/chall_decompressed.pdf` là PDF có mọi stream đã được giải nén.
- `artifacts/hidden_stream_obj179..182.txt` là bốn content stream chứa chữ vô hình được thêm vào.
- `artifacts/solver_output.txt` là kết quả của solver.
