# Whispers in the Margin

**Thể loại:** Giấu tin  **Flag:** `hiCTF{573g4n0gr4phy_!5_fun}`

> Đôi khi những chi tiết quan trọng nhất ở ngay trước mắt, ẩn tại chỗ không ai nghĩ tới. Hãy xem kỹ các tài liệu được cung cấp — thứ trông có vẻ trống rỗng có thể là chìa khóa mở ra bí mật cuối cùng.

Các tệp: `whispers-in-the-margin.zip` → `chall/chall.jpg`, `chall/Those numbers are process counts.docx`

## Lời giải

### Lớp 1: Giấu tin bằng khoảng trắng trong tài liệu Word

Văn bản nhìn thấy trong `.docx` là một câu trả lời trò chuyện vô hại về số tiến trình của trình duyệt (`artifacts/docx_visible_text.txt`). Sau phần đó, tài liệu có một loạt đoạn văn **trông như rỗng**, nhưng chỉ chứa dấu cách và tab (“thứ trông có vẻ trống rỗng có thể là chìa khóa”).

Trong `word/document.xml`, mỗi đoạn văn như vậy kết thúc bằng 8 ký tự khoảng trắng. Đọc chúng thành bit, với **dấu cách = 0** và **tab (`<w:tab/>`) = 1**. Mỗi đoạn văn cho một byte ASCII:

```
haha! u got me, now what?
```

Chuỗi này giống một lời trêu chọc, nhưng chính là mật khẩu cho lớp tiếp theo.

### Lớp 2: Steghide trong ảnh JPEG

`chall.jpg` không mở được bằng steghide với mật khẩu rỗng. Chuỗi vừa giải mã lại dùng được:

```
steghide extract -sf chall.jpg -p "haha! u got me, now what?"
→ hiCTF{573g4n0gr4phy_!5_fun}
```

## Các tệp

- `solve/docx_whitespace.py` giải các bit dấu cách/tab từ DOCX.
- `solve/solve.sh` chạy cả chuỗi (DOCX → mật khẩu → steghide).
- `artifacts/document.xml` là XML gốc của tài liệu (các đoạn văn chứa khoảng trắng ở cuối).
- `artifacts/docx_visible_text.txt` là văn bản mồi nhử nhìn thấy được.
- `artifacts/steghide_extracted.txt` là tệp chứa flag được trích xuất.
