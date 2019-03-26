import functools
from dataclasses import Field, MISSING, _FIELD


def with_label(label: str = None):
    def first_wrapper(func):
        @functools.wraps(func)
        def second_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            label_field = Field(
                default=MISSING, default_factory=MISSING, init=False, repr=True, hash=None, compare=False, metadata=None
            )
            label_field.name = "label"
            label_field.type = str
            label_field._field_type = _FIELD
            result.__dataclass_fields__["label"] = label_field
            result.label = label if label is not None else result.__class__.__name__.lower()
            return result

        return second_wrapper

    return first_wrapper
