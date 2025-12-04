import os
import shutil
import tempfile
import zipfile
import logging
import time
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import Callback
import tf2onnx
import s3fs
from asgiref.sync import sync_to_async

from app.core.s3_manager import s3_manager
from app.core.config import settings
from app.integrations.django_bridge import get_upload_record_model
from app.core.celery_app import celery_app
from app.core.s3_manager import S3Manager

logger = logging.getLogger(__name__)
UploadRecord = get_upload_record_model()

# =================================================================
# 학습 전용 유틸리티 함수 및 클래스
# =================================================================

def load_and_preprocess_image(path_tensor: tf.Tensor, label: tf.Tensor) -> tuple:
    # S3 경로를 받아 이미지를 로드하고 전처리하는 tf.data.Dataset map 함수
    img_raw = tf.io.read_file(path_tensor)
    img = tf.image.decode_jpeg(img_raw, channels=3)
    img = tf.image.resize(img, (224, 224)) 
    img = img / 255.0
    label = tf.one_hot(label, depth=2) 
    return img, label

def get_s3_files(s3_base_path: str, label_names: list) -> tuple:
    # S3에서 학습에 필요한 파일 경로 목록과 레이블을 가져옴
    fs = s3fs.S3FileSystem(
        anon=False, 
        key=settings.AWS_ACCESS_KEY, 
        secret=settings.AWS_SECRET_KEY # AWS 자격 증명 명시
    ) 
    all_image_paths = []
    all_image_labels = []
    
    for i, label_name in enumerate(label_names):
        # 학습 데이터가 S3에 저장된 실제 경로 구조(mvtec_ad/bottle/train/good)를 고려하여 재귀적으로 검색
        class_path_jpg = f"{s3_base_path}/{label_name}/**/*.jpg"
        class_path_png = f"{s3_base_path}/{label_name}/**/*.png"
        
        try:
            paths = fs.glob(class_path_jpg)
            paths.extend(fs.glob(class_path_png))
            
            s3_urls = [f"s3://{p}" for p in paths]
            all_image_paths.extend(s3_urls)
            all_image_labels.extend([i] * len(s3_urls))

            # 메모리 절약을 위해 샘플링 적용
            SAMPLE_SIZE = 20
            if len(all_image_paths) > SAMPLE_SIZE:
                logger.warning(f"메모리 절약을 위해 전체 {len(all_image_paths)}개 중 상위 {SAMPLE_SIZE}개 파일만 사용합니다.")
                # 무작위 샘플링 대신 앞부분 파일 사용 (재현성 확보)
                all_image_paths = all_image_paths[:SAMPLE_SIZE]
                all_image_labels = all_image_labels[:SAMPLE_SIZE]

            # logger.info(f"S3에서 레이블 '{label_name}'에 대해 {len(s3_urls)}개 파일을 찾았습니다.")
        except Exception as e:
            logger.warning(f"S3 경로 {label_name} 파일 검색 실패: {e}")
            continue

    if len(all_image_paths) == 0:
         logger.error(f"S3 베이스 경로 {s3_base_path}에서 파일을 찾을 수 없습니다.")

    return all_image_paths, all_image_labels, len(label_names)

class S3CheckpointCallback(Callback):
    # 체크포인트를 로컬에 임시 저장 후 S3에 업로드하고 즉시 로컬 파일을 삭제
    def __init__(self, s3_prefix: str):
        super().__init__()
        self.s3_prefix = s3_prefix
        self.bucket = settings.BUCKET_NAME 

    def on_epoch_end(self, epoch, logs=None):
        temp_model_path = None
        try:
            temp_model_path = os.path.join(tempfile.gettempdir(), f"ckpt_{time.time()}.h5")
            self.model.save(temp_model_path)
            
            s3_key = f"{self.s3_prefix}/epoch_{epoch+1}_{logs.get('loss', 0):.4f}.h5"
            s3_manager.upload_file(temp_model_path, self.bucket, s3_key)
            
        except Exception as e:
            logger.error(f"체크포인트 저장 중 오류 발생: {e}")
        finally:
            if temp_model_path and os.path.exists(temp_model_path):
                os.unlink(temp_model_path)


