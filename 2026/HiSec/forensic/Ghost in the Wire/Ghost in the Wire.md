# Ghost in the Wire

**Thể loại:** Forensics / Mạng  **Flag:** `hiCTF{1cmp_3xf1l_d3t3ct3d}`

> Nhóm giám sát mạng phát hiện lưu lượng ICMP bất thường trong một lần bắt gói thường kỳ. Có thứ gì đó đang được đưa ra ngoài qua đường truyền, nhưng dữ liệu hòa lẫn với lưu lượng bình thường. Hãy phân tích bản bắt gói và trích xuất thông điệp ẩn trước khi bóng ma biến mất.

Tệp: `ghost-in-the-wire.zip` → `ghost_traffic.pcap` (30 gói ICMP Echo Request)

## Lời giải

1. Mở bản bắt gói: trong đó chỉ có các gói ICMP Echo Request. Tất cả có cùng ICMP identifier (`4919` = `0x1337`) và cùng TTL, nên lọc riêng theo các trường này không tách được dữ liệu cần tìm.
2. Chia lưu lượng theo **cặp nguồn/đích**:

   | Luồng | Số gói | Payload |
   |---|---|---|
   | `192.168.1.100 → 10.0.0.5` | 4 | `AAAA…`, `ping from server1`, `health check ok`, `monitor alive 001` (nhiễu đánh lạc hướng) |
   | `10.13.37.1 → 10.13.37.2` | 26 | **Mỗi gói một byte**, sequence từ 1 đến 26 |

3. Sắp xếp luồng thứ hai theo ICMP sequence rồi nối các payload một byte:

   ```
   h i C T F { 1 c m p _ 3 x f 1 l _ d 3 t 3 c t 3 d }
   ```

Điểm đánh lừa là mỗi gói truyền dữ liệu trông giống một lệnh ping rất nhỏ. Luồng ẩn chỉ hiện rõ khi nhóm các gói theo hai đầu liên lạc và nhận ra rằng payload của chúng đều dài đúng một byte.

## Các tệp

- `solve/solve.py` nhóm ICMP theo luồng và tái dựng chuỗi một byte mỗi gói (cần `scapy`).
- `artifacts/icmp_packets.tsv` ghi mọi gói ICMP (nguồn, đích, ID, sequence, payload hex).
- `artifacts/solver_output.txt` là kết quả của solver.
- `challenge/` chứa tệp ZIP ban đầu.
