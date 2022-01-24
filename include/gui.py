import pendulum
import traceback
import sys

from typing import List
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import *
from include.doc_data import DocData, DATE_FORMAT, TIME_FORMAT

DEFAULT_OUTPUT_DIR = Path.cwd()
MAIN_WINDOW_PATH = list(Path.cwd().rglob('main_window.ui'))[0]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()  # noqa
        uic.loadUi(MAIN_WINDOW_PATH, self)
        self.setFixedSize(self.size())
        
        # Type hints
        self.forename: QLineEdit = self.forename
        self.surname: QLineEdit = self.surname
        self.institute: QLineEdit = self.institute
        self.birthdate: QDateEdit = self.birthdate
        self.doc_from: QDateEdit = self.doc_from
        self.doc_until: QDateEdit = self.doc_until
        self.example_table: QTableWidget = self.example_table
        self.fit_to_monthly_hours: QCheckBox = self.fit_to_monthly_hours
        self.monthly_hours: QDoubleSpinBox = self.monthly_hours
        self.check_label1: QLabel = self.check_label1
        self.check_label2: QLabel = self.check_label2
        self.select_directory: QPushButton = self.select_directory
        self.directory_label: QLabel = self.directory_label
        self.create_files: QPushButton = self.create_files
        self.file_prefix: QLineEdit = self.file_prefix
        self.file_name_preview: QLabel = self.file_name_preview
        
        self.output_dir = DEFAULT_OUTPUT_DIR
        self.directory_label.setText(self.output_dir.as_posix())
        
        for col in range(self.example_table.columnCount()):
            self.example_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        for row in range(self.example_table.rowCount()):
            self.example_table.verticalHeader().setSectionResizeMode(row, QHeaderView.Stretch)
        
        self.fit_to_monthly_hours.stateChanged.connect(self.on_fit_to_monthly_hours_click)  # noqa
        self.create_files.clicked.connect(self.on_create_files)  # noqa
        self.select_directory.clicked.connect(self.on_select_directory)  # noqa
        self.file_prefix.textChanged.connect(self.on_file_prefix_change)  # noqa
    
    def on_fit_to_monthly_hours_click(self):
        if self.fit_to_monthly_hours.isChecked():
            self.check_label1.setEnabled(True)
            self.check_label2.setEnabled(True)
            self.monthly_hours.setEnabled(True)
        else:
            self.check_label1.setEnabled(False)
            self.check_label2.setEnabled(False)
            self.monthly_hours.setEnabled(False)
    
    # noinspection PyUnresolvedReferences
    def on_create_files(self):
        try:
            kwargs = dict(
                forename=self.forename.text(),
                surname=self.surname.text(),
                institute=self.institute.text(),
                birthdate=pendulum.from_format(self.birthdate.text(), DATE_FORMAT).date(),
                doc_from=pendulum.from_format(self.doc_from.text(), DATE_FORMAT).date(),
                doc_until=pendulum.from_format(self.doc_until.text(), DATE_FORMAT).date(),
                pattern=self.get_pattern(),
                output_dir=self.output_dir,
                file_prefix=self.file_prefix.text()
            )
            
            if any((
                    kwargs['forename'] == '',
                    kwargs['surname'] == '',
                    kwargs['institute'] == ''
            )):
                raise ValueError("Please fill in every field in Personal Information!")
            
            if any((
                    kwargs['doc_from'].day_of_week in [pendulum.SATURDAY, pendulum.SUNDAY],
                    kwargs['doc_until'].day_of_week in [pendulum.SATURDAY, pendulum.SUNDAY],
                    kwargs['doc_until'] <= kwargs['doc_from']
            )):
                raise ValueError(f"You specified an unsupported documentation start and/or end."
                                 f"\n   From {kwargs['doc_from'].format('dddd Do [of] MMM YYYY')}"
                                 f"\n   Until {kwargs['doc_until'].format('dddd Do [of] MMM YYYY')}"
                                 f"\nDocumentation must start and end during workdays and it is necessary that the From Date is smaller than the Until Date!")
            
            kwargs['monthly_hours'] = self.monthly_hours.value() if self.fit_to_monthly_hours.isChecked() \
                else sum([end - start for start, end in kwargs['pattern']], pendulum.Duration()).total_hours() * 4
            
            message = f"Documentation Range:" \
                      f"\n  - From {kwargs['doc_from'].format('dddd Do [of] MMM YYYY')}" \
                      f"\n  - Until {kwargs['doc_until'].format('dddd Do [of] MMM YYYY')}" \
                      f"\n\nIt contains {(kwargs['doc_until'] - kwargs['doc_from']).in_weeks() + 1} weeks." \
                      f"\nThe table entries will match {kwargs['monthly_hours']:.2f} hours a month." \
                      f"\n\nClick OK to create the documentation files inside the specified working directory!"
            answer = QMessageBox.information(self, "Create Documentation Files", message, buttons=QMessageBox.Cancel | QMessageBox.Ok)  # noqa
            
            if answer == QMessageBox.Ok:
                DocData(**kwargs).write_files()
                
        except Exception as e:
            QMessageBox.warning(self, "Wrong Inputs", str(e))  # noqa
            traceback.print_exception(type(e), e, sys.exc_info()[2])
    
    def on_select_directory(self):
        d = QFileDialog.getExistingDirectory(self, "Choose Working Directory", self.output_dir.as_posix())  # noqa
        if d != '':
            self.output_dir = Path(d)
        
        self.directory_label.setText(self.output_dir.as_posix())
    
    def on_file_prefix_change(self):
        self.file_name_preview.setText(self.file_prefix.text() + "_Week<num>_<year>.pdf")
    
    def get_pattern(self) -> List[tuple[pendulum.Time, pendulum.Time]]:
        entries = []
        for row_index in range(self.example_table.rowCount()):
            time_from = self.example_table.item(row_index, 0).text()
            time_until = self.example_table.item(row_index, 1).text()
            if time_from != '' and time_until != '':
                try:
                    entries.append(
                        (
                            pendulum.from_format(self.example_table.item(row_index, 0).text(), TIME_FORMAT).time(),
                            pendulum.from_format(self.example_table.item(row_index, 1).text(), TIME_FORMAT).time()
                        )
                    )
                except ValueError:
                    raise ValueError(f"The format of entries inside the table must be equivalent to {TIME_FORMAT}!")
        if entries:
            return entries  # noqa
        else:
            raise ValueError("Entries inside the table must not be empty!")


if __name__ == "__main__":
    app = QApplication([])
    
    window = MainWindow()
    window.show()
    
    app.exec_()
