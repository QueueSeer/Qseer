# For VSCode
สร้าง Python Virtual Environment
```
F1 -> Python: Create Environment -> Venv -> Python 3.10+
```

เลือก Python Interpreter
```
F1 -> Python: Select Interpreter -> Python venv
```

สร้าง Terminal ใหม่
```
Terminal -> New Terminal
```

ตรวจสอบว่ากำลังใช้ venv
```
pip -V
```

ติดตั้ง library
```
pip install -r requirements.txt
```

Run server
```
fastapi dev app
```

# For Command-line
สร้าง Python Virtual Environment
```
python -m venv ./.venv
```

สำหรับ Windows เปลี่ยน ExecutionPolicy เป็น RemoteSigned เพื่อให้สามารถใช้งาน scripts ได้
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Activate venv
```
.\.venv\Scripts\activate
```

ตรวจสอบว่ากำลังใช้ venv
```
pip -V
```

หากต้องการออกจาก venv
```
deactivate
```

ติดตั้ง library
```
pip install -r requirements.txt
```

Run server
```
fastapi dev app
```