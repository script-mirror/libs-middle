import pandas as pd


class DecompParams:
    def __init__(self):
        self.dadger_path: str = None
        self.output_path: str = None
        self.id_estudo: str = None
        self.case: str = None
        self.load_level_path: str = None
        self.load_level_data: pd.DataFrame = None
        self.pq_load_level: pd.DataFrame = None

    def to_dict(self):
        return self.__dict__
