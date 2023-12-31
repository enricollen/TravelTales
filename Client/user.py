class User:

    COLORS = ["blue", "green", "yellow", "orange", "purple", "brown"]
    COLOR_INDEX = 0

    def __init__(self, username, embedding, path_to_voice_profile) -> None:
        self.username = username
        self.embedding = embedding
        self.path_to_voice_profile = path_to_voice_profile
        self.color = User.COLORS[User.COLOR_INDEX]
        User.COLOR_INDEX = (User.COLOR_INDEX + 1) % len(User.COLORS)

    def get_username(self) -> str:
        return self.username
    
    def get_embedding(self) -> list[float]:
        return self.embedding
    
    def get_path_to_voice_profile(self) -> str:
        return self.path_to_voice_profile
    
    def get_color(self) -> str:
        return self.color