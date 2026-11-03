# Memory Liar

**Thể loại:** Forensics / Bộ nhớ  **Flag:** `hiCTF{dk0m_unl1nk_3pr0c3ss_l1st_cr0ss_ch3ck_7c3a9f}`

> Một máy trạm quan trọng trên mạng con quản lý tài chính bị nghi đã bị một nhóm APT xâm nhập. Nhóm phân loại sự cố cấp 1 đã chụp bộ nhớ vật lý và chạy công cụ kiểm tra tiến trình tự động. Công cụ báo mọi thứ đều sạch: tất cả tiến trình đang chạy đều có vẻ bình thường. Bạn có thể tìm ra flag không?

Tệp: `memory-liar.zip` → `memory.raw` (ảnh bộ nhớ Windows mô phỏng, 16 MB)

## Lời giải

### 1. Mồi nhử

`strings` tìm thấy ngay nội dung này:

```
Status: System integrity validated. No hidden tasks or hooks found.
Forensics Verification Token: hiCTF{th1s_1s_4_f4k3_d3c0y_fl4g_f0r_n00bs_883a1c}
```

Đây là mồi cho người chỉ dùng `grep`. Báo cáo kiểm tra nói hệ thống “sạch”, đúng điều mà tên bài cảnh báo là không đáng tin.

### 2. Tách bản ghi tiến trình (theo kiểu psscan)

Dump có các bản ghi giống EPROCESS cách nhau `0x8000` byte. Mỗi bản ghi lưu tên ảnh tiến trình tại `+0x174`, PID tại `+0xbc` và `ActiveProcessLinks` (Flink, Blink) tại `+0xc0`. Địa chỉ ảo kernel bằng `0x80000000 + offset vật lý`.

| Offset | Tên | PID | Flink | Blink |
|---|---|---|---|---|
| 0x313000 | smss.exe | 264 | → csrss | → System |
| … | csrss, wininit, services, lsass, svchost×2, explorer | | có liên kết | có liên kết |
| 0x353000 | notepad.exe | 2180 | → đầu danh sách | → explorer |
| **0x35d000** | **winxnet.exe** | **1337** | **0x8035d0c0 (chính nó)** | **0x8035d0c0 (chính nó)** |

`winxnet.exe` là tiến trình thứ 11. Cả Flink và Blink của nó đều **trỏ về chính nó**, còn Flink của notepad bỏ qua nó và trỏ đến đầu danh sách. Đây là kiểu **gỡ liên kết DKOM** điển hình: rootkit đã bỏ EPROCESS của nó khỏi danh sách tiến trình đang hoạt động có liên kết hai chiều. Công cụ đi theo danh sách (`pslist`) sẽ không thấy nó, nhưng quét pool hoặc chữ ký (`psscan`) vẫn tìm được cấu trúc. Đó là ý của cụm “đối chiếu danh sách tiến trình” trong flag.

### 3. Payload

Ngay sau tiến trình ẩn, tại `0x35f000`, có một khối dữ liệu được đánh dấu:

```
52 4f 4f 54 | 39 05 00 00 | 5d 00 00 00 | 33 00 00 00 | 35 34 1e 09 ...
  "ROOT"       pid=1337      key=0x5d      len=51        data
```

Nó nằm gần địa chỉ C2 `c2.darkshadow-apt.org:8443` và marker `OP_SHADOW_LIAR_ACTIVE`. XOR 51 byte dữ liệu với `0x5d` để lấy flag.

## Các tệp

- `solve/solve.py` tách các bản ghi tiến trình theo kiểu psscan, phát hiện tiến trình tự liên kết và giải mã khối ROOT.
- `artifacts/winxnet_eprocess_0x35d000.bin` là bản ghi tiến trình ẩn (4 KB).
- `artifacts/root_payload_0x35f000.bin` là khối ROOT, chuỗi C2 và marker.
- `artifacts/strings.txt` là bản xuất chuỗi đầy đủ kèm offset.
- `artifacts/solver_output.txt` là kết quả của solver.
