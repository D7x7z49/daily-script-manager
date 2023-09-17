from typing import Callable
from functools import wraps


def validate_bool(func):
    """
    Decorator to validate the return value of a function is a boolean.

    Args:
        func (Callable): The function to be decorated.

    Raises:
        TypeError: If the return value of the function is not a boolean.
    
    Returns:
        Callable: The decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if not isinstance(result, bool):
            raise TypeError(f"{func.__name__} must return a boolean value.")
        return result
    return wrapper


def read_lines(file_path: str, match_callback: Callable[[str], bool] = lambda line: True):
    """
    Read lines from a file and return a list of lines that match the callback function.

    Args:
        file_path (str): The path of the file to read.
        match_callback (Callable[[str], bool], optional): The callback function to match lines. Defaults to lambda line: True.

    Returns:
        list: A list of lines that match the callback function.
    """

    try:
        with open(file_path, 'r') as f:
            return [
                line[:-1] if '\n' in line else line 
                for line in f
                if match_callback(line)
            ]

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None

if "__main__" == __name__:

    TEST_FILE_PATH = "test\\test.txt"

    # Test validate_bool decorator
    import re

    @validate_bool
    def is_domain_name(input_str):
        domain_pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        return re.match(domain_pattern, input_str) is not None

    
    def test_func(line: str) -> bool:
        return False

    # Test read_lines function
    print(read_lines(TEST_FILE_PATH))
    print(read_lines(TEST_FILE_PATH, test_func))
    print(read_lines(TEST_FILE_PATH, is_domain_name))
    print(read_lines(TEST_FILE_PATH, lambda line: "hello" in line))