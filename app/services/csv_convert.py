import pandas as pd
from io import BytesIO

def convert_xlsx_to_csv(file_obj: BytesIO) -> BytesIO:
    df = pd.read_excel(file_obj)
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False, encoding="ISO-8859-1")
    csv_buffer.seek(0)
    return csv_buffer
