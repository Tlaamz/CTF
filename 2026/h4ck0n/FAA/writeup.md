# FAA — Forensics (500 pts)

**Author:** paramveer504

**Description:**

> Many may not know that not everything is needed to make up something.

## 1. Phân tích file ban đầu

Challenge cung cấp một file `chall.zip`. Giải nén:

```bash
unzip chall.zip
cd chall-image
```

Bên trong chỉ có một ảnh JPEG dung lượng khoảng 18 MB:

```text
benjamin-chambon-WAWyV76C3t8-unsplash.jpg
```

Tiến hành kiểm tra file bằng các công cụ cơ bản:

```bash
file *.jpg
exiftool -a -u -g1 *.jpg
strings -a *.jpg | less
binwalk *.jpg
xxd -l 2048 *.jpg
stegseek --seed *.jpg
```

Khi phân tích dữ liệu được giấu trong các hệ số DCT của JPEG, phát hiện **Steghide magic `73 68 8d`**, cùng seed `0xc6adb5de`. Đây là dấu hiệu cho thấy ảnh chứa dữ liệu Steghide. Magic này nằm trong luồng bit được trích xuất, không phải ba byte liên tiếp có sẵn trong JPEG thô.

Đồng thời, khi kiểm tra các JPEG segment, ta phát hiện **7 đoạn dữ liệu bất thường** nằm ở APP0, EXIF, XMP, APP11, APP12, APP15 và phần sau marker kết thúc ảnh `FF D9`.

Các đoạn này được lưu dưới nhiều định dạng khác nhau, nên ban đầu chưa rõ chúng dùng để làm gì. Trong JPEG còn có một comment:

```text
The Three Musketeers may find the prime
```

Tạm thời ghi nhận những dữ liệu này và quyết định xử lý **Steghide trước**, vì đây là hướng có thể kiểm tra trực tiếp.

## 2. Tìm mật khẩu Steghide

Thử mật khẩu rỗng, một số từ khóa liên quan đến ảnh, địa điểm và wordlist thông dụng nhưng đều không thành công.

Quan sát lại tên file, ta thấy một đoạn định danh khá đặc biệt:

```text
WAWyV76C3t8
```

Đây là mã định danh ảnh Unsplash. Vì có thể tác giả sử dụng chính tên ảnh làm manh mối, ta thử nhiều phép biến đổi như đảo chuỗi, Base64, Base32 và Caesar Cipher.

Khi thử **ROT13**, thu được:

```bash
echo 'WAWyV76C3t8' | tr 'A-Za-z' 'N-ZA-Mn-za-m'
```

Output:

```text
JNJlI76P3g8
```

Thử chuỗi này làm mật khẩu:

```bash
steghide extract \
  -sf benjamin-chambon-WAWyV76C3t8-unsplash.jpg \
  -p 'JNJlI76P3g8'
```

Lần này Steghide trích xuất thành công một file:

```text
output.txt.xz
```

Vậy mật khẩu Steghide chính là **ROT13 của mã định danh trong tên ảnh**.

## 3. Bóc các lớp mã hóa

Kiểm tra file vừa trích xuất:

```bash
file output.txt.xz
```

Nhận diện đây là file nén XZ, tiến hành giải nén:

```bash
xz -dc output.txt.xz > output.txt
```

Nội dung `output.txt` là một chuỗi Base64 rất dài. Giải mã tiếp:

```bash
base64 -d output.txt > jsfuck.js
```

Kiểm tra file JavaScript nhận thấy toàn bộ mã chỉ sử dụng sáu ký tự:

```text
[]()+!
```

Đây là **JSFuck**, một kỹ thuật obfuscation JavaScript.

Ta sử dụng Node.js để khôi phục JavaScript bên trong. Thay vì thực thi payload, ta chặn lời gọi `eval` và ghi lại đoạn mã được truyền vào nó.

Tạo `capture.cjs`:

