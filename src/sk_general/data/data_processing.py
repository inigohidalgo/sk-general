from typing import Tuple, Union, Iterable, Any, Dict
from typing import overload, Optional, Literal, List
from dataclasses import dataclass

import pandas as pd
import numpy as np
import logging


log = logging.getLogger(__name__)


def _is_true(series: pd.Series, true_key: Any = "Y", false_key: Optional[Any] = None) -> pd.Series:
    """
    Converts a Series of elements supposed to indicate a boolean to a boolean series.

    :param series: Series of bool-like elements
    :param true_key: element to == True
    :param false_key: Optional: element to == for False

    """
    conditions: List[Union[pd.Series, bool]] = [series == true_key]
    choices = [True, False]
    if false_key is not None:
        conditions.append(series == false_key)
    else:
        conditions.append(True)
    true_values = np.select(conditions, choices, default=np.nan)
    true_series = pd.Series(true_values, index=series.index, name=series.name).astype(bool)

    return true_series


def get_index_pattern_mask(
    df: Union[pd.DataFrame, pd.Series],
    pattern: str,
    axis: Union[str, int] = 0,
    regex: bool = True,
    **contains_kwargs: Dict[str, Any],
) -> np.ndarray:
    """
    Returns a boolean mask of the axis that matches the pattern.

    :param df: DataFrame or Series to filter
    :param pattern: Pattern to match
    :param axis: Axis to filter on
        * 0/"index"
        * 1/"columns"
        * 2, 3, 4... theoretically higher axis orders returned by df.axes. Added for extensibility.

    :param regex: whether to use regex or standard substring contains
    :return: Boolean mask
    """
    if isinstance(axis, str):
        if axis == "columns":
            axis = 1
        elif axis == "index":
            axis = 0
        else:
            raise ValueError("If passed as a str, axis must be one of 'columns' or 'index'")
        log.debug(f"Converted str-type axis to {axis}")
    axes = df.axes
    if len(axes) >= axis:
        return df.axes[axis].str.contains(pattern, regex=regex, **contains_kwargs)
    else:
        raise ValueError(f"Axis {axis} is not in the dataframe")


def extract_target_from_df(
    df: pd.DataFrame, target_name: Optional[str] = None, return_Xy: Optional[bool] = True
) -> Union[Tuple[pd.DataFrame, pd.Series], pd.Series]:
    if target_name is None:
        target_name = "target"
        log.info(f"No target name specified, assuming default: {target_name}")
    log.info(f"Extracting target {target_name} from df")
    target_series = df[target_name]
    if return_Xy:
        log.debug("Returning df and target as (X, y)")
        return df.drop(columns=target_name), target_series
    else:
        log.debug("Returning target variable as Series")
        return df[target_name]


def iter_to_dict(iterable: Iterable[Any], keys: Optional[Iterable[Any]]=None, index_as_keys:bool=True, **conversion_kwargs: Dict[str, Any]) -> Dict[Any, Any]:
    """
    Converts an iterable of values to a dictionary.
    """
    if not keys:
        log.info("No keys specified")
        if index_as_keys:
            log.debug("Taking index position as keys")
            keys = range(len(iterable))
        else:
            log.debug("Taking keys from first element of iterable")
            keys = iterable[0]
            iterable = iterable[1:]
    return dict(zip(keys, iterable))

def dict_to_iter(dictionary: Dict[Any, Any], prepend_keys:bool = False, **conversion_kwargs: Dict[str, Any]) -> Iterable[Any]:
    """
    Converts a dictionary of values to an iterable.
    """
    values = list(dictionary.values())
    if prepend_keys:
        keys = tuple(dictionary.keys())
        values.insert(0, keys)
    return values

from typing import Callable

from dataclasses import field


def get_base_converters():

    converters = {
        ("iter", "dict"): iter_to_dict,
        ("dict", "iter"): dict_to_iter,
    }

    return converters

def get_base_verifiers():

    verifiers = {
        "iter": lambda data: isinstance(data, Iterable),
        "dict": lambda data: isinstance(data, dict),
    }
    return verifiers

@dataclass
class DataConversionDispatch:
    converters: Dict[Tuple[str, str], Callable] = field(default_factory=get_base_converters)
    transformers: Iterable[Callable] = field(default_factory=list)
    verifiers: Dict[str, Callable[[Any], bool]] = field(default_factory=get_base_verifiers)
    

@dataclass
class DataStatus:
    input_type: str
    output_type: str
    processing_type: str
    current_type: str


class DataHandler:

    operations = DataConversionDispatch()

    def __init__(
        self,
        input_type: Optional[str] = None,
        output_type: Optional[str] = None,
        transformation_type: Optional[str] = None,
        converters: Optional[Dict[Tuple[str, str], Callable]] = None,
        verifiers: Optional[Dict[str, Callable[[Any], bool]]] = None,
        transformers: Optional[Iterable[Callable]] = None
    ) -> None:
        self.data_status = DataStatus(input_type, output_type, transformation_type, input_type)
        self.add_operations(converters=converters, verifiers=verifiers, transformers=transformers)


    def convert_data(self, data, input_type, output_type, **conversion_kwargs):
        if input_type == output_type:
            pass
        conversion_keys = (input_type, output_type)
        if all(conversion_keys): # if either input or output type is None, we skip conversion
            return self.operations.converters[conversion_keys](data, **conversion_kwargs)
        else:
            return data

    def add_operations(self, **new_operations):
        if new_operations.get("converters"):
            self.operations.converters.update(new_operations["converters"])
        
        if new_operations.get("verifiers"):
            self.operations.verifiers.update(new_operations["verifiers"])

        if new_operations.get("transformers"):
            if self.operations.transformers is None:
                self.operations.transformers = new_operations["transformers"]
            else:
                self.operations.transformers.extend(new_operations["transformers"])

    def receive_data(self, data) -> None:
        if self.verify_input_type(data):
            data = self.convert_data(data, self.data_status.input_type, self.data_status.transformation_type)
            self.data = data
            self.data_status.current_type = self.data_status.transformation_type
        else:
            raise TypeError(f"Incorrect input type: {type(data)}, ")

    def verify_input_type(self, data: Any, default: bool = False) -> bool:
        if self.data_status.input_type:
            return self.operations.verifiers[self.input_type](data)
        else:
            choice = 'correct' if default else 'wrong'
            log.debug(f"No input checking, assuming {choice} input type")
            return default

    def emit_data(self, **emit_kwargs) -> None:
        return self.convert_data(self.data, self.data_status.current_type, self.data_status.output_type, **emit_kwargs)

    def transform_data(self) -> None:
        if self.operations.transformers:
            for transformer in self.operations.transformers:
                self.data = transformer(self.data)
            self.data_status.current_type = self.data_status.transformation_type

    def __call__(self, data: Any, **kwargs):
        self.receive_data(data, **kwargs.get("receive_kwargs"))
        self.transform_data(**kwargs.get("transform_kwargs"))
        return self.emit_data(**kwargs.get("emit_kwargs"))

