# NovaVault / ECHO CTF Chain — Walkthrough (Tiếng Việt)

> **Phạm vi:** The Setup → NovaVault Investigation → Hidden In Plain Sight → Chasing Shadows → Behind The Login → WhoAmI.  
> **Lưu ý về độ tin cậy:** Các kết quả được phân loại **đã khôi phục/đã kiểm tra**, **đáp án dựng từ bằng chứng nhưng không có phản hồi submit**, hoặc **ứng viên**. Riêng khóa Notebook cuối cùng, flag Behind The Login và fragment 3 của WhoAmI không có trong transcript/chứng cứ đã nhận; không tự điền giả.

## Sơ đồ tổng thể

```text
The Setup (WAV: stereo Morse)
  └─ tVBxt → shorturl.at → RSA private key → credentials A.MEHRA
       └─ NovaVault terminal (DFIR)
            └─ TX881 → S704 → EV315 → R12 → L09 → OPS203
                 └─ Hidden In Plain Sight (image 9x9)
                      └─ FEDIVERSE → Mastodon @amehraCC704
                           └─ Chasing Shadows: Mastodon edit history → GitHub ECHO-704
                                └─ Git history → 10-number sequence
                                     └─ Behind The Login: ECHO Private Network
                                          ├─ System 01: Identity Cache
                                          ├─ System 02: Notebook
                                          └─ System 03: Device Link
                                               └─ WhoAmI: 3 fragments, fragment 3 chưa xác minh
```

---

## 1. The Setup — Stereo Morse + RSA

### 1.1. Phân tích audio

File `audio.wav` là PCM 16-bit, stereo, sample rate 22.050 Hz, thời lượng khoảng 5,86 s. Tách hai kênh thay vì nghe chung:

```python
from scipy.io import wavfile
sr, wav = wavfile.read('audio.wav')
print(sr, wav.shape)  # 22050, (129214, 2)
left, right = wav[:, 0], wav[:, 1]
```

Các xung tạo Morse:

| Thời điểm xấp xỉ | Channel | Morse | Ký tự | Quy tắc chữ hoa/thường |
|---|---|---|---|---|
| 0,00–0,36 s | Left | `-` | T | `t` |
| 0,72–1,81 s | Right | `...-` | V | `V` |
| 2,16–3,25 s | Right | `-...` | B | `B` |
| 3,61–4,93 s | Left | `-..-` | X | `x` |
| 5,29–5,66 s | Left | `-` | T | `t` |

Hai kênh riêng lẻ là Left = `TXT`, Right = `VB`. Nhưng **thứ tự phát âm toàn cục** mới là `T V B X T`. Theo quy ước bài, Left viết thường, Right viết hoa, thu được **`tVBxt`**.

### 1.2. Short link dẫn tới RSA private key

Gợi ý “The short address can lead to somewhere much longer” dẫn tới:

`https://shorturl.at/tVBxt`

Redirect đã quan sát trong quá trình giải:

`https://www.image2url.com/r2/default/files/1792782290262-cb6dabe0-3e6d-4a4e-bf23-d03d888ab133.txt`

Nội dung là một **RSA private key PEM 2048-bit**. Bản mã trong challenge được mã hóa Base64; sau khi giải Base64 ta có ciphertext RSA 256 byte. Dùng RSA OAEP với SHA-256:

```python
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

private_key = serialization.load_pem_private_key(
    open('private_key.pem', 'rb').read(), password=None
)
ciphertext = base64.b64decode('BASE64_CIPHERTEXT_FROM_CHALLENGE')
plain = private_key.decrypt(
    ciphertext,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(), label=None,
    ),
)
print(plain.decode())
```

**Flag:** `d4rk{username_a.mehraCC704_password_drower4648}`

**Credentials:** `a.mehraCC704` / `drower4648`.

> Chú ý: chuỗi Base64 gốc không có trong các attachment hiện tại, vì vậy ví dụ dùng placeholder; không đưa ra ciphertext giả.

