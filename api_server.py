import os
import sys
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# 🔹 إضافة مسار الملف الحالي حتى يقدر يلاقي hawsa_core.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from hawsa_core import HawsaCore   # ✅ هذا الكلاس الصحيح

app = FastAPI(
    title="Hawsa AI Local API",
    version="1.0.0",
    description="Local API for Hawsa AI Core"
)

core = HawsaCore()  # ✅ إنشاء النواة

class AIRequest(BaseModel):
    user_id: str
    message: str

@app.post("/analyze")
def analyze(req: AIRequest):
    result = core.process_comprehensive_query(
        user_id=req.user_id,
        user_message=req.message
    )
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
