import numpy as np
from io import BytesIO
from PIL import Image
from fastapi import HTTPException
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ----------------------------
# ONNX 초기화
# ----------------------------
try:
    import onnxruntime as ort
except ImportError:
    ort = None

BASE_MODEL_DIR = os.path.abspath("app/data")
ONNX_MODEL_PATH: Optional[str] = None
session = None

def initialize_onnx(model_dir: Optional[str] = None):
    global ONNX_MODEL_PATH, session
    dir_to_check = model_dir or BASE_MODEL_DIR

    if ort is None:
        logger.warning("onnxruntime 패키지 없음, 이미지 추론 비활성화")
        session = None
        return

    if not os.path.isdir(dir_to_check):
        logger.warning(f"모델 디렉토리 없음: {dir_to_check}")
        session = None
        return

    onnx_files = [f for f in os.listdir(dir_to_check) if f.endswith(".onnx")]
    if not onnx_files:
        logger.warning("ONNX 모델 파일 없음, 추론 비활성화")
        session = None
        return

    latest = max(onnx_files, key=lambda f: os.path.getctime(os.path.join(dir_to_check, f)))
    ONNX_MODEL_PATH = os.path.join(dir_to_check, latest)
    try:
        session = ort.InferenceSession(ONNX_MODEL_PATH)
        logger.info(f"사용 ONNX 모델: {ONNX_MODEL_PATH}")
    except Exception:
        logger.exception("ONNX InferenceSession 생성 실패")
        session = None

# ----------------------------
# 이미지 전처리 및 예측
# ----------------------------
def preprocess_image(file: BytesIO, target_size=(224, 224)) -> np.ndarray:
    try:
        img = Image.open(file).convert("RGB").resize(target_size)
        arr = np.array(img).astype(np.float32) / 255.0
        arr = np.expand_dims(arr, axis=0)
        return arr
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

def predict_image(file: BytesIO) -> dict:
    if session is None:
        return {"prediction": "error", "confidence": 0.0, "error": "ONNX session not initialized"}

    try:
        arr = preprocess_image(file)
        input_name = session.get_inputs()[0].name
        pred = session.run(None, {input_name: arr})[0]
        idx = int(np.argmax(pred))
        confidence = float(np.max(pred))
        label_map = {0: "normal", 1: "defect"}  # 실제 라벨 필요 시 수정
        return {"prediction": label_map.get(idx, "unknown"), "confidence": confidence}
    except Exception as e:
        return {"prediction": "error", "confidence": 0.0, "error": str(e)}