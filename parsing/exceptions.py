class BaseProjectException(Exception):
    pass


# Исключения, связанные с загрузкой файлов
class FileNotDownloaded(BaseProjectException):
    pass


class UnsupportedFileFormat(BaseProjectException):
    pass

