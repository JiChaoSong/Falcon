class AbstractBaseEnum:

    def get_string_key_value(self):
        return f'#{self.key} {self.value}'

    def __init__(self, key: int, value: str):
        self.key = key
        self.value = value


class AbstractBaseCodeMessageEnum:

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message