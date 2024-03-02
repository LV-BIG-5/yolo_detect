import json
import random
import string

def generate_serial_number(length):
    characters = string.ascii_uppercase + string.digits
    serial_number = ''.join(random.choice(characters) for _ in range(length))
    return serial_number

# 生成包含多个序列码的数组
number_of_serials = 100
serial_numbers = [generate_serial_number(8) for _ in range(number_of_serials)]

filename = "random_serial_numbers.json"
with open(filename, "w") as file:
    json.dump(serial_numbers, file)

print(f"随机生成的序列码数组已存储到 {filename}")