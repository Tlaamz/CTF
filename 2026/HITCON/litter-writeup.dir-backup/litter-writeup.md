# HITCON CTF - litter

Flag: `hitcon{too_many_types_of_pudding}`

## Đề bài

```text
My precious pudding image got ransomed :tear: Someone help me.
```

File nhận được là `flag.png.ltr`. Đây không phải PNG trực tiếp mà là một file
được bọc bởi format `LITTER/5`, có phần header, nonce, ciphertext và tag xác
thực.

## 1. Đọc format ban đầu

Hai dòng đầu của file là:

```text
LITTER/5
https://www.youtube.com/watch?v=652tk3UnO4E
```

Sau URL có một dòng trống. Dòng trống này là một phần của header được xác thực,
không được bỏ khi parse file. Layout là:

```text
header = b"LITTER/5\\n" + url + b"\\n\\n"
nonce  = 12 bytes
body   = ciphertext
tag    = 16 bytes cuối file
```

Nonce của file này là:

```text
4bc0da6728a5cb2e9c854a52
```

URL dẫn tới clue tiếp theo trong caption của video.

## 2. Giải caption để lấy URL recovery

Video gần như chỉ có các frame đen giống nhau; phần hình pudding và các ký tự
được tạo bởi caption. Hai caption track (English và zh-TW) chứa cùng một thông
điệp.

### 2.1. Clue đầu tiên: `Think outside the box`

Trong hình pudding của caption, lấy các ký tự `0` và `1` theo thứ tự thời gian.
Có 168 bit. Chia thành từng nhóm 8 bit, đọc MSB trước sẽ được:

```text
Think outside the box
```

Thông điệp này gợi ý phải xem vị trí của caption, không chỉ xem nội dung text
hoặc timestamp.

### 2.2. Dùng JSON3 thay vì VTT

Tải caption dạng JSON3:

```sh
/mnt/d/ctftraining/tools/yt-dlp/yt-dlp \\
  --skip-download --write-subs \\
  --sub-format json3 --sub-langs en,zh-TW \\
  -o 'pudding-source.%(ext)s' \\
  'https://www.youtube.com/watch?v=652tk3UnO4E'
```

VTT làm mất hoặc làm phẳng các giá trị vị trí ngang rất lớn. JSON3 vẫn giữ
`wpWinPosId`, từ đó tra được phần tử tương ứng trong `wpWinPositions`.

Trong mỗi track có 432 event chỉ chứa `X` hoặc `O` (có thể kèm khoảng trắng
Unicode). Với mỗi event:

1. Lấy `ahHorPos` từ `wpWinPositions[event["wpWinPosId"]]`.
2. Sắp xếp event theo `ahHorPos` tăng dần.
3. Đổi `X` thành bit `1`, `O` thành bit `0`.
4. Ghép từng 8 bit theo MSB-first thành ASCII.

Các vị trí ngang là dãy đầy đủ:

```text
1000, 2000, 3000, ..., 432000
```

Kết quả của cả hai track đều giống nhau:

```text
https://litter-at-5eae141dc75753ef.chal.hitconctf.com/
```

Script tái hiện bước này:

```sh
python3 decode_captions.py pudding-source.en.json3 pudding-source.zh-TW.json3
```

Kết quả mẫu:

```text
pudding-source.en.json3: https://litter-at-5eae141dc75753ef.chal.hitconctf.com/
pudding-source.zh-TW.json3: https://litter-at-5eae141dc75753ef.chal.hitconctf.com/
```

## 3. Recovery page là mồi nhử

Trang recovery hiển thị:

```text
Case: LTR-24 / INTAKE-7C
Amount due: 0.314 LTR
Payment status: PENDING PAYMENT
Decryptor: Download link sent by email after payment
```

Hai file public download (`litter-caption-preview.mp4` và
`lyrics-zh-Hant.srt`) chỉ là bản render/lyrics của clue caption. JavaScript của
trang chỉ mở dialog trạng thái; không có endpoint thanh toán thật hay link
decryptor ẩn trong đó. Cần quay lại phân tích cryptography của `flag.png.ltr`.

## 4. Phân tích lớp mã hóa

Reverse engineering phần encrypt/decrypt cho thấy có hai lớp:

1. Một primitive giống AES-192-GCM.
2. Một byte transform riêng được áp dụng lên plaintext.

