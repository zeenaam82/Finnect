import os
import sys
from pathlib import Path
import django

BASE_DIR = Path(__file__).resolve().parents[1]  # Finnect/
DJANGO_ROOT = BASE_DIR / "backend"
for path in [str(DJANGO_ROOT), str(DJANGO_ROOT / "core"), str(DJANGO_ROOT / "finnect_admin")]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Django 설정 경로 지정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finnect_admin.settings")
django.setup()

from core.models import Intent

# 1. 인사/기본 대화
intents_basic = [
    {"question": "안녕", "answer": "안녕하세요! 무엇을 도와드릴까요?"},
    {"question": "고마워", "answer": "별말씀을요. 언제든 도와드리겠습니다."},
]

# 2. 파일 업로드/분석 요청
intents_file = [
    {"question": "이 파일 분석해줘", "answer": "파일이 정상적으로 업로드되었습니다. 분석을 시작합니다."},
    {"question": "이미지 업로드 했어, 결과 알려줘", "answer": "이미지 파일이 확인되었습니다. AI 모델로 분석 중입니다."},
    {"question": "데이터셋 검사해줘", "answer": "데이터셋을 불러와 검증 중입니다. 잠시만 기다려주세요."},
]

# 3. AI 분석 결과 조회
intents_result = [
    {"question": "업로드한 파일 결과 보여줘", "answer": "업로드한 파일의 분석 결과: 정상 데이터 95%, 이상 데이터 5%입니다."},
    {"question": "AI 분석 결과 알려줘", "answer": "분석이 완료되었습니다. 해당 데이터는 ‘정상’으로 분류되었습니다."},
    {"question": "내가 올린 데이터 정상인지 확인해줘", "answer": "결과 확인: 이상 없음으로 판정되었습니다."},
]

# 4. 모델 상태 확인
intents_model = [
    {"question": "모델 상태 어때?", "answer": "AI 모델이 정상적으로 로드되어 있습니다."},
    {"question": "AI 모델 지금 사용 가능해?", "answer": "네, 현재 ONNX 모델이 활성화되어 있습니다."},
    {"question": "모델 로드 됐어?", "answer": "마지막 모델이 성공적으로 로드되었습니다."},
]

# 5. 기본 도움말/안내
intents_help = [
    {"question": "무슨 기능 할 수 있어?", "answer": "저는 파일 업로드, 데이터/이미지 분석, 분석 결과 조회, 모델 상태 확인 기능을 지원합니다."},
    {"question": "너 뭐 할 줄 알아?", "answer": "파일을 분석하고 AI 모델 결과를 제공할 수 있습니다."},
    {"question": "사용 방법 알려줘", "answer": "먼저 파일을 업로드하시고, 이후 ‘분석해줘’라고 요청하시면 결과를 알려드립니다."},
]

all_intents = intents_basic + intents_file + intents_result + intents_model + intents_help

for item in all_intents:
    # 중복 방지
    obj, created = Intent.objects.get_or_create(
    keywords=item["question"], 
    defaults={"response": item["answer"], "name": item.get("name", "")}
    )
    if created:
        print(f"Intent 추가: {item['question']}")
    else:
        print(f"이미 존재: {item['question']}")

print("초기 Intent 데이터 등록 완료!")
