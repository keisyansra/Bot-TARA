import pandas as pd


def read_table(file_path: str) -> pd.DataFrame:
    """
    Baca file .xlsx/.xls atau .csv.
    Semua kolom dibaca sebagai string sesuai desain Bronze.
    """

    lower = file_path.lower()

    if lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(file_path, dtype=str)

    elif lower.endswith(".csv"):
        return pd.read_csv(file_path, dtype=str)

    else:
        raise ValueError(
            f"Format file nggak dikenali: {file_path} "
            "(harus .xlsx, .xls, atau .csv)"
        )