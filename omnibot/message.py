class Message:
    """
    An adapter for messages from multiple possible servers.
    """
    def __init__(self, server: 'Server', sender: str, target: str, message: str) -> None:
        self._server = server
        self._sender = sender
        self._target = target
        self._message = message

    @property
    def server(self):
        return self._server

    @property
    def sender(self) -> str:
        return self._sender

    @property
    def target(self) -> str:
        return self._target

    @property
    def message(self) -> str:
        return self._message
