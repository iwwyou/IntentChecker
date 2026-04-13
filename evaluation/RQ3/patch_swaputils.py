import re
import sys

path = "C:/Users/isjeon/PycharmProjects/pythonProject/SolidityGuardian/evaluation/RQ3/workdir_numscout_patched/run_Swap/Swap_patched.sol"
with open(path, encoding='utf-8', newline='') as f:
    text = f.read()

def mask_comments(s):
    """Replace comment characters with spaces (preserving offsets)."""
    out = list(s)
    i = 0
    n = len(s)
    while i < n:
        if i + 1 < n and s[i] == '/' and s[i+1] == '/':
            # Line comment: replace until end of line
            j = i
            while j < n and s[j] != '\n':
                out[j] = ' '
                j += 1
            i = j
        elif i + 1 < n and s[i] == '/' and s[i+1] == '*':
            # Block comment: replace until */
            j = i
            out[j] = ' '; out[j+1] = ' '
            j += 2
            while j + 1 < n and not (s[j] == '*' and s[j+1] == '/'):
                if s[j] != '\n':
                    out[j] = ' '
                j += 1
            if j + 1 < n:
                out[j] = ' '; out[j+1] = ' '
                j += 2
            i = j
        elif s[i] == '"':
            # String literal
            out[i] = ' '
            j = i + 1
            while j < n and s[j] != '"':
                if s[j] == '\\' and j + 1 < n:
                    out[j] = ' '; out[j+1] = ' '
                    j += 2
                    continue
                if s[j] != '\n':
                    out[j] = ' '
                j += 1
            if j < n:
                out[j] = ' '
                j += 1
            i = j
        else:
            i += 1
    return "".join(out)

def transform_block(b):
    masked = mask_comments(b)
    pattern = re.compile(r'\bfunction\s+\w+', re.MULTILINE)
    last = 0
    pieces = []
    for m in pattern.finditer(masked):
        j = m.end()
        depth = 0
        while j < len(masked):
            ch = masked[j]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif depth == 0 and ch in '{;':
                break
            j += 1
        sig_end = j
        # Apply replacement to ORIGINAL text in this range, not the masked version
        sig = b[m.start():sig_end]
        new_sig = re.sub(r'\bpublic\b', 'internal', sig)
        new_sig = re.sub(r'\bexternal\b', 'internal', new_sig)
        pieces.append(b[last:m.start()])
        pieces.append(new_sig)
        last = sig_end
    pieces.append(b[last:])
    return "".join(pieces)

def find_block_end(s, start):
    i = s.find('{', start)
    if i == -1: return -1
    depth = 1
    i += 1
    while i < len(s) and depth > 0:
        if s[i] == '{': depth += 1
        elif s[i] == '}': depth -= 1
        i += 1
    return i

def patch_library(text, lib_name):
    m = re.search(r'^library\s+' + lib_name + r'\b', text, re.MULTILINE)
    if not m:
        print(f"  {lib_name}: not found")
        return text
    start = m.start()
    end = find_block_end(text, start)
    block = text[start:end]
    new_block = transform_block(block)
    pub_before = len(re.findall(r'\bfunction\s+\w+[^;{]*?\bpublic\b', block, re.DOTALL))
    ext_before = len(re.findall(r'\bfunction\s+\w+[^;{]*?\bexternal\b', block, re.DOTALL))
    pub_after = len(re.findall(r'\bfunction\s+\w+[^;{]*?\bpublic\b', new_block, re.DOTALL))
    ext_after = len(re.findall(r'\bfunction\s+\w+[^;{]*?\bexternal\b', new_block, re.DOTALL))
    print(f"  {lib_name}: pub {pub_before}->{pub_after}, ext {ext_before}->{ext_after}")
    return text[:start] + new_block + text[end:]

for lib in ["SwapUtils", "MathUtils", "SafeMath", "SafeERC20", "Address", "console"]:
    text = patch_library(text, lib)

with open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(text)
print("written")