# =================================================================
# 모델 학습 태스크
# S3 스트리밍을 사용하여 모델 학습을 수행하고 결과를 ONNX로 변환 후 S3에 저장
# =================================================================

@celery_app.task(bind=True)
def trigger_training_task(self, category: str):
    temp_onnx_path = None
    local_data_dir = None
    s3_manager = S3Manager()

    try:
        # 학습 데이터 다운로드를 위한 로컬 임시 폴더 생성
        local_data_dir = tempfile.mkdtemp()
        
        # 학습 환경 정의
        EPOCHS = 3
        BATCH_SIZE = 16 #4
        LABEL_NAMES = ['good', 'defect']
        
        # S3 학습 데이터 경로, 최종 베이스 경로 정의
        MVTEC_BASE_DIR = f"{settings.S3_TRAINING_DATA_FOLDER}/mvtec_ad"
        S3_TRAIN_DIR = f"s3://{settings.BUCKET_NAME}/{MVTEC_BASE_DIR}/{category}/train"

        # S3에서 파일 경로 목록 가져오기
        all_image_paths, all_image_labels, num_classes = get_s3_files(S3_TRAIN_DIR, LABEL_NAMES)

        if not all_image_paths:
            logger.error(f"S3 경로 {S3_TRAIN_DIR}에서 파일을 찾을 수 없습니다.")
            return {"status": "failed", "reason": "No training data found"}

        logger.info(f"S3에서 총 {len(all_image_paths)}개의 학습 파일을 찾았습니다. 로컬 다운로드 시작.")

        # S3 파일들을 로컬로 다운로드 및 로컬 경로 목록 생성
        local_image_paths = []
        
        for s3_url in all_image_paths:
            s3_key = s3_url.replace(f"s3://{settings.BUCKET_NAME}/", "")
            
            relative_path = s3_key.replace(f"{MVTEC_BASE_DIR}/", "") 
            local_path = os.path.join(local_data_dir, relative_path)
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            s3_manager.download_file(s3_key, local_path)
            local_image_paths.append(local_path)

        logger.info(f"로컬 다운로드 완료. 총 {len(local_image_paths)}개. 학습 시작.")

        # Keras/TF 학습 시작 (로컬 경로 사용)
        
        # 데이터 전처리 함수 정의
        def load_and_preprocess_image(path, label):
            image = tf.io.read_file(path)
            image = tf.image.decode_image(image, channels=3, expand_animations=False) # JPG/PNG 파일 모두 처리
            image = tf.image.resize(image, [256, 256])
            image = tf.cast(image, tf.float32) / 255.0
            return image, label

        # Dataset 생성 및 구성
        train_dataset = tf.data.Dataset.from_tensor_slices((local_image_paths, all_image_labels))
        train_dataset = train_dataset.map(load_and_preprocess_image, num_parallel_calls=tf.data.AUTOTUNE) # 병렬 처리 활성화
        # train_dataset = train_dataset.map(load_and_preprocess_image) # 병렬 처리 비활성화
        train_dataset = train_dataset.shuffle(buffer_size=100).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

        # 모델 정의 및 학습
        inputs = layers.Input(shape=(256, 256, 3), name='input_image') # 입력 노드 정의 및 이름 지정
        x = layers.Conv2D(32, (3, 3), activation='relu')(inputs)
        x = layers.MaxPooling2D(pool_size=(2, 2))(x)
        x = layers.Flatten()(x)
        x = layers.Dense(128, activation='relu')(x)
        outputs = layers.Dense(num_classes, activation='softmax', name='output_class')(x) # 출력 노드 정의 및 이름 지정

        model = models.Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        model.build(input_shape=(None, 256, 256, 3))

        s3_callback = S3CheckpointCallback(s3_prefix=f"models/{category}_checkpoints")
        logger.info(f"모델 학습 시작. Category: {category}, Epochs: {EPOCHS}")
        model.fit(train_dataset, epochs=EPOCHS, callbacks=[s3_callback])
        
        # ONNX 변환 및 S3 저장 (디스크 관리)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".onnx") as tmp:
            temp_onnx_path = tmp.name
        
        input_signature = [tf.TensorSpec(shape=[1, 256, 256, 3], dtype=tf.float32, name='input_image')]

        tf2onnx.convert.from_keras(model, input_signature=input_signature, output_path=temp_onnx_path)

        final_s3_onnx_path = f"models/{category}_latest.onnx"
        s3_manager.upload_file(temp_onnx_path, settings.BUCKET_NAME, final_s3_onnx_path)
        
        logger.info(f"학습 완료 및 ONNX 모델 S3 업로드 성공. 경로: {final_s3_onnx_path}")
        return {"status": "success", "category": category, "onnx_path": final_s3_onnx_path}

    except Exception as e:
        logger.error(f"모델 학습 중 오류 발생: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60, max_retries=3)

    finally:
        if local_data_dir and os.path.exists(local_data_dir):
            shutil.rmtree(local_data_dir)
            logger.info(f"학습 데이터 로컬 임시 디렉터리 {local_data_dir} 삭제 완료.")


# =================================================================
# 데이터 전처리 태스크 (ETL)
# =================================================================

# 모델 상태를 업데이트하고 저장하는 헬퍼 함수를 정의 (동기)
def set_status_and_save_sync(record_id: int, new_status: str):
    try:
        record = UploadRecord.objects.get(pk=record_id)
        record.status = new_status
        record.save()
    except UploadRecord.DoesNotExist:
        logger.error(f"UploadRecord ID {record_id}를 찾을 수 없습니다.")

@celery_app.task(bind=True)
def process_image_dataset_task(self, s3_key: str, record_id: int, filename: str):
    temp_dir = None
    
    try:
        temp_dir = tempfile.mkdtemp()
        local_zip_path = os.path.join(temp_dir, filename)
        logger.info(f"데이터셋 처리 시작: {filename} -> 임시 경로: {temp_dir}")
        
        # S3 다운로드, 압축 해제, 재업로드
        s3_manager.download_file(s3_key, local_zip_path)
        
        unzip_path = os.path.join(temp_dir, "unzipped_data")
        os.makedirs(unzip_path, exist_ok=True)
        with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
            zip_ref.extractall(unzip_path)
            
        category_name = filename.split('.')[0] 
        final_s3_prefix = f"{settings.S3_TRAINING_DATA_FOLDER}/{category_name}" 
        
        for root, _, files in os.walk(unzip_path):
            if files:
                relative_path = os.path.relpath(root, unzip_path)
                s3_target_dir = os.path.join(final_s3_prefix, relative_path).replace("\\", "/") + "/"
                
                for f in files:
                    local_file_path = os.path.join(root, f)
                    s3_manager.upload_file(local_file_path, settings.BUCKET_NAME, s3_target_dir + f)
                    
        logger.info(f"데이터셋 재업로드 완료. 최종 S3 경로: {final_s3_prefix}")
        
        # DB 상태 업데이트 및 원본 RAW ZIP 파일 삭제
        s3_manager.delete_file(s3_key) 
        sync_to_async(set_status_and_save_sync)(record_id, "DATA_PREP_COMPLETE")
        
        # 최종 학습 작업 트리거 (파이프라인 연결)
        trigger_training_task.apply_async((category_name,)) 
        logger.info(f"데이터 전처리 완료 후, 학습 태스크 '{category_name}' 트리거 완료.")
        
        return {"status": "success", "category": category_name}

    except Exception as e:
        logger.error(f"데이터셋 처리 중 오류 발생: {e}")
        # 에러 시 상태 업데이트 및 저장
        sync_to_async(set_status_and_save_sync)(record_id, "DATA_PREP_FAILED") 
        
        raise self.retry(exc=e, countdown=60, max_retries=3)

    finally:
        # 로컬 임시 파일 삭제
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"로컬 임시 디렉터리 {temp_dir} 삭제 완료.")