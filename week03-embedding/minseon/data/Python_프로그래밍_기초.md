# Python 프로그래밍 기초

## Python이란?

Python은 간결하고 읽기 쉬운 문법을 가진 프로그래밍 언어입니다. 데이터 과학, 웹 개발, 자동화, AI/ML 등 다양한 분야에서 널리 사용됩니다.

## 기본 문법

### 변수와 자료형

```python
# 정수
age = 25

# 실수
pi = 3.14

# 문자열
name = "홍길동"

# 불리언
is_student = True

# 리스트
fruits = ["사과", "바나나", "딸기"]

# 딕셔너리
person = {"name": "홍길동", "age": 25}
```

### 조건문

```python
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"
```

### 반복문

```python
# for 반복문
for i in range(5):
    print(i)

# while 반복문
count = 0
while count < 3:
    print(count)
    count += 1
```

### 함수

```python
def greet(name, greeting="안녕하세요"):
    return f"{greeting}, {name}님!"

result = greet("홍길동")
print(result)  # 안녕하세요, 홍길동님!
```

## 주요 라이브러리

### NumPy
수치 계산을 위한 라이브러리입니다. 다차원 배열 연산에 최적화되어 있습니다.

```python
import numpy as np

arr = np.array([1, 2, 3, 4, 5])
print(arr.mean())  # 3.0
print(arr.sum())   # 15
```

### Pandas
데이터 분석을 위한 라이브러리입니다. DataFrame으로 테이블 형식 데이터를 쉽게 다룰 수 있습니다.

```python
import pandas as pd

df = pd.DataFrame({
    "이름": ["홍길동", "김철수"],
    "나이": [25, 30],
    "점수": [85, 92]
})
print(df.describe())
```

### FastAPI
Python으로 고성능 REST API를 만드는 프레임워크입니다.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def hello(name: str = "world"):
    return {"message": f"Hello, {name}!"}
```

## 가상환경과 패키지 관리

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Windows)
venv\Scripts\activate

# 패키지 설치
pip install numpy pandas fastapi

# 설치된 패키지 목록 저장
pip freeze > requirements.txt

# requirements.txt로 설치
pip install -r requirements.txt
```

## 파일 입출력

```python
# 파일 쓰기
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("Hello, Python!")

# 파일 읽기
with open("output.txt", "r", encoding="utf-8") as f:
    content = f.read()
    print(content)
```

## 객체지향 프로그래밍(OOP)

```python
class Animal:
    def __init__(self, name, sound):
        self.name = name
        self.sound = sound

    def speak(self):
        return f"{self.name}가 {self.sound} 소리를 냅니다"

class Dog(Animal):
    def __init__(self, name):
        super().__init__(name, "멍멍")

    def fetch(self):
        return f"{self.name}가 공을 가져옵니다"

dog = Dog("바둑이")
print(dog.speak())   # 바둑이가 멍멍 소리를 냅니다
print(dog.fetch())   # 바둑이가 공을 가져옵니다
```
