# fine-tuning to DPO

### Prerequisites
* Python 3.11+ with venv
* M-series Mac (optimoitu MPS:lle)
* Hugging Face account and token
* Gemini API key (testausta varten)

### Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
Create `.env` file with:
```
HUGGINGFACE_TOKEN=your_token_here
GEMINI_API_KEY=your_key_here  # For model comparison testing
```

### Implementation Details

The implementation consists of three main parts:

1. **Fine-tuning** (`dpo_finetuning.py`):
* Mistral-7B-Instruct-v0.3 as base model
* SFTTrainer with LoRA adapters
* float16 precision on MPS
* Training results saved in `models/finetuned/`

2. **Testing** (`compare_models.py`):
* Compares base and finetuned models
* Uses Gemini as evaluator
* Tests 5 different prompts
* Detailed logs in `models/logs/`

3. **Model Loading** (`test_model.py`):
* Loads finetuned model for inference
* Includes file validation
* Basic testing functionality

### Dataset
Uses [Anthropic's Helpful/Harmless dataset (HH-RLHF):
* Human preference data for model training
* Each example contains:
  - chosen: Better/helpful responses
  - rejected: Worse/harmful responses
* Training uses first 1000 examples

### Test Results

The finetuned model was compared against the base model using five different prompts:
* Quantum computing explanation
* AI ethics in healthcare
* Creative writing (time travel)
* Technical comparison (ML vs traditional programming)
* Problem solving (climate change)

**Results Summary:**
* Finetuned model performed better in 4/5 tests
* Strengths: Deeper analysis, better coherence
* Base model better at simple explanations
* Detailed results in `models/logs/model_comparison_*.log`

### M-series Mac Optimization
* Uses MPS (Metal Performance Shaders)
* Adjusted batch size and accumulation steps
* Basic attention implementation (flash attention not supported)
* float16 precision (bfloat16 not supported on MPS)
* Detailed logging for debugging

### References
* [Hugging Face TRL Documentation](https://huggingface.co/docs/trl/index)
* [LoRA Paper](https://arxiv.org/abs/2106.09685)
* [Anthropic HH-RLHF Dataset](https://huggingface.co/datasets/Anthropic/hh-rlhf)