AES bị làm hỏng có chủ đích: S-box dùng S-box AES chuẩn cho input `0..0x7f`,
nhưng mọi input `0x80..0xff` đều cho ra `0`:

```python
S = AES_SBOX[:128] + [0] * 128
```

Key dùng trong lớp AES là key 24 byte sau một bước derive. Key được lưu trong
encryptor không phải trực tiếp key này; sau khi tìm được derived key có thể
đảo phép derive để lấy source key.

Lớp byte transform có dạng (với `i` là offset tuyệt đối):

```python
r = (i % 7) + 1
v = outer[i] ^ dkey[i % 24] ^ schedule[192 + (i & 15)]
plain[i] = ROR8(v, r) ^ ((0xa7 + 0x1d*i) & 0xff)
```

Do transform này XOR round-key cuối trước khi AES thực hiện AddRoundKey cuối,
hai thành phần triệt tiêu nhau. Với byte plaintext PNG đã biết, ta thu được
quan hệ:

```text
c[i] XOR ROL8(p[i] XOR ((0xa7 + 0x1d*i) & 255), i%7+1)
    = dkey[i%24] XOR S[unknown]
```

Vế `S[unknown]` chỉ có 128 giá trị có thể. Vì vậy mỗi byte PNG đã biết tạo ra
một tập ứng viên cho một byte của derived key; lấy giao các tập ứng viên ở
nhiều vị trí sẽ khôi phục được key mà không cần brute-force 192 bit.

## 5. Dùng cấu trúc PNG để khôi phục key

PNG có nhiều byte cố định và nhiều chunk lặp lại:

```text
89 50 4e 47 0d 0a 1a 0a       PNG signature
00 00 00 0d 49 48 44 52       IHDR
...                            các field IHDR
00 00 00 xx 49 44 41 54       IDAT
00 00 00 00 49 45 4e 44 ae 42 60 82   IEND
```

Script thử các kích thước chunk IDAT thông dụng (`8192`, `16384`, `32768`,
`65536`) và các vị trí IDAT hợp lệ, đồng thời ràng buộc signature, IHDR,
IDAT và IEND. Layout duy nhất thỏa mãn toàn bộ điều kiện là:

```text
first IDAT offset = 495
IDAT chunk size   = 16384
```

Derived AES-192 key khôi phục được:

```text
a5cebfb829368d1e31f8445e4d5301392083e54ed2a23a96
```

Đảo bước derive cho source key ban đầu:

```text
a37a974a901dc4e245231c13784621a3152c943e2c8947c1
```

## 6. Xác thực và giải mã

Không chấp nhận kết quả chỉ vì vài byte đầu trông giống PNG. Sau khi có key,
script phải kiểm tra tag GCM-like đầy đủ, sau đó:

1. Giải mã lớp AES.
2. Undo byte transform.
3. Parse toàn bộ PNG chunk.
4. Kiểm tra CRC của mọi chunk.
5. Giải nén IDAT bằng zlib.
6. Kiểm tra kích thước scanline và các filter byte.

Chạy:

```sh
cd /mnt/d/ctftraining/HITCON/misc/litter
python3 recover_png.py flag.png.ltr
```

Output đã xác minh:

```text
IDAT: first offset=495, chunk size=16384
Derived AES-192 key: a5cebfb829368d1e31f8445e4d5301392083e54ed2a23a96
Original source key: a37a974a901dc4e245231c13784621a3152c943e2c8947c1
Authentication tag verified: 5336b3766e2e6c0ab825cea36231809c
PNG verified: 1254x1254; 104 valid chunk CRCs
Saved: .../flag.recovered.png
```

Ảnh sau khi giải mã là PNG RGBA `1254x1254`; flag được viết ở mép dưới ảnh:

```text
hitcon{too_many_types_of_pudding}
```

## Tóm tắt đường đi

```text
flag.png.ltr
  -> đọc URL trong LITTER/5 header
  -> caption JSON3
  -> 0/1: Think outside the box
  -> X/O + ahHorPos
  -> litter-at-5eae141dc75753ef.chal.hitconctf.com
  -> quay lại cryptanalysis file LITTER
  -> known PNG bytes + broken AES S-box
  -> derived AES-192 key
  -> xác thực tag + CRC toàn bộ PNG
  -> flag
```