---

## 2. NovaVault Investigation — Correlating Forensic Evidence

### 2.1. Đăng nhập

```bash
nc 4.187.169.60 4444
```

Nhập credentials từ The Setup. Đây là terminal điều tra **mô phỏng, read-only**, không phải shell Linux. Trong briefing, Kabir yêu cầu dựng đúng sáu định danh:

**Transaction → Session → Key Event → Room → Locker → Custody Operator**.

### 2.2. Xác định giao dịch có thực

```text
help
list transactions
inspect TX881
amount TX881
```

`TX881` tại `03:14:07` ngày `2026-09-12` ghi nhận INR **500.000.000** (`₹50 crore`), nguồn `NOVAVAULT-COLD`, đích `BRIDGE-7`, trạng thái `settled`, `SESSION=S704`, `EVENT REF=EV0314`, batch `LB-77-0314` và `COSIGN KID=3b2e82d3b17b`.

Các tranche (không tính cộng lại parent một lần nữa):

| ID | INR | Time | Status |
|---|---:|---|---|
| TR-01 | 125.000.000 | 03:14:02 | posted |
| TR-02 | 100.000.000 | 03:14:03 | posted |
| TR-03 | 75.000.000 | 03:14:04 | posted |
| TR-04 | 100.000.000 | 03:14:05 | posted |
| TR-05 | 100.000.000 | 03:14:07 | posted |
| **Tổng** | **500.000.000** | | |

### 2.3. Session không chứng minh người thực hiện

```text
sessions S704
inspect S704
```

Session `S704`: account `A.MEHRA`, login `03:11:42`, logout `03:18:09`, terminal `TERM-04`, IP `10.4.7.19`, gateway `VPN-GW-2`, badge `CC704`, shift `N-03`, `cached gateway ticket`, MFA `degraded`, `operator_binding=unverified`. Vì vậy **tài khoản được ghi trên session không đồng nghĩa danh tính người mở tủ**.

### 2.4. Phân biệt ledger event với access claim giả

```text
events EV0314
events EV0315
events EV0762
```

`EV0314` là transfer event từ settlement ledger, chứng minh ghi sổ, **không phải** key event dùng để nối tới phòng.

`EV0315` là gateway-cache access claim: `S704 → R12`, `RD12`, `BADGE=UNKNOWN`, `NONCE=MISSING`, `INTEGRITY=gateway-signed`, `SIGNATURE SCOPE=gateway-transport`, device counter `45346`, digest `e786fdcf91be6fa7`, device time `03:11:04`, gateway event time `03:14:08`.

Trong khi đó `EV0762` là event gốc do reader-RD12 phát ra: thời gian `03:11:04`, session `S0762`, room `R12`, badge `BD417`, `NONCE-EV0762-A`, **cùng** device counter `45346` và digest `e786fdcf91be6fa7`.

| Bằng chứng | EV0315 | EV0762 |
|---|---|---|
| Source | gateway-cache | reader-RD12 |
| Session | S704 | S0762 |
| Reader | RD12 | RD12 |
| Counter | 45346 | 45346 |
| Frame digest | `e786fdcf91be6fa7` | `e786fdcf91be6fa7` |
| Device nonce | MISSING | NONCE-EV0762-A |

**Kết luận:** observation của reader đã bị trình bày lại qua gateway, gắn với session `S704`. Bản ghi gateway được ký chỉ đảm bảo vận chuyển, không xác thực nội dung tuyên bố về người mở cửa.

Các nhánh decoy: `EV0317 → R28` và `EV0318 → R04` cũng là gateway-cache claim thiếu nonce. Không được chọn chỉ vì timestamp gần giao dịch. Các sự kiện locker `EV0309`, `EV0310` thuộc `S203`, có dữ liệu legacy incomplete/delayed; `EV8572` thực ra ghi `L2812`, dù hồ sơ `L02` tham chiếu nhầm.

### 2.5. Room → Locker bằng kiểm chứng hash

