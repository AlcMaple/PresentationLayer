from pydantic import BaseModel, ValidationError, model_validator, field_validator

def scales_validator(min_scale: int, max_scale: int):