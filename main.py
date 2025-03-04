
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = FastAPI(title="DeepSeek文本生成API")

# 挂载静态文件（用于CSS/JS等）
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 模型配置
MODEL_PATH = "/home/workspace/train_test/Models"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 加载模型和分词器
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH).to(DEVICE)

class GenerationRequest(BaseModel):
    prompt: str
    max_length: int = 150
    temperature: float = 0.7
    top_p: float = 0.9
    num_return_sequences: int = 1

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """展示交互界面"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_text(request: GenerationRequest):
    """文本生成API端点"""
    try:
        inputs = tokenizer(
            request.prompt, 
            return_tensors="pt"
        ).to(DEVICE)

        outputs = model.generate(
            inputs.input_ids,
            max_length=request.max_length,
            temperature=request.temperature,
            top_p=request.top_p,
            num_return_sequences=request.num_return_sequences,
            pad_token_id=tokenizer.eos_token_id
        )

        generated_texts = [
            tokenizer.decode(output, skip_special_tokens=True)
            for output in outputs
        ]

        return {
            "status": "success",
            "results": generated_texts,
            "parameters": request.dict()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