`EV0315` dẫn tới phòng `R12`, cabinet `CAB-12`. Manifest `EV59936` ghi tủ `L09` chứa hardware token có serial `HTK-8346-93`.

```python
import hashlib
print(hashlib.sha256(b'HTK-8346-93').hexdigest()[:12])
# 3b2e82d3b17b
```

12 ký tự đầu SHA-256 **trùng tuyệt đối** COSIGN KID của `TX881`. Vì vậy xác định `R12 → L09` độc lập với lời khai/cached access event.

### 2.6. Locker → Custody allocation

`EV50137` (workforce roster) ghi revision `N-03/17`: custody block `CB-12B`, custody post `OPS203`, staffed employee `EMP076`. Revision `N-03/18` ra đời/commit sau thời điểm mở tủ, không thể dùng để thay thế ngược allocation lịch sử.

`EV0774` ghi trên actuator `L09`: latch cycle `8841`, cause `SVC-BYPASS`, origin `MC-2`, `KEY SENSED=NO`. Đây là bằng chứng cơ chế bypass, **không chứng minh** chính `EMP076` tự tay mở bằng chìa khóa.

### 2.7. Chuẩn hóa ID theo SOP

Event `EV55552` (case citation standard) chỉ dẫn: sáu ID nối bằng dấu `-`; với ID sự kiện có padding số 0 phải bỏ số 0 đầu. Vì vậy **`EV0315` được ghi thành `EV315`** trong submission.

```text
submit TX881-S704-EV315-R12-L09-OPS203
```

Đây là chuỗi được dựng từ evidence của file `novavault_evidence.zip`. Transcript không chứa phản hồi chấm của lệnh submit nên không ghi thêm flag suy đoán.

---

## 3. Hidden In Plain Sight — Image Grid / Graph Tracing

**File:** `What_Was_That.png` (1620×1620, ô 9×9). Kiểm tra metadata:

```bash
exiftool What_Was_That.png
```

Trong EXIF `ImageDescription`:

> Don't Jump when their is the red, otherwise you should!  
> nothing is inside this challenge.

`Artist=d4rkc0de` là tên CLB/đơn vị tạo challenge; không tự coi đó là tên Echo.

**Cách giải:** Chia lưới 9×9 thành chín khối 3×3. Ở mỗi khối, nối các số theo thứ tự tăng dần, chỉ giữ nét nối khi hai ô kề cạnh. Khi hai ô chỉ chạm góc, **nhấc bút**, trừ khi góc đó có chấm đỏ. Hai chấm đỏ ở khối giữa giữ hai nét chéo `2 → 3 → 4`, tạo chữ **V**; chấm đỏ ở khối dưới-trái giữ nét `7 → 8`, tạo chân **R**.

Chữ đọc theo chín khối (trái→phải, trên→dưới):

```text
F E D
I V E
R S E
```

Ghép: **FEDIVERSE**.

**Flag:** `d4rk{fediverse}`.

**Liên kết sang bài sau:** Fediverse gợi ý Mastodon; tìm hồ sơ Arjun bằng username đã lấy từ The Setup.

---

## 4. Chasing Shadows — Mastodon OSINT + Git Forensics

### 4.1. Tìm nhân vật Arjun trên Mastodon

Từ `a.mehraCC704`, tra cứu trên Mastodon bằng username `amehraCC704` (không có dấu chấm):

- Profile: https://mastodon.social/@amehraCC704
- Account ID: `117500643961282073`.
- Bio: `NOVAVAULT - EMPLOYEE`.

API công khai:

```bash
curl -s 'https://mastodon.social/api/v2/search?q=amehraCC704&type=accounts' | jq
curl -s 'https://mastodon.social/api/v1/accounts/117500643961282073/statuses?limit=40' | jq
```

Một post của Arjun đã bị **chỉnh sửa nhiều lần** (`117501213333124527`). Mastodon lưu lịch sử sửa:

