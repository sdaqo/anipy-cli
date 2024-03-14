
class BaseAnime(ABC):
    @abstractmethod
    def __init__(self, provider: BaseProvider):
        pass

    @abstractmethod
    def get_episodes(self):
        pass

    @abstractmethod
    def get_video(self, episode: int)
