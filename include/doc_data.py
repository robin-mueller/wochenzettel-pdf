import warnings
import holidays
import pendulum
import pandas as pd

from dataclasses import dataclass
from typing import List
from pathlib import Path
from pdfrw import PdfReader, PdfDict, PdfWriter, PdfObject

TEMPLATE_PATH = list(Path.cwd().rglob('TUD_HiWi_hours_doc_template.pdf'))[0]
DATE_FORMAT = "DD.MM.YYYY"
TIME_FORMAT = "HH:mm"


@dataclass(frozen=True)
class DocData:
    forename: str
    surname: str
    institute: str
    birthdate: pendulum.Date
    doc_from: pendulum.Date
    doc_until: pendulum.Date
    monthly_hours: float
    pattern: List[tuple[pendulum.Time, pendulum.Time]]
    output_dir: Path
    file_prefix: str
    
    def _table_rows(self, week_start_date: pendulum.Date, pattern: List[tuple[pendulum.Time, pendulum.Time]]) -> pd.DataFrame:
        row_date = week_start_date
        table_rows = pd.DataFrame()
        for index, ele in enumerate(pattern):
            
            while row_date in holidays.Germany(prov='HE'):
                row_date = row_date.add(days=1)
            
            if any((
                    row_date.day_of_week in [pendulum.SATURDAY, pendulum.SUNDAY],
                    row_date > self.doc_until
            )):
                break
            
            pattern_from, pattern_until = ele
            pattern_diff = pattern_until - pattern_from
            table_rows = pd.concat([
                table_rows,
                pd.DataFrame({
                    'Datum': row_date.format(DATE_FORMAT),
                    'Beginn': pattern_from.format(TIME_FORMAT),
                    'Ende': pattern_until.format(TIME_FORMAT),
                    'Stunden': round(pattern_diff.total_hours(), 2)
                }, index=pd.MultiIndex.from_tuples([(row_date.month, row_date.week_of_year, index)]))
            ])
            row_date = row_date.add(days=1)
        
        table_rows.index.set_names(['month_num', 'week_num', 'entry_index'], inplace=True)
        return table_rows
    
    def _fit_to_monthly_hours(self, current_month_df: pd.DataFrame):
        assert len(current_month_df.index.get_level_values('month_num').unique()) == 1, "Variable current_month_df does not contain only one single month!"
        month_df = current_month_df.copy()
        
        def get_current_hours_diff():
            return month_df.Stunden.sum() - self.monthly_hours
        
        hours_diff = get_current_hours_diff()
        
        while hours_diff > 0:  # Sum of pattern hours is greater than monthly hours
            last_entry_diff = month_df.iloc[-1].Stunden - hours_diff
            if last_entry_diff > 0:  # hours diff can be resolved by subtracting from last entry
                # Change values
                start_time: pendulum.Time = pendulum.from_format(month_df.iloc[-1].Beginn, TIME_FORMAT).time()  # noqa
                end_time = start_time.add(hours=last_entry_diff)
                month_df.loc[month_df.index[-1], 'Ende'] = end_time.format(TIME_FORMAT)
                month_df.loc[month_df.index[-1], 'Stunden'] = round((end_time - start_time).total_hours(), 2)
            else:
                # Drop values
                month_df.drop(index=month_df.index[-1], inplace=True)
            hours_diff = get_current_hours_diff()
        
        reverse_iterator = 0
        while hours_diff < 0:  # Sum of pattern hours is smaller than monthly hours
            start_time = pendulum.time(8)
            
            try:
                # Append rows
                add_day: pendulum.Date = pendulum.from_format(month_df.iloc[-1].Datum, DATE_FORMAT).date().add(days=1)  # noqa
                add_entry_diff = min([abs(hours_diff), 8])  # 8 hours of work per day at a maximum
                # noqa
                if add_day.month == current_month_df.index[0][0]:  # add_day must be within the current month
                    add_dict = self._table_rows(add_day, [(start_time, start_time.add(hours=add_entry_diff))]).to_dict('list')
                    month_df = pd.concat([
                        month_df,
                        pd.DataFrame(
                            add_dict,
                            index=pd.MultiIndex.from_tuples([(month_df.index[-1][0], month_df.index[-1][1], month_df.index[-1][2] + 1)], names=month_df.index.names))
                    ])
                else:
                    raise ValueError
            except ValueError:  # No more rows can be added
                # Extend working time by iterating reversely and changing rows
                try:
                    reverse_iterator -= 1
                    change_entry_diff = min([month_df.iloc[reverse_iterator].Stunden + abs(hours_diff), 8])
                    
                    month_df.iloc[reverse_iterator] = self._table_rows(
                        pendulum.from_format(month_df.iloc[reverse_iterator].Datum, DATE_FORMAT).date(),  # noqa
                        [(start_time, start_time.add(hours=change_entry_diff))]
                    ).squeeze()
                except IndexError:
                    # Drop data of current month if algorithm can't fit to monthly hours
                    warnings.warn(RuntimeWarning(f"Can't fit {pendulum.from_format(month_df.iloc[0].Datum, DATE_FORMAT).format('MMMM')} to specified monthly hours of {self.monthly_hours}!"
                                                 f"\nThere are probably insufficient workdays between "
                                                 f"{pendulum.from_format(month_df.iloc[0].Datum, DATE_FORMAT).to_formatted_date_string()} and "
                                                 f"{pendulum.from_format(month_df.iloc[-1].Datum, DATE_FORMAT).to_formatted_date_string()}."
                                                 f"\nDropping table entries associated with {pendulum.from_format(month_df.iloc[0].Datum, DATE_FORMAT).format('MMMM')}.\n"))
                    return pd.DataFrame()
            
            hours_diff = get_current_hours_diff()
        
        return month_df
    
    @staticmethod
    def _fill_pdf_forms(pdf_template: PdfReader, data: dict):
        annotations = pdf_template.pages[0]['/Annots']
        for annotation in annotations:
            if annotation['/Subtype'] == '/Widget' and annotation['/T']:
                key = annotation['/T'][1:-1]
                if 'Leer' not in key:
                    try:
                        annotation.update(
                            PdfDict(V=data[key])
                        )
                    except KeyError as key_error:
                        # Don't raise an error if the key of rows does not exist, because they should be left empty
                        if 'Row' not in key:
                            raise key_error
                    else:
                        annotation.update(PdfDict(AP=''))
    
    def write_files(self):
        doc_weeks_start = [self.doc_from] + [self.doc_from.add(weeks=num).start_of('week') for num in range(1, (self.doc_until - self.doc_from).in_weeks() + 1)]
        
        # Prepare table entries
        doc_table_df = pd.concat([self._table_rows(week_start_day, self.pattern) for week_start_day in doc_weeks_start])
        
        for month_num, month_df in doc_table_df.groupby(level='month_num'):
            doc_table_df.drop(month_num, level='month_num', inplace=True)
            doc_table_df = pd.concat([
                doc_table_df,
                self._fit_to_monthly_hours(month_df)
            ])
            
        # Save month to files
        for week_start_day in doc_weeks_start:
            data = {
                'Institut': self.institute,
                'Name, Vorname': f"{self.surname}, {self.forename}",
                'Geburtsdatum': self.birthdate.format(DATE_FORMAT),
                'Bearbeitungsdatum': pendulum.today().format(DATE_FORMAT),
                'vom': week_start_day.format(DATE_FORMAT),
                'bis': week_start_day.end_of('week').subtract(days=2).format(DATE_FORMAT),
            }
            
            # Add table entries if necessary
            try:
                week_df = doc_table_df.xs(week_start_day.week_of_year, level='week_num')
            except KeyError:
                pass
            else:
                data.update({
                    f"{key}Row{index}": value
                    for index, d in enumerate(week_df.to_dict('records'))
                    for key, value in d.items()
                })
            
            pdf_template = PdfReader(TEMPLATE_PATH)
            
            # Iterate over all fields and fill with data
            self._fill_pdf_forms(pdf_template, data)
            
            # Save to file
            pdf_template.Root.AcroForm.update(PdfDict(NeedAppearances=PdfObject("true")))
            PdfWriter().write(self.output_dir / f"{self.file_prefix}_Week{week_start_day.week_of_year}_{week_start_day.format('YYYY')}.pdf", pdf_template)


# Debugging
def main():
    DocData(
        "Max", "Mustermann", "TUDa", pendulum.Date(1995, 4, 10), pendulum.Date(2022, 2, 1), pendulum.Date(2022, 3, 4),
        30, [(pendulum.Time(8), pendulum.Time(14)),
             (pendulum.Time(9), pendulum.Time(12)),
             (pendulum.Time(8), pendulum.Time(10)),
             (pendulum.Time(8), pendulum.Time(16))],
        Path.cwd(), 'test'
    ).write_files()


if __name__ == '__main__':
    main()
