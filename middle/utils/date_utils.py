import datetime
from typing import List, Union

def get_last_saturday(date: datetime.date) -> datetime.date:
    if not isinstance(date, datetime.date):
        raise TypeError("date must be a datetime.date object")
    if date.weekday() != 5:
        if date.weekday() < 5:
            date = date - datetime.timedelta(days=(date.weekday()+2))
        else:
            date = date - datetime.timedelta(days=1)
    return date

def get_last_friday(date: datetime.date) -> datetime.date:
    if not isinstance(date, datetime.date):
        raise TypeError("date must be a datetime.date object")
    if date.weekday() != 4:
        if date.weekday() < 4:
            date = date - datetime.timedelta(days=(date.weekday()+3))
        else:
            date = date - datetime.timedelta(days=(date.weekday()-4))
    return date

def get_last_thursday(date: datetime.date) -> datetime.date:
    if not isinstance(date, datetime.date):
        raise TypeError("date must be a datetime.date object")
    if date.weekday() != 3:
        if date.weekday() < 3:
            date = date - datetime.timedelta(days=(date.weekday()+4))
        else:
            date = date - datetime.timedelta(days=(date.weekday()-3))
    return date

def diff_week(date1: datetime.date, date2: datetime.date) -> float:
    if not (isinstance(date1, datetime.date) and isinstance(date2, datetime.date)):
        raise TypeError("Both inputs must be datetime.date objects")
    if date1 > date2:
        return (date1 - date2).days / 7.0
    return (date2 - date1).days / 7.0

def count_elec_week(date1: datetime.date, date2: datetime.date) -> float:
    return diff_week(date1, date2)

def get_last_round(date: datetime.date) -> datetime.date:
    return get_last_thursday(date)

def get_current_revision(first_day_of_month: datetime.date, date: datetime.date) -> float:
    return diff_week(first_day_of_month, get_last_saturday(date))

def get_week_weights(first_day_of_month: datetime.date) -> List[int]:
    if not isinstance(first_day_of_month, datetime.date):
        raise TypeError("first_day_of_month must be a datetime.date object")
    if first_day_of_month.weekday() != 5:
        raise ValueError("first_day_of_month must be a Saturday")
    weights = []
    weights.append((first_day_of_month + datetime.timedelta(days=6)).day)
    month = (first_day_of_month + datetime.timedelta(days=6)).month
    j = 1
    while (first_day_of_month + datetime.timedelta(days=7*j)).month == month:
        weights.append(7)
        j += 1
    weights.pop(-1)
    weights.append(8 - (first_day_of_month + datetime.timedelta(days=7*j)).day)
    while len(weights) < 6:
        weights.append(0)
    return weights

class SemanaOperativa:
    def __init__(self, date: Union[datetime.date, datetime.datetime]):
        if isinstance(date, datetime.datetime):
            date = date.date()
        elif not isinstance(date, datetime.date):
            raise TypeError("date must be a datetime.date or datetime.datetime object")
        if date.weekday() != 5:
            raise ValueError("Input date must be a Saturday")
        self.date = date
        self.first_day_of_month = get_last_saturday(datetime.date(date.year, date.month, 1))
        if date > self.first_day_of_month:
            date_aux = date + datetime.timedelta(days=6)
            self.first_day_of_year = get_last_saturday(datetime.date(date_aux.year, 1, 1))
            self.last_day_of_year = get_last_friday(datetime.date(date_aux.year, 12, 31))
            self.first_day_of_month = get_last_saturday(datetime.date(date_aux.year, date_aux.month, 1))
        else:
            self.first_day_of_year = get_last_saturday(datetime.date(date.year, 1, 1))
            self.last_day_of_year = get_last_friday(datetime.date(date.year, 12, 31))
        self.current_revision = get_current_revision(self.first_day_of_month, date)
        self.week_start = self.first_day_of_month + datetime.timedelta(days=7 * self.current_revision)
        self.num_weeks = count_elec_week(self.first_day_of_year, get_last_saturday(date)) + 1
        self.num_weeks_first_day_of_month = count_elec_week(self.first_day_of_year, self.first_day_of_month) + 1
        self.num_weeks_in_year = count_elec_week(self.first_day_of_year, self.last_day_of_year + datetime.timedelta(days=1))
        self.ref_month = (self.first_day_of_month + datetime.timedelta(days=6)).month
        self.ref_year = self.last_day_of_year.year

    def get_week_weights(self) -> List[int]:
        return get_week_weights(self.first_day_of_month)

    def __str__(self) -> str:
        return (
            f"first_day_of_year: {self.first_day_of_year}\n"
            f"last_day_of_year: {self.last_day_of_year}\n"
            f"first_day_of_month: {self.first_day_of_month}\n"
            f"week_start: {self.week_start}\n"
            f"current_revision: {self.current_revision}\n"
            f"num_weeks: {self.num_weeks}\n"
            f"num_weeks_in_year: {self.num_weeks_in_year}\n"
            f"ref_month: {self.ref_month}\n"
            f"num_weeks_first_day_of_month: {self.num_weeks_first_day_of_month}"
        )

if __name__ == "__main__":
    ano_operacional = SemanaOperativa(datetime.date(2019, 12, 21))
    print("primeiroDiaAno:", ano_operacional.first_day_of_year)
    print("ultimoDiaAno:", ano_operacional.last_day_of_year)
    print("primeiroDiaMes:", ano_operacional.first_day_of_month)
    print("atualRevisao:", ano_operacional.current_revision)
    print("numSemanas:", ano_operacional.num_weeks)
    print("numSemanasAno:", ano_operacional.num_weeks_in_year)
    print("mesRefente:", ano_operacional.ref_month)
    print("numSemanasPrimeiroDiaMes:", ano_operacional.num_weeks_first_day_of_month)