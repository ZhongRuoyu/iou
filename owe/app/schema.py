from typing import Annotated, Any, TypeVar

from pydantic import (
  BaseModel,
  Field,
  StrictBool,
  StrictInt,
  StrictStr,
  ValidationError,
)

from owe.record import RecordType

ModelT = TypeVar("ModelT", bound=BaseModel)


class AddRecordsRequest(BaseModel):
  """Typed request for creating one aggregated record."""

  type: RecordType
  lender: StrictStr
  borrowers: Annotated[list[StrictStr], Field(min_length=1)]
  amount: Annotated[StrictInt, Field(gt=0)]
  remarks: StrictStr | None


class SetRecordsActiveRequest(BaseModel):
  """Typed request for batch record-status updates."""

  ids: Annotated[list[StrictInt], Field(min_length=1)]
  active: StrictBool


def parse(
  request: dict[str, Any],
  model: type[ModelT],
) -> tuple[ModelT | None, str | None]:
  """Parse and validate a JSON request body with a Pydantic model."""
  try:
    return model.model_validate(request), None
  except ValidationError as error:
    return None, _validation_error_message(error)


def _validation_error_message(error: ValidationError) -> str:
  """Return a short human-readable message for a Pydantic error."""
  first_error = error.errors()[0]
  field = ".".join(str(item) for item in first_error["loc"])
  message = str(first_error["msg"])
  if not field:
    return message
  return f"Invalid {field}: {message}"
