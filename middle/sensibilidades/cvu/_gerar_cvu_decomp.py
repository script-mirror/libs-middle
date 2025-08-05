import os
import glob
import pandas as pd
from typing import List
from ...decomp import (
    cvu_input_generator, retrieve_dadger_metadata,
    DecompParams, process_decomp
)

def atualizar_cvu_dadger_decomp(
    info_cvu,
    paths_to_modify: List[str],
    id_estudo: str
):
    paths_modified = []
    for path_dadger in paths_to_modify:
        
        params = DecompParams(
            dadger_path=path_dadger,
            output_path=os.path.dirname(path_dadger),
            id_estudo=id_estudo,
            case='att-cvu',
        )
        
        metadata = retrieve_dadger_metadata(**params.to_dict())
        weeks = metadata['stages'][-1]
        power_plants_ids = [int(x['id']) for x in metadata['power_plants']]
        if type(info_cvu) is pd.DataFrame:
            info_cvu = info_cvu[
                info_cvu['cd_usina'].isin(power_plants_ids)
            ].drop_duplicates(['cd_usina'], keep='last').to_dict('records')

        cvu_input = cvu_input_generator(
            info_cvu,
            weeks
        )
        process_decomp(params, cvu_input)
        paths_modified.append(path_dadger)
        paths_modified.extend(
            glob.glob(os.path.join(
                os.path.dirname(path_dadger), "**", "*.log"
                ), recursive=True)
        )

    return paths_modified