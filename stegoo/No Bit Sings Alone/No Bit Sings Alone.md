# No Bit Sings Alone

**Thể loại:** Giấu tin âm thanh / Mật mã  **Flag:** `hiCTF{m4th3m4t!c5_g4v3_m3_4_l0t_Of_p4!n_8d52ae513}`

> Một tệp âm thanh đáng ngờ. Chỉ thế thôi. Hay đó chính là điều nó muốn bạn nghĩ? Hãy nghe kỹ và nhìn sâu hơn.

Các tệp: `no-bit-sings-alone.zip` → `suspicious.wav` (stereo, 16 bit, 44,1 kHz, 2.635.988 frame); `hints.zip` → `hints.txt`

## Lời giải

### 1. Chữ trên spectrogram (cả hai kênh, khoảng 0,7–5 giây, 7–18 kHz)

Một khối chữ được vẽ bằng các âm sắc (`artifacts/spectrogram_text_0-5s.png`) cho thấy:

```
AES256GCM
N=99CB9C49E4C83527CE6F89D9                 ← nonce GCM 12 byte
C0=8A845BA500DE25B749F1FF63CCFF
C1=9D2D9FD8D2614E19BCA42CC7E438
C2=B31407AE896311C3AADCF9327610
C3=478444A09EF6FE3650DF7EBEC3B7
C4=1FF18CF0EB728DBFA791B7485D76
C5=7172AE8493A8715210B5                     ← 80 byte = ciphertext 64 byte + tag 16 byte
```

Thông tin này cho biết thuật toán mã hóa, nonce và ciphertext, nhưng chưa có khóa.

### 2. Các âm hướng dẫn (kênh phải, block 585–642)

58 block cuối, mỗi block 4096 mẫu (tính từ mẫu 0 và kết thúc ở block đầy đủ cuối cùng), đều chứa **một âm thuần**. Bin FFT có biên độ đỉnh `k` luôn là số lẻ (1305–1801). Các bin này là độ dài bước nhảy. Cả 58 giá trị được liệt kê trong `artifacts/tone_guide_bins.txt`.

### 3. Chọn mẫu và tính parity (kênh trái)

Hint bảo dùng bin làm bước nhảy để chọn mẫu trong kênh **còn lại**, với vị trí quay vòng trong từng block.

Với block `b` và bước `k`, lấy các LSB của mẫu kênh trái tại:

```
pos_j = b·4096 + ((j+1)·k mod 4096),   j = 0..30          (31 bit mỗi block)
```

Đọc trực tiếp các bit đó chỉ cho ra nhiễu. Chúng là một **từ mã Hamming(31,26)**, và thông điệp là **syndrome**: XOR chỉ số cột của mọi bit bằng 1. Tần số của block còn **dịch cách sắp xếp parity**, nên bit `j` ứng với cột `(j − k) mod 31 + 1`. Mỗi block cho ra một syndrome 5 bit, đọc bit cao trước.

58 block × 5 bit = 290 bit (dùng 288 bit, còn dư 2 bit).

### 4. Trường hữu hạn và NTT nghịch đảo

- Chia các bit thành **32 giá trị chín bit**. Tất cả đều ≤ 256, nên là các phần tử của **GF(257)**.
- Chúng là kết quả NTT độ dài 32 trên GF(257). Dùng **NTT nghịch đảo** (căn `136`, sau đó nhân với `32⁻¹ mod 257`) cho ra 32 giá trị đều < 256. Đây là khóa AES-256:

```
8da8dca0aa79a8a2b1e1aef181e98e63fcca7da26d49d6dbffdb461e3ecd544d
```

### 5. Giải mã

AES-256-GCM với nonce trên spectrogram xác thực và giải mã được:

```
00 32 | hiCTF{m4th3m4t!c5_g4v3_m3_4_l0t_Of_p4!n_8d52ae513} | padding
len=50
```

### Điều giúp tìm ra cách giải

Có nhiều cách sắp xếp có vẻ hợp lý (thứ tự chọn mẫu, độ lệch cột, thứ tự bit, chọn kênh nào). Bộ lọc nhanh là **"cả 32 giá trị chín bit đều ≤ 256"**. Một cấu hình sai có xác suất vượt qua điều kiện này khoảng 2⁻³². Chỉ cách sắp xếp đúng vượt qua, nên tôi biết mình đã đi đúng hướng trước cả khi thử tag GCM.

## Các tệp

- `solve/solve.py` là solver đầy đủ (bin âm → chọn LSB → syndrome Hamming → NTT nghịch đảo trên GF(257) → AES-GCM).
- `artifacts/spectrogram_text_0-5s.png` là spectrogram của khối chữ.
- `artifacts/tone_guide_bins.txt` ghi bin đỉnh cho từng block hướng dẫn.
- `artifacts/hints.txt` là gợi ý chính thức.
- `artifacts/solver_output.txt` ghi các giá trị GF(257), khóa và plaintext đã giải mã.
- `challenge/` chứa ZIP ban đầu và `hints.zip`.
