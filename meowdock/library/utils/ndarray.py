from typing import Generic, TypeVar, Any, get_args, Iterator
import numpy as np
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


E = TypeVar("E", bound=np.generic)

class NDArray(Generic[E]):
    '''A wrapper class for numpy array. Implement iterator-related methods only. Binary operators like +-*/ are skipped.
    '''
    def __init__(self, arr: np.ndarray):
        self.arr = arr

    def __repr__(self) -> str:
        return f"{type(self).__name__}(arr={self.arr})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Get generic type from `source_type`
        if hasattr(source_type, "__origin__") and source_type.__origin__ is not None:
            type_args = get_args(source_type)
            if type_args:
                dtype = type_args[0]
            else:
                dtype = np.float64
        else:
            dtype = np.float64

        def validate(values: list[float], _info: core_schema.ValidationInfo) -> "NDArray[E]":
            if isinstance(values, NDArray):
                return values
            arr = np.array(values, dtype=dtype)
            return cls(arr)

        def serialize(v: NDArray[E]):
            return v.arr.tolist()

        return core_schema.with_info_after_validator_function(
            validate,
            core_schema.any_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize, when_used="always"
            )
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: core_schema.CoreSchema,
        handler: GetCoreSchemaHandler
    ):
        return {
            "type": "array",
            "items": {"type": "number"}
        }

    def __getitem__(self, index: int) -> E:
        return self.arr[index]
    
    def __setitem__(self, index: int, value: E) -> None:
        self.arr[index] = value

    def __len__(self) -> int:
        return len(self.arr)
    
    def __iter__(self) -> Iterator[E]:
        return iter(self.arr)
    
    def __contains__(self, value: E) -> bool:
        return value in self.arr


if __name__ == "__main__":
    from pydantic import BaseModel

    class ExampleModel(BaseModel):
        floats: NDArray[np.float64]
        bools: NDArray[np.bool_]
        ints: NDArray[np.int64]

    data = {
        "floats": [1.1, 2.2, 3.3],
        "bools": [True, False, True],
        "ints": [123,456,-789]
    }

    print("\nJSON Schema:")
    print(ExampleModel.model_json_schema())    
    model = ExampleModel(**data)
    print(type(model.floats.arr)) 
    print(model.floats.arr) 
    print(type(model.bools.arr)) 
    print(model.bools.arr)
    print(type(model.ints.arr)) 
    print(model.ints.arr)

    print(model.model_dump())