```bash
curl -s 'https://mastodon.social/api/v1/statuses/117501213333124527/history' | jq -r '.[].content'
```

Phiên bản cũ nhất chứa:

```text
github: ECHO-704
```

Dẫn tới https://github.com/ECHO-704 và repository https://github.com/ECHO-704/- .

### 4.2. Khôi phục những phiên bản code đã bị thay thế

Repository chỉ có một file tên đặc biệt `:).py`, nhưng có lịch sử 8 commit, trong đó có commit merge/fork. Nội dung phiên bản mới nhất chỉ in **mẫu flag**, nên phải xem các phiên bản trước.

```bash
git clone 'https://github.com/ECHO-704/-.git' echo-repo
cd echo-repo
git log --all --graph --oneline --decorate
# Dạng filename đặc biệt; git show <rev>:<path>
git show 'aba4b010::).py'
git show '63645f89::).py'
git show '8bfef516::).py'
git show '11c42ce1::).py'
git show '4b48bda8::).py'
```

Các cặp số được giấu trong nội dung file theo từng phiên bản:

| Commit | Kỹ thuật | Dữ liệu nguồn | Cặp số |
|---|---|---|---|
| `aba4b010` | XOR 41 | bytes `[27,118,26]` | `2_3` |
| `63645f89` | Base64 | `OF83` | `8_7` |
| `11c42ce1` | Mỗi chữ số trừ 1 | `22_27` | `11_16` |
| `8bfef516` | Điều kiện số học và nội dung trả về | `(5*4)-3=17` | `17_23` |
| `4b48bda8` | Hex decode | `31395F3133` | `19_13` |

Kiểm tra nhanh các mảnh:

```python
import base64
print(bytes(x ^ 41 for x in [27,118,26]).decode())  # 2_3
print(base64.b64decode('OF83').decode())         # 8_7
print(''.join(chr(ord(c)-1) if c.isdigit() else c for c in '22_27'))  # 11_16
print(bytes.fromhex('31395F3133').decode())     # 19_13
```

**Bẫy thứ tự:** `11c42ce1` thuộc nhánh/merge; commit message nói “I forget to add this one. this should come before the previous commit”. Không đọc đơn giản theo commit timestamp mới→cũ. Ghép theo logic trình tự, được:

**Flag dựng từ lịch sử Git:** `d4rk{2_3_8_7_11_16_17_23_19_13}`.

Trong transcript chưa có ảnh kết quả chấm flag này, nhưng 10 số và thứ tự được phục hồi trực tiếp từ code Git.

---

## 5. Behind The Login — Web + Device Forensics

**URL:** http://4.187.169.60:8881/

### 5.1. Login với KEY SEQUENCE (không phải mật khẩu viết liền)

Dãy 10 số của Chasing Shadows được dùng làm input form trên màn hình lưới 5×5:

```text
2,3,8,7,11,16,17,23,19,13
```

Dịch ngược JavaScript bundle `_next/static/chunks/app/page-f4b3305bcc5a7d99.js` có dòng:

```javascript
S(x.split(/[\s,]+/).filter(Boolean).map(Number))
```

Nó biến chuỗi thành **mảng số**. Nhập `2387111617231913` bị từ chối; nhập với **dấu phẩy** đăng nhập thành công theo ảnh người giải cung cấp. API phía giao diện: `POST /api/auth/pattern` với JSON `{ "pattern": [2,3,8,7,11,16,17,23,19,13] }`.

Sau đăng nhập hiện ba hệ thống:

| ID | System | Đường dẫn | Chủ đề |
|---|---|---|---|
| `c1` | IDENTITY CACHE | `/challenge5.1/` | HTTP parameter/caching discrepancy |
| `c2` | NOTEBOOK | `/challenge5.2/` | Signed claims, duplicate keys, SHA-256 length-extension |
| `c3` | DEVICE LINK | `/challenge5.3/` | Endpoint telemetry, clock skew, HID + screen reconstruction |

