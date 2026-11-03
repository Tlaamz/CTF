# Roof of Africa

**Thể loại:** Giấu tin / OSINT  **Flag:** `hiCTF{h4kun4_m4t4t4_m34ns_n0_w0rr13s}`

> Người ta nói đỉnh núi cao nhất châu Phi cất giữ những bí mật cổ xưa trong các sông băng. Một bức ảnh đã bị chặn lại, nhưng ý nghĩa thật của nó bị khóa bằng con số nổi tiếng nhất của ngọn núi. Bạn có thể lên tới đỉnh và tìm ra thứ được giấu không?

Tệp: `roof-of-africa.zip` → `roof_of_africa.jpg`

## Lời giải

1. “Đỉnh núi cao nhất châu Phi” là **núi Kilimanjaro**. “Con số nổi tiếng nhất” của núi là độ cao **5.895 m** (19.341 ft).
2. Cụm “bị khóa” trong một tệp JPEG gợi ý dùng steghide với mật khẩu. `5895` dùng được:

   ```
   steghide info roof_of_africa.jpg -p 5895
     embedded file "roof_flag_v2.txt": 38 bytes, rijndael-128 cbc, compressed
   steghide extract -sf roof_of_africa.jpg -p 5895
   → hiCTF{h4kun4_m4t4t4_m34ns_n0_w0rr13s}
   ```

(“Hakuna matata” là tiếng Swahili, phù hợp với chủ đề Tanzania/Kilimanjaro.)

## Các tệp

- `solve/solve.sh` thực hiện trích xuất bằng steghide.
- `artifacts/steghide_extracted.txt` là tệp được giấu.
- `artifacts/exiftool.txt` là metadata của ảnh.
