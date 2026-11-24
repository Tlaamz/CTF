# Write-up – Dont we all love OSINT, This guy did too

### 1. GitHub Reconnaissance

The challenge provides a GitHub profile:

https://github.com/codrrr-max

Start by examining the user's public repositories and commit history.

Two repositories were found. While inspecting their commits, I noticed an unusual detail: one commit (`7582edc`) used a personal Gmail address instead of GitHub's standard `noreply` email.

The email address was:

`testing.saydo@gmail.com`

This became the first pivot point of the investigation.

### 2. Email to OpenPGP Key

Instead of stopping at the email address, I searched for it in public OpenPGP keyservers.

I used the Ubuntu Keyserver:

https://keyserver.ubuntu.com/

Searching for `testing.saydo@gmail.com` returned a matching public OpenPGP key.

The key identifier was:

`F6B4A4E01AD8FF80`

Direct lookup:

https://keyserver.ubuntu.com/pks/lookup?op=vindex&search=0xF6B4A4E01AD8FF80

The important step was not simply finding the key, but inspecting its associated identity information (User IDs).

Inside the key's identity information, I discovered a reference to a Pastebin URL:

`https://pastebin.com/q8iDMZf4`

This was the connection between the GitHub account and the next stage of the challenge.

### 3. Pastebin – First Flag Fragment

Opening the Pastebin note revealed that the flag was not there yet.

Instead, it contained another clue:

`{ƒU_`

This was the first fragment of the flag.

### 4. Finding the Second Fragment

I continued examining the target's publicly available pages.

Another message was discovered:

`0S1Nt}`

This was the remaining fragment.

### 5. Assemble the Flag

Combining the two fragments in their original order and adding the required prefix:

- First fragment: `{ƒU_`
- Second fragment: `0S1Nt}`

Final flag:

`d4rk{ƒU_0S1Nt}`

### Conclusion

The challenge follows a classic OSINT pivoting workflow:

GitHub profile → Commit history → Personal email → OpenPGP Keyserver → Key User IDs → Pastebin → Flag fragments.

The key lesson is to inspect metadata and identity information associated with publicly available accounts rather than limiting the investigation to what is immediately visible on the profile.