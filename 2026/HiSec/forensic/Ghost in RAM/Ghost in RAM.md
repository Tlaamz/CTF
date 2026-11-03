# Ghost in RAM

**Thể loại:** Forensics · **Sự kiện:** HI Cyber Con 2026

## Kết quả

```text
hiCTF{gh0st_pr0c3ss_rng_pwn3d}
```

## Khảo sát ảnh bộ nhớ

Tệp `ghost-in-ram.zip` được cung cấp có SHA-256 là `5d93dd23e89876a4d7caead1dca17121ae36a17a29941a6c0bd75fccf13f020e` và chứa `mem.elf`, một ảnh RAM Linux dài 2.164.394.051 byte. Máy đã bị xóa dữ liệu, nên các dấu vết còn lại trong bộ nhớ là nguồn chứng cứ.

Bắt đầu bằng cách lấy các chuỗi kèm offset và tìm kiếm cấu trúc:

```bash
strings -a -t x -n 6 mem.elf > strings.txt
```

Có một số chuỗi trông như flag nhưng là mồi nhử, gồm `hiCTF{d3bug_m3}` và `hiCTF{stop_here}`. Một chuỗi mồi nhử thậm chí còn bảo người phân tích dừng lại. Những byte đó là dữ liệu cần điều tra, không phải chỉ dẫn đáng tin hay bằng chứng về đáp án.

## Tìm máy ảo tùy biến

Tìm `GVM1` cho ra hai lần xuất hiện. Header có cấu trúc thực sự nằm tại offset tệp `0x21d4038`; lần xuất hiện còn lại tại `0x7fc42131` nằm bên trong mã máy. Header có ý nghĩa được giải ra như sau:

| Trường | Giá trị quan sát được |
| :--- | :--- |
| Seed RNG | `0x6f2e1a53` |
| Offset bytecode | `0x80` |
| Độ dài bytecode | `0x5b` |
| Offset buffer nguồn | `0x180` |
| Offset buffer đích | `0x1c0` |
| Độ dài dữ liệu | `0x1e` (30 byte) |

Có thể tách mã interpreter từ offset tệp `0x21d3838` rồi dịch ngược dưới dạng x86-64. Các handler của nó thao tác với thanh ghi, nạp byte từ buffer, thực hiện phép toán số học và XOR, đồng thời triển khai bộ sinh số đồng dư tuyến tính 32 bit.

## Khôi phục buffer còn sót lại

Điểm điều chỉnh then chốt khi giải bài là chọn buffer đích. Buffer nguồn đã bị xóa, còn buffer đầu ra của máy ảo vẫn tồn tại. Đọc buffer nguồn đã bị xóa sẽ đưa dữ liệu sai vào phép đảo, dù header và seed RNG đều đúng.

Tái dựng chính xác bộ sinh số của interpreter, giữ đúng phép tràn 32 bit và cách chọn byte. Cho bộ sinh chạy thêm một bước với mỗi byte rồi đảo phép XOR với vùng buffer đích còn sót lại. Kết quả là flag 30 byte ở trên.

Script được ghi lại trước đây in ra:

```text
header: 0x6f2e1a53 0x80 0x5b 0x180 0x1c0 0x1e
hiCTF{gh0st_pr0c3ss_rng_pwn3d}
```

## Giới hạn chứng cứ

Bài viết này dựng lại cách giải đã được ghi nhận. Script giải độc lập ban đầu không còn trong không gian làm việc này, nên không được đính kèm hoặc trình bày như thể vừa chạy lại. Kết quả khôi phục được ghi nhận đến từ việc phân tích máy ảo và đảo phép biến đổi trên buffer của nó, chứ không phải chọn một chuỗi trông như flag trong bản xuất `strings`.