```javascript
const fs = require('fs');
const vm = require('vm');

const src = fs.readFileSync('jsfuck.js', 'utf8');
let count = 0;

vm.runInNewContext(src, {
    eval: code => {
        count++;
        fs.writeFileSync('hidden.js', String(code));
    }
}, {timeout: 30000});

if (count !== 1)
    throw Error('Unexpected eval count');
```

Chạy trong môi trường phân tích cô lập:

```bash
node capture.cjs
```

*Lưu ý: Node VM không phải sandbox bảo mật hoàn chỉnh, vì vậy không chạy mã không tin cậy trực tiếp trên máy chính.*

Sau khi khôi phục, ta nhận được file `hidden.js`. Mặc dù JavaScript vẫn bị obfuscate, việc phân tích code cho thấy các thành phần quan trọng:

- `cipherBytes`: mảng ciphertext dài 43 byte.
- `OPERATION_ORDERS`: bảng thứ tự các phép biến đổi.
- `decryptPayload(cipherBytes, playerKey)`: hàm giải mã.
- `process.argv[2]`: vị trí nhận khóa `playerKey`.

Đến đây đã có **ciphertext và thuật toán giải mã, nhưng chưa có `playerKey`**.

Do vậy, ta quay lại 7 đoạn dữ liệu bất thường được phát hiện ở bước đầu.

## 4. Phân tích lại 7 mảnh dữ liệu

Đọc lại đề bài:

> Many may not know that not everything is needed to make up something.

Cụm *not everything is needed* gợi ý rằng **không nhất thiết phải sử dụng tất cả các mảnh dữ liệu để khôi phục một thứ hoàn chỉnh**.

Kết hợp với comment `The Three Musketeers may find the prime` tìm thấy ngay trong JPEG, ta nghĩ đến **Shamir Secret Sharing** — thuật toán chia một bí mật thành nhiều share, trong đó chỉ cần một số lượng share nhất định để khôi phục bí mật.

Đầu tiên phải đưa 7 đoạn dữ liệu về cùng một định dạng.

| Vị trí | Cách giải mã |
|---|---|
| XMP `xmp:Label` | Base64 |
| EXIF `UserComment` | Base85 |
| APP12 | Base32 |
| APP15 | Đảo chuỗi rồi giải Hex |
| APP11 | Base36 |
| APP0 | Dữ liệu nhị phân |
| Sau JPEG EOI | ASCII85 |

Sau khi giải mã, cả 7 mảnh đều có độ dài **69 byte**, với cấu trúc:

```text
[Share ID: 1 byte]
[Y value: 66 bytes]
[Checksum: 2 bytes]
```

Kiểm tra tính toàn vẹn từng mảnh bằng SHA-256:

```python
assert len(record) == 69

assert (
    hashlib.sha256(record[:-2]).digest()[:2]
    == record[-2:]
)
```

Cả 7 checksum đều hợp lệ, các Share ID lần lượt từ `1` đến `7`.

Với mỗi mảnh, lấy:

```python
x = record[0]
y = int.from_bytes(record[1:-2], 'big')
```

Ta thu được 7 điểm `(x, y)`, phù hợp với cách biểu diễn share của Shamir Secret Sharing.

Ta chưa biết trước threshold của Shamir, tức là cần bao nhiêu share để khôi phục secret.

Sắp xếp bảy giá trị `y` theo Share ID từ 1 đến 7 và tính các hiệu hữu hạn liên tiếp:

\[
\Delta y_i=y_{i+1}-y_i
\]

\[
\Delta^2y_i=\Delta y_{i+1}-\Delta y_i
\]

\[
\Delta^3y_i=\Delta^2y_{i+1}-\Delta^2y_i
\]

Kết quả hiệu bậc ba là:

```text
[0, -M, 0, 2M]
```

Tính GCD của những hiệu khác 0:

\[
M=\gcd(|-M|,|2M|)
\]

Thu được:

\[
\boxed{M=2^{521}-1}
\]

Đây là một **số nguyên tố Mersenne**.

Khi xét theo modulo `M`, hiệu bậc hai không đổi và khác 0, trong khi toàn bộ hiệu bậc ba bằng 0. Điều này chứng minh bảy điểm nằm trên một **đa thức bậc hai trong trường hữu hạn**.

