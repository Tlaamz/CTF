# The Miner That Mined The Victim

**Thể loại:** Forensics · **Sự kiện:** HI Cyber Con 2026

## Kết quả

```text
hiCTF{finally_u_proved_ur_worthiness}
```

Thử thách đưa ra 14 câu hỏi theo thứ tự; trả lời sai ba lần liên tiếp sẽ khiến tiến độ bị đặt lại. Môi trường ban đầu không thể kết nối tới phiên bài, nên người dùng đã dán các câu hỏi và đáp án được suy ra từ chứng cứ Windows được cung cấp. Bản dựng lại này giữ nguyên chuỗi đáp án đó.

## Quy trình xem xét chứng cứ

Tệp nén chứa nhật ký sự kiện Windows, lịch sử Edge, dữ liệu Prefetch, metadata hệ thống tệp và dấu vết tệp đã xóa. Cần giải nén cẩn thận: đường dẫn trong tệp nén dùng dấu gạch chéo ngược của Windows, và lần giải nén đầu gặp xung đột giữa tệp và thư mục. Hãy chuẩn hóa dấu phân cách và kiểm tra các mục trong tệp nén thay vì giả định cấu trúc thư mục Unix thông thường.

Truy vấn cơ sở dữ liệu SQLite `History` của Edge để tìm lượt tải và chuỗi chuyển hướng. Phân tích bản ghi EVTX thành các trường sự kiện có tên, thay vì chỉ đọc chuỗi văn bản đã hiển thị. Dùng các sự kiện tạo tiến trình và nạp ảnh của Sysmon để phân biệt tệp thực thi được tải về với tệp thực sự đã chạy. Đối chiếu đường dẫn và kích thước đã xóa với dấu vết hệ thống tệp hoặc thùng rác, thay vì suy luận việc xóa chỉ từ sự vắng mặt của tệp.

Chuẩn hóa thời gian sang UTC trước khi so sánh các artifact. Độ lệch múi giờ thực tế của máy nạn nhân là UTC-7, trong khi một số artifact hiển thị thời gian cách nhau bảy giờ. Sau khi chuẩn hóa, thứ tự thời gian tải, thực thi, nạp assembly và xóa là nhất quán.

## Đáp án

| # | Chứng cứ được hỏi | Đáp án |
| :--- | :--- | :--- |
| 1 | Phiên bản hệ điều hành lúc thực thi | `Microsoft Windows NT 10.0.26200.0` |
| 2 | Độ lệch UTC thực tế và bias | `UTC-7, 420` |
| 3 | Trang tải | `https://limewire.com/d/Ak55K#Yrx3FgK3du` |
| 4 | `downloadId` trong chuyển hướng | `42d377fe-8948-4a32-809f-69a51e6dbcfa` |
| 5 | Thời điểm trình duyệt tải xong | `2026-05-13 14:25:36 UTC` |
| 6 | Lần thực thi đầu tiên và số lần chạy | `2026-05-13 14:26:55 UTC, 1` |
| 7 | Assembly mật mã và thời điểm nạp | `C:\Program Files\dotnet\shared\Microsoft.NETCore.App\9.0.16\System.Security.Cryptography.dll, 2026-05-13 14:26:58 UTC` |
| 8 | Giá trị Registry | `HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\DisableAntiSpyware` |
| 9 | Mã kỹ thuật được đưa ra trong đáp án đã ghi nhận | `T1685` |
| 10 | Đoạn văn bản quan trọng trong artifact | `hiCTF{finally_u_proved_ur_worthiness}` |
| 11 | Đường dẫn gốc và thời điểm xóa thư mục | `C:\Users\milon1\Downloads\miner, 2026-05-13 14:27:47 UTC` |
| 12 | Kích thước thư mục miner đã xóa, tính bằng byte | `179623` |
| 13 | Nội dung gốc của `bar.txt` đã xóa | `I will always be there for you bro!` |
| 14 | Các byte ASCII trong mẫu ghi đè khi hủy tệp | `help` |

## Lưu ý khi diễn giải

Câu hỏi về Registry dùng cụm “sửa đổi thành công”, nhưng sự kiện Defender được xem trong lịch sử lại ghi thay đổi ở trạng thái `Ignored` và `0x1(Not Applicable)`. Đáp án nêu mục Registry được quan sát, không chứng minh Defender đã thực sự bị tắt.

Mã kỹ thuật ở trên là đáp án được cung cấp trong lần hỏi đáp đó. Ánh xạ ATT&CK có thể thay đổi, nên nó được ghi lại như dữ liệu đáp án lịch sử chứ không phải khẳng định rằng hệ phân loại luôn cố định.

Chuỗi trông như flag được tìm thấy ở câu 10. Bản ghi hội thoại hiện có không bao gồm thông báo cuối của máy chủ sau câu 14; vì vậy, bài viết phân biệt giữa việc khôi phục chứng cứ và một thông báo độc lập xác nhận phiên hỏi đáp đã được chấp nhận.