Mỗi hệ thống phải tìm **Authorization Key** riêng để nhập ở màn hình chính (endpoint `POST /api/challenges/{id}/verify`). Sau khi cả ba đúng, frontend gọi `POST /api/flag` với `secrets:[key_c1,key_c2,key_c3]`.

### 5.2. System 01 — Identity Cache

Landing `/challenge5.1/` cho biết:

> Three desks touch every record. Intake assigns a shelf; the edge mirror remembers that shelf. The archive clerk reads the instruction attached to the envelope.

Public reference `/records?slot=blue&view=index` và manifest `/challenge5.1/manifest` ghi:

```json
{
  "client":"archive-ui/4.7",
  "route":"/records",
  "fields":{"view":["index","audit","ledger"],"realm":["public","staff"]},
  "note":"legacy clients may repeat a field"
}
```

Hint “first label ... final instruction ...” mô tả **không đồng nhất giữa hệ thống phân loại bản ghi và phần xử lý query** (HTTP Parameter Pollution / cache-key discrepancy). Trong phiên điều tra, endpoint records đã trả `Restricted Ledger` và chuỗi:

**Authorization Key c1:** `first-label-last-folio-final-clearance-echo-7319`.

> Transcript không giữ lại chính xác toàn bộ request đã gây ra trạng thái cache đó. Không tuyên bố một URL HPP cụ thể là payload chắc chắn hoặc GET chuẩn lúc nào cũng lấy được key.

### 5.3. System 02 — Notebook

Landing `/challenge5.2/` yêu cầu một `Operator alias`, POST tới `/challenge5.2/login`. Server cấp cookie `session`, có cấu trúc:

```text
Base64(v=2;uid=...;usr=arjun;iat=...;nonce=...;scope=read;cap=0;perm=reader;fmt=claims-v2)
~
64-hex SHA256 digest
```

Khi dùng cookie hợp lệ mặc định:

```text
GET /challenge5.2/content
HTTP 403
Session accepted as a reader. The restricted notebook requires a higher permission claim.
```

Hint:

> A signed record can still tell two different stories.  
> The audit parser folds repeated claims in arrival order; the terminal value is authoritative.

Hướng kiểm tra: **SHA-256 length extension** trên dạng prefix-MAC, nối claim `scope`, `cap`, `perm` mới sau dữ liệu cũ; sự khác biệt cách parser giải nghĩa claim lặp khiến giá trị xuất hiện cuối có thể có hiệu lực. Phải kiểm tra chữ ký *và* mức quyền, không chỉ HTTP status.

Các phép thử thực tế:

- Cookie gốc: HTTP `403` (chữ ký/phiên hợp lệ, nhưng `reader`).
- Cookie bị thay đổi không hợp lệ: HTTP `303` về `/challenge5.2/login`.
- Trong khảo sát secret length 1–96, duy nhất **52 byte** cho forged cookie phản hồi `403` thay vì redirect. Đây là bằng chứng khá mạnh rằng phần SHA-256 length-extension có thể đúng với khóa 52 byte.
- **Tuy nhiên** forged cookie độ dài 52 vẫn chưa nâng quyền thành công trong log được gửi. Phép thử ban đầu nhầm `303` là thành công đã bị loại bỏ.

**Authorization Key c2:** người giải cho biết đã hoàn thành bài sau đó, nhưng không gửi value cuối / HTTP 200 để ghi vào walkthrough. Không bịa key.

### 5.4. System 03 — Device Link

Endpoint evidence công khai:

```text
/challenge5.3/api/capture
/challenge5.3/evidence/screen_trace.csv
/challenge5.3/evidence/clock_sync.csv
/challenge5.3/evidence/process_map.csv
/challenge5.3/evidence/control_map.csv
/challenge5.3/evidence/keymap.csv
/challenge5.3/evidence/field-notes.txt
```

Mục tiêu là khôi phục credential đã được nhập trên endpoint `NV-04`. Dữ liệu có **nhiễu** từ nhiều process, nhiều clock và các bản chụp màn hình có hiệu lực trong những time window khác nhau.

