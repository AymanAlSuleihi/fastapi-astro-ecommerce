from src.exceptions import NotFoundException


class ImageNotFound(NotFoundException):
    def __init__(self):
        super().__init__(detail="Image not found")
