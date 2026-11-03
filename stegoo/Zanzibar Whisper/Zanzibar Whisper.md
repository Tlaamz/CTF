# Zanzibar Whisper

**Thể loại:** Giấu tin  **Flag:** `hiCTF{sp1c3_1sl4nd_s3cr3ts}`

> Một bức ảnh bí ẩn từ bờ biển Zanzibar đã xuất hiện. Người địa phương nói nó mang một thông điệp ẩn — lời thì thầm từ Đảo Gia vị. Bạn có thể tìm ra bí mật của nó không?

Tệp: `zanzibar-whisper.zip` → `zanzibar_whisper.jpg`

## Lời giải

1. Dữ liệu EXIF, `strings` và `binwalk` không cho thấy điều gì đáng chú ý (xem `artifacts/exiftool.txt`).
2. Một “lời thì thầm” trong JPEG gợi ý steghide. `steghide info` với **mật khẩu rỗng** đã liệt kê được payload:

   ```
   embedded file "zanzibar_flag2.txt": size 28 bytes, encrypted rijndael-128 cbc, compressed
   ```

3. Trích xuất nó:

   ```
   steghide extract -sf zanzibar_whisper.jpg -p ""
   cat zanzibar_flag2.txt   # hiCTF{sp1c3_1sl4nd_s3cr3ts}
   ```

Dữ liệu được “mã hóa”, nhưng mật khẩu là chuỗi rỗng, nên chỉ cần thử `-p ""` trước.

## Các tệp

- `solve/solve.sh` thực hiện trích xuất bằng steghide.
- `artifacts/zanzibar_flag2.txt` là tệp ẩn được trích xuất.
- `artifacts/exiftool.txt` là metadata ảnh (không có dữ liệu ẩn ở đó).
- `challenge/` chứa ZIP ban đầu.
