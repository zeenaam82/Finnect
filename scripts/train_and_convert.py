import os
import datetime
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import tf2onnx

# -----------------------------
# 환경 설정
# -----------------------------
DATA_DIR = os.path.abspath("data/mvtec_ad")
CLASS_NAME = "bottle"  # 단일 클래스 학습 예시
TRAIN_DIR = os.path.join(DATA_DIR, CLASS_NAME, "train")

IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 3  # 테스트용, 실제 학습 시 늘리기

# 모델 버전/날짜 추가
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BASE_MODEL_DIR = os.path.abspath("app/data")
os.makedirs(BASE_MODEL_DIR, exist_ok=True)

TF_MODEL_PATH = os.path.join(BASE_MODEL_DIR, f"model_tf_{timestamp}.keras")
ONNX_MODEL_PATH = os.path.join(BASE_MODEL_DIR, f"model_{timestamp}.onnx")

# -----------------------------
# 데이터 로딩
# -----------------------------
train_datagen = ImageDataGenerator(rescale=1./255)
train_generator = train_datagen.flow_from_directory(
    TRAIN_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical"
)

# -----------------------------
# TensorFlow Functional 모델 정의
# -----------------------------
num_classes = train_generator.num_classes

inputs = tf.keras.Input(shape=(224, 224, 3))
x = layers.Conv2D(32, (3,3), activation="relu")(inputs)
x = layers.MaxPooling2D(2,2)(x)
x = layers.Conv2D(64, (3,3), activation="relu")(x)
x = layers.MaxPooling2D(2,2)(x)
x = layers.Flatten()(x)
x = layers.Dense(64, activation="relu")(x)
outputs = layers.Dense(num_classes, activation="softmax")(x)

model = tf.keras.Model(inputs=inputs, outputs=outputs)
model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

# -----------------------------
# 모델 학습
# -----------------------------
print("모델 학습 시작...")
model.fit(train_generator, epochs=EPOCHS)
print("모델 학습 완료.")

# -----------------------------
# TensorFlow 모델 저장
# -----------------------------
model.save(TF_MODEL_PATH)
print(f"TensorFlow 모델 저장 완료: {TF_MODEL_PATH}")

# -----------------------------
# ONNX 변환
# -----------------------------
spec = (tf.TensorSpec((None, 224, 224, 3), tf.float32, name="input"),)
tf2onnx.convert.from_keras(model, input_signature=spec, output_path=ONNX_MODEL_PATH)

print(f"ONNX 모델 생성 완료: {ONNX_MODEL_PATH}")

# -----------------------------
# 변환 후 ONNX 출력 확인 (선택)
# -----------------------------
import onnx
onnx_model = onnx.load(ONNX_MODEL_PATH)
print("ONNX 모델 출력 노드:", [o.name for o in onnx_model.graph.output])
