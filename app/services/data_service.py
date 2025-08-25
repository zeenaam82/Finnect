import tempfile
import dask.dataframe as dd
from PIL import Image
from fastapi import HTTPException
from io import BytesIO
import os
import logging
from typing import Optional
import numpy as np
from app.core.metrics import METRICS

# ONNX 모델 초기화 
# 최신 파일 자동 선택
logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort
except Exception:
    ort = None

BASE_MODEL_DIR = os.path.abspath("app/data")
ONNX_MODEL_PATH: Optional[str] = None
session = None

def initialize_onnx(model_dir: Optional[str] = None):
    """
    앱 시작 시 호출하여 ONNX 세션을 안전하게 초기화합니다.
    (이미지: model_dir 지정 가능, 기본은 BASE_MODEL_DIR)
    """
    global ONNX_MODEL_PATH, session
    dir_to_check = model_dir or BASE_MODEL_DIR

    if ort is None:
        logger.warning("onnxruntime 패키지를 찾을 수 없습니다. 이미지 추론 비활성화.")
        session = None
        return

    try:
        if not os.path.isdir(dir_to_check):
            logger.warning(f"모델 디렉토리가 없습니다: {dir_to_check}")
            session = None
            return

        onnx_files = [f for f in os.listdir(dir_to_check) if f.endswith(".onnx")]
        if not onnx_files:
            logger.warning("ONNX 모델 파일이 존재하지 않습니다. 추론 엔드포인트는 503을 반환합니다.")
            session = None
            return

        latest = max(onnx_files, key=lambda f: os.path.getctime(os.path.join(dir_to_check, f)))
        ONNX_MODEL_PATH = os.path.join(dir_to_check, latest)
        try:
            session = ort.InferenceSession(ONNX_MODEL_PATH)
            logger.info(f"사용할 ONNX 모델: {ONNX_MODEL_PATH}")
        except Exception:
            logger.exception("ONNX InferenceSession 생성 실패 — 추론 비활성화")
            session = None
    except Exception:
        logger.exception("ONNX 초기화 중 예기치 않은 오류")
        session = None

# 이미지 전처리 및 추론
def preprocess_image(file: BytesIO, target_size=(224, 224)) -> np.ndarray:
    """
    이미지 전처리: RGB 변환, resize, 정규화, 배치 차원 추가
    """
    try:
        image = Image.open(file).convert("RGB")
        image = image.resize(target_size)
        img_array = np.array(image).astype(np.float32) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        return img_array
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

def predict_image(file: BytesIO) -> dict:
    """
    ONNX 모델 추론
    """
    try:
        input_array = preprocess_image(file)
        input_name = session.get_inputs()[0].name
        pred = session.run(None, {input_name: input_array})[0]
        label_idx = int(np.argmax(pred))
        confidence = float(np.max(pred))
        label_map = {0: "normal", 1: "defect"}  # TODO: 실제 MVTec AD 라벨 매핑
        return {"prediction": label_map.get(label_idx, "unknown"), "confidence": confidence}
    except Exception as e:
        return {"prediction": "error", "confidence": 0.0, "error": str(e)}

# CSV 통계 처리 
# 최신 결과 캐싱
_latest_csv_stats = {}

def process_csv(file: BytesIO) -> dict:
    """
    CSV 업로드 처리 및 METRICS 계산
    """
    global _latest_csv_stats
    tmp = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp.write(file.read())
        tmp.flush()
        tmp.close()

        df = dd.read_csv(
            tmp.name,
            encoding="ISO-8859-1",
            on_bad_lines="skip",
            blocksize="16MB",
            assume_missing=True,
            dtype={"InvoiceNo": "object"}
        )

        metrics = {k: f(df) for k, f in METRICS.items()}
        keys, tasks = zip(*[(k, v) for k, v in metrics.items() if v is not None])
        results = dd.compute(*tasks)

        stats = {}
        for k, v in zip(keys, results):
            if isinstance(v, (np.integer, np.int64)):
                stats[k] = int(v)
            elif isinstance(v, (np.floating, np.float64)):
                stats[k] = float(v)
            else:
                stats[k] = v

        # 최신 CSV 결과 저장 (챗봇에서 참조 가능)
        _latest_csv_stats = stats
        return stats

    except Exception as e:
        print("Upload CSV error:", e)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if tmp:
            os.unlink(tmp.name)

def get_latest_csv_stats() -> dict:
    """
    챗봇이 호출할 최신 CSV 통계 반환
    """
    global _latest_csv_stats
    return _latest_csv_stats if _latest_csv_stats else {}
