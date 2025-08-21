import os
import sys

def main():
    """관리자용 명령어 실행"""
    # Django 설정 모듈 지정
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finnect_admin.settings")
    try:
        # Django 관리 명령어 함수 import
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django를 불러올 수 없습니다. 설치 여부와 PYTHONPATH를 확인해주세요. "
            "가상환경을 활성화하지 않았을 수도 있습니다."
        ) from exc
    # 커맨드라인 명령 실행
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