Đa thức bậc hai có dạng:

\[
f(x)=ax^2+bx+c\pmod M
\]

Nó có ba hệ số cần xác định là `a`, `b`, `c`. Vì thế cần **3 điểm có hoành độ khác nhau** để xác định đa thức và khôi phục `f(0)`.

Như vậy, **chỉ cần 3 trong 7 share**, đúng với giả thuyết ban đầu.

## 6. Nội suy Lagrange để khôi phục secret

Áp dụng nội suy Lagrange trên trường hữu hạn với mô-đun:

\[
M=2^{521}-1
\]

Secret là giá trị của đa thức tại `x = 0`:

\[
f(0)=\sum_{i=1}^{3}y_i
\prod_{j\ne i}\frac{-x_j}{x_i-x_j}\pmod M
\]

Trong phép toán modulo, phép chia được tính bằng nghịch đảo modulo.

Thực hiện nội suy với 3 share bất kỳ, sau đó thử toàn bộ:

\[
\binom{7}{3}=35
\]

Cả **35 tổ hợp** đều trả về cùng một secret:

```text
21388077551557335503598707706588121040060001228422848505354972680588693352330213
```

Lưu ý: `2^521−1` là mô-đun, còn số nguyên 80 chữ số vừa khôi phục mới là secret cần tìm.

Đến đây có thể hiểu rõ ý nghĩa câu mô tả đề bài: **không cần sử dụng tất cả 7 mảnh để khôi phục bí mật, mà chỉ cần 3 mảnh là đủ**.

## 7. Giải mã payload cuối cùng

Quay lại file `hidden.js`, sử dụng secret vừa khôi phục ở dạng chuỗi thập phân làm `playerKey` trong hàm `decryptPayload`.

Thuật toán thực hiện:

1. Hash `playerKey` bằng **FNV-1a 64-bit** để tạo seed.
2. Sử dụng **SplitMix64** và thuật toán **Fisher–Yates** để tạo S-box gồm 256 phần tử và inverse S-box.
3. Lần lượt giải mã các byte trong `cipherBytes` bằng inverse S-box, rồi đảo ngược các phép XOR, cộng modulo 256 và xoay bit theo `OPERATION_ORDERS`. Phép XOR có sử dụng byte plaintext trước đó.
4. Tách 4 byte cuối làm checksum, đối chiếu với 4 byte đầu theo little-endian của FNV-1a 64-bit tính trên plaintext.

Checksum thu được:

```text
af 81 2e 0b
```

Checksum khớp hoàn toàn, xác nhận secret và quá trình giải mã chính xác.

Plaintext cuối cùng:

```text
FLAG = "d4rk{JsFAaAaA_0bfu5c4710n_<3}"
```

## Flag

```text
d4rk{JsFAaAaA_0bfu5c4710n_<3}
```

## Tổng kết

```text
chall.zip
  └── JPEG
       ├── Phát hiện dấu hiệu Steghide
       ├── Phát hiện 7 mảnh dữ liệu lạ
       │
       ├── Thử các phép biến đổi ID ảnh
       │    └── ROT13
       │         └── Steghide
       │              └── output.txt.xz
       │                   └── XZ
       │                        └── Base64
       │                             └── JSFuck
       │                                  └── hidden.js
       │                                       └── Thiếu playerKey
       │
       └── Quay lại 7 mảnh
            └── Giải các encoding
                 └── Shamir Secret Sharing
                      └── Chứng minh threshold = 3
                           └── Nội suy Lagrange
                                └── Secret
                                     └── decryptPayload
                                          └── Checksum
                                               └── FLAG
```

Bài kết hợp **Steganography, ROT13, Compression, Base64, JavaScript Obfuscation và Shamir Secret Sharing**. Điểm mấu chốt là nhận ra hai nguồn dữ liệu trong cùng một JPEG bổ sung cho nhau: một nhánh chứa chương trình giải mã và ciphertext, nhánh còn lại chứa secret được chia thành 7 share.