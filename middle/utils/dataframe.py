import pandas as pd


def convert_date_columns(df: pd.DataFrame,
                         date_pattern=r'^\d{2}/\d{2}/\d{4}$'
                         ) -> pd.DataFrame:
    """
    Identifica e converte colunas com formato de data DD/MM/YYYY
    para string no formato YYYY-MM-DD.

    Args:
        df (pd.DataFrame): DataFrame a ser processado
        date_pattern (pd.DataFrame): DataFrame a ser processado

    Returns:
        pd.DataFrame: DataFrame com colunas de data convertidas
    """

    for col in df.columns:
        if df[col].dtype == 'object':
            non_null_values = df[col].dropna().astype(str)
            if len(non_null_values) > 0:
                matches = non_null_values.str.match(date_pattern)
                if matches.sum() / len(non_null_values) >= 0.5:
                    try:
                        dt_series = pd.to_datetime(df[col], format='%d/%m/%Y',
                                                   errors='coerce')
                        df[col] = dt_series.dt.strftime('%Y-%m-%d')
                        print(f"Coluna '{col}' convertida "
                              "para string YYYY-MM-DD")
                    except Exception as e:
                        print(f"Erro ao converter coluna '{col}': {e}")
    return df