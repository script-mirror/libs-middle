import pandas as pd


class DecompParams:
    def __init__(
        self,
        dadger_path: str = None,
        output_path: str = None,
        id_estudo: str = None,
        case: str = None,
        load_level_path: str = None,
        load_level_data: pd.DataFrame = None,
        pq_load_level: pd.DataFrame = None,
    ):
        self.dadger_path = dadger_path
        self.output_path = output_path
        self.id_estudo = id_estudo
        self.case = case
        self.load_level_path = load_level_path
        self.load_level_data = load_level_data
        self.pq_load_level = pq_load_level

    def to_dict(self):
        return self.__dict__
