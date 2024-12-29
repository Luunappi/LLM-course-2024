"""Model configuration and selection"""

from enum import Enum
from dataclasses import dataclass


@dataclass
class ModelConfig:
    model_id: str
    input_cost: float
    output_cost: float
    context_length: int


class ModelType(Enum):
    FAST = "fast"  # Nopeat, kevyet kyselyt (gpt-4o-mini)
    STANDARD = "standard"  # Normaalit kyselyt (o1-mini)
    ADVANCED = "advanced"  # Monimutkaiset tehtävät (o1)


MODELS = {
    ModelType.FAST: ModelConfig(
        model_id="gpt-3.5-turbo",
        input_cost=0.0015,
        output_cost=0.002,
        context_length=4096,
    ),
    ModelType.STANDARD: ModelConfig(
        model_id="gpt-4", input_cost=0.03, output_cost=0.06, context_length=8192
    ),
    ModelType.ADVANCED: ModelConfig(
        model_id="gpt-4-turbo", input_cost=0.01, output_cost=0.03, context_length=128000
    ),
}


def get_model_config(model_type: ModelType) -> ModelConfig:
    """Get model configuration"""
    return MODELS[model_type]