1. `process_map.csv`: lọc `NovaVaultClient.exe` (`pid=4242`, window `W-19`), loại `browser.exe` (`5010`) và `notes.exe` (`6112`).
2. `control_map.csv`: xác nhận ô nhập credential `C91A` (sự kiện `focus` và `blur`), loại input không liên quan.
3. Sắp xếp `capture.events` theo `seq`, không theo `rx` (arrival timestamp bị đảo thứ tự).
4. `clock_sync.csv`: chỉ dùng dòng `quality=LOCKED`, loại `HOLDOVER`. Hồi quy tuyến tính gần đúng:

   `screen_tick ≈ 1.00036578171 × device_tick + 731.52449853`

5. Với event `kind=key`, giải `scan` qua `keymap.csv`, `mods` để biết chữ hoa/thường.
6. Với event `kind=click`, chuyển `device_tick` sang thời gian màn hình rồi tìm snapshot `screen_start <= screen_tick < screen_end` trong `screen_trace.csv`. Từ snapshot lấy ký tự tại `(x,y)`.
7. Bỏ các sự kiện `noise`, chỉ ghép các ký tự từ `key` và `click` theo `seq`.

Kết quả:

**Credential và Authorization Key c3:** `clock-skew-is-part-of-the-evidence-731`.

Bằng chứng xác minh: POST tới `/challenge5.3/api/unlock` với JSON `{ "password": "clock-skew-is-part-of-the-evidence-731" }` đã trả **HTTP 200** và HTML chứa `authorization: clock-skew-is-part-of-the-evidence-731`.

### 5.5. Ghép ba hệ thống

Frontend xác minh từng key theo `id=c1,c2,c3`, sau đó gọi:

```http
POST /api/flag
Content-Type: application/json

{"secrets":["first-label-last-folio-final-clearance-echo-7319","<NOTEBOOK_KEY>","clock-skew-is-part-of-the-evidence-731"]}
```

Người giải thông báo **đã hoàn thành Behind The Login**, nhưng transcript không có `NOTEBOOK_KEY` và final flag nên không thể ghi chắc hai giá trị đó.

---

## 6. WhoAmI — Retrospective OSINT / Meta Puzzle

Mô tả yêu cầu: `d4rk{fragment1_fragment2_fragment3}`, **mỗi fragment có thể gồm nhiều từ**, ngăn cách bằng `_`. Hint từ tác giả:

- Các fragment nằm trong các **challenge trước**; không phải challenge trước nào cũng chứa fragment.
- “fragment two is a name like: full_name guess who is the echo”.
- “For fragment3 - just find another one of echo's account on real social media, who could echo be obviously following? and who could be obviously following echo?”
- Tác giả thông báo có **glitch fragment 3**, hứa bổ sung file trong mô tả.

### 6.1. Fragment 1 — ứng viên từ terminal prompt

Prompt NovaVault là:

```text
NHGUBE:NovaVault>
```

ROT13:

```python
import codecs
print(codecs.decode('NHGUBE', 'rot_13'))  # AUTHOR
```

`author` là **ứng viên fragment 1**, phù hợp với lời đề “I gave Arjun his badge ... I gave him his credentials”. Nhưng **chưa có xác nhận của hệ thống chấm** rằng đây chính xác là fragment 1.

### 6.2. Fragment 2 — danh tính của ECHO

GitHub `ECHO-704/-` có commit `11c42ce1` với author **Tarun Yadav** và tài khoản `tarunyadav-dev`:

https://github.com/ECHO-704/-/commit/11c42ce10e6166431262c66fc10d86b8996f5ea5

Trong ảnh Discord từ người giải, tác giả `Tarun Yadav` còn tự trả lời:

> it's me  
> find my insta id

Do đó **`tarun_yadav`** là ứng viên có bằng chứng mạnh cho fragment 2. Tuy nhiên, tên tác giả commit không tự nó chứng minh danh tính nhân vật nếu chưa có lời nhắc Discord; ở đây cả hai nguồn trùng khớp.

