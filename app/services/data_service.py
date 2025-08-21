import tempfile
import dask.dataframe as dd
from PIL import Image
from fastapi import HTTPException
from io import BytesIO
import os
import numpy as np
from app.core.metrics import METRICS
import onnxruntime as ort

# -----------------------------
# ONNX 모델 초기화 (최신 파일 자동 선택)
# -----------------------------
BASE_MODEL_DIR = os.path.abspath("app/data")
onnx_files = [f for f in os.listdir(BASE_MODEL_DIR) if f.endswith(".onnx")]
if not onnx_files:
    raise FileNotFoundError("ONNX 모델 파일이 존재하지 않습니다.")

# 최신 생성된 ONNX 모델 선택
ONNX_MODEL_PATH = os.path.join(BASE_MODEL_DIR, max(onnx_files, key=lambda f: os.path.getctime(os.path.join(BASE_MODEL_DIR, f))))
print(f"사용할 ONNX 모델: {ONNX_MODEL_PATH}")

session = ort.InferenceSession(ONNX_MODEL_PATH)

# -----------------------------
# 이미지 전처리 및 추론
# -----------------------------
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

# -----------------------------
# CSV 통계 처리 + 최신 결과 캐싱
# -----------------------------
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
