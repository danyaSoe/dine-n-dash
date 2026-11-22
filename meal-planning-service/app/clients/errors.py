class DependencyRequestError(Exception):
    def __init__(self, service_name: str, message: str) -> None:
        self.service_name = service_name
        super().__init__(f"{service_name} dependency error: {message}")


class DependencyNotFoundError(DependencyRequestError):
    pass


class RouteUnavailableError(Exception):
    pass
