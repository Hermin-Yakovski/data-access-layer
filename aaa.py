from abc import ABC, abstractmethod


class Handler(ABC):
    @abstractmethod
    def fetch(self) -> Dict[str, List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def store(self, data: Dict[str, List[Dict[str, Any]]]):
        pass


class JsonHandler(Handler):
    def fetch(self) -> Dict[str, List[Dict[str, Any]]]:
        pass

    def store(self, data: Dict[str, List[Dict[str, Any]]], inplace: bool = False):
        super().store(data)


class XlsxHandler(Handler):
    def fetch(self, sheet_list: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        pass

    def store(self, data: Dict[str, List[Dict[str, Any]]], inplace: bool = False):
        super().store(data)