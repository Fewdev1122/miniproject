# crc16.py
# เวอร์ชัน Pure Python สำหรับทดแทน library crc16 ที่หายไป

def crc16xmodem(data: bytes, init_crc: int = 0xFFFF) -> int:
    """
    คำนวณค่า CRC16 แบบ XMODEM (Polynomial 0x1021)
    data: ข้อมูลแบบ bytes
    init_crc: ค่าเริ่มต้น (default 0xFFFF)
    return: ค่า CRC16 เป็น int
    """
    poly = 0x1021
    crc = init_crc
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFF  # ตัดให้เหลือ 16 บิต
    return crc
