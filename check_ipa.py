import sys
import zipfile
import struct
import array
import os

def check_ipa(ipa_path):
    print(f"[*] Đang kiểm tra: {ipa_path}")
    if not os.path.exists(ipa_path):
        print(f"[-] Lỗi: Không tìm thấy file {ipa_path}")
        return

    try:
        with zipfile.ZipFile(ipa_path, 'r') as z:
            binary_path = None
            for info in z.infolist():
                if info.filename.startswith('Payload/') and info.filename.count('/') == 2:
                    if info.filename.endswith('.app/'): continue
                    app_name = info.filename.split('/')[1]
                    bin_name = app_name.replace('.app', '')
                    if info.filename.endswith(bin_name):
                        binary_path = info.filename
                        break
            
            if not binary_path:
                print("[-] Không tìm thấy file nhị phân chính trong Payload.")
                return
            
            data = z.read(binary_path)
    except Exception as e:
        print(f"[-] Lỗi đọc archive: {e}")
        return

    print("\n[+] Kiểm tra lỗi 21008")
    err_21008 = data.count(b'\x09\x42\x8A\x52') # MOVZ W9, #0x5210
    err_21006 = data.count(b'\xC9\x41\x8A\x52') # MOVZ W9, #0x520E
    err_21000 = data.count(b'\x09\x41\x8A\x52') # MOVZ W9, #0x5208

    if err_21008 > 0:
        print(f"[-] THẤT BẠI: Lỗi 21008 vẫn còn ({err_21008} kết quả).")
    else:
        print(f"[+] ĐẠT: Đã dọn sạch 21008.")
        
    if err_21006 > 0: print(f"    -> Tìm thấy {err_21006} lần patch chuyển hướng sang 21006.")
    if err_21000 > 0: print(f"    -> Tìm thấy {err_21000} lần patch chuyển hướng sang 21000.")

    print("\n[+] Kiểm tra Premium")
    words = array.array('I', data)
    
    mask = 0xFFFFFC00
    base_3a = 0x39400000 | (0x3A << 10)
    base_39 = 0x39400000 | (0x39 << 10)
    base_3b = 0x39400000 | (0x3B << 10)
    
    c_3a = c_39 = c_3b = 0
    
    for inst in words:
        masked = inst & mask
        if masked == base_3a: c_3a += 1
        elif masked == base_39: c_39 += 1
        elif masked == base_3b: c_3b += 1

    print(f"    Số lệnh đọc isPremiumUser gốc còn lại: {c_3a} (Gốc khoảng ~196)")
    print(f"    Số lệnh đọc isFreeUser gốc còn lại:    {c_39}")
    print(f"    Số lệnh đọc experiments gốc còn lại:   {c_3b}")
    
    if c_3a == 0:
        print("[+] ĐẠT: Toàn bộ premium đã được patch.")
    elif c_3a < 20:
        print("[-] CẢNH BÁO: Premium chỉ được patch một phần.")
    else:
        print("[-] THẤT BẠI: Premium chưa được patch.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Sử dụng: python check_ipa.py <đường_dẫn_file_ipa>")
    else:
        check_ipa(sys.argv[1])