### 6.3. Fragment 3 — mạng xã hội và quan hệ follow

Hint yêu cầu tìm **một tài khoản mạng xã hội khác của Echo**, xác minh **Following + Followers**; không phải chỉ tìm tài khoản trùng nickname.

- Người giải đưa `tarunyadav_999` từ **Discord username**, không phải từ Instagram.
- Một tài khoản Instagram công khai theo URL có username tương tự và display name Tarun Yadav: `https://www.instagram.com/tarunyadav_999/`, nhưng tài khoản **private**. Chưa xác minh được có thuộc cùng người hay quan hệ follow nào.
- Các biến thể `tarun_yadav`, `tarun.yadav_`, `tarunyadav99` cũng tồn tại và trùng tên; **không thể suy định** chúng thuộc cùng người.
- `d4rkc0de` là CLB an ninh mạng của IIIT Delhi/đơn vị tổ chức challenge, không tự coi là tài khoản Echo hoặc đáp án.
- File sửa glitch fragment 3 chưa được cung cấp trong transcript.

Vì vậy **fragment 3 vẫn CHƯA XÁC MINH**. Không điền ngẫu nhiên vào flag.

### 6.4. Trạng thái flag

Ứng viên chưa xác nhận:

```text
d4rk{author_tarun_yadav_<fragment3>}
```

Đây **không phải flag hoàn chỉnh**. Chỉ hoàn tất sau khi xác minh fragment 3 từ quan hệ Following/Followers đúng tài khoản, và kiểm tra fragment 1 có đúng là `author` hay không.

---

## Tóm tắt đáp án và độ tin cậy

| Challenge | Kết quả | Trạng thái |
|---|---|---|
| The Setup | `d4rk{username_a.mehraCC704_password_drower4648}` | Đã giải RSA, credentials đăng nhập được |
| NovaVault | `submit TX881-S704-EV315-R12-L09-OPS203` | Dựng bằng evidence; thiếu phản hồi submit |
| Hidden In Plain Sight | `d4rk{fediverse}` | Đã giải lưới và hint |
| Chasing Shadows | `d4rk{2_3_8_7_11_16_17_23_19_13}` | Khôi phục từ các Git commit; chưa có phản hồi chấm |
| Behind The Login / c1 | `first-label-last-folio-final-clearance-echo-7319` | Đã thấy trên trang trả về |
| Behind The Login / c2 | Chưa có key cuối trong transcript | Có bằng chứng MAC length extension, chưa ghi final |
| Behind The Login / c3 | `clock-skew-is-part-of-the-evidence-731` | Được server xác nhận HTTP 200 |
| Behind The Login / Final | Người giải báo đã xong, chưa cung cấp flag | Chưa thể ghi chính xác |
| WhoAmI | `author` (ứng viên), `tarun_yadav` (ứng viên mạnh), fragment 3 chưa xác minh | Chưa hoàn tất |

## Bài học rút ra

1. **OSINT không dừng ở bài đăng đang hiển thị:** cần xem edit history và Git commit history, kể cả merge/fork.
2. **Chữ ký hợp lệ không đồng nghĩa sự thật của phát biểu:** signed gateway transport không xác thực nhân thân người xuất hiện trong claim.
3. **Tính toàn vẹn phải đi kèm kiểm tra quan hệ tham chiếu:** hash token → COSIGN KID, frame digest/counter giữa reader và gateway; event trỏ nhầm locker vẫn có thể đúng byte.
4. **Truy vết thời gian đúng miền clock:** ingest, device, screen và commit là những khái niệm khác nhau.
5. **Phân biệt chứng minh và đoán:** đặc biệt đối với WhoAmI fragment 3 chưa có evidence follow graph.

*Walkthrough được biên soạn từ audio/PNG/ZIP evidence và transcript quá trình giải, không điền các đáp án chưa được cung cấp hoặc xác nhận.*
