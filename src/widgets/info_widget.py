from PyQt5 import QtWidgets
from PyQt5 import QtCore
import datetime


class InfoWidget(QtWidgets.QWidget):
    info_changed = QtCore.pyqtSignal(tuple)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.layout = QtWidgets.QGridLayout(self)

        h_align = QtCore.Qt.AlignmentFlag.AlignRight
        v_align = QtCore.Qt.AlignmentFlag.AlignTop

        self.executor_label = QtWidgets.QLabel("审查人员：")
        self.layout.addWidget(self.executor_label, 0, 0, alignment=h_align)

        self.executor_edit = QtWidgets.QLineEdit()
        self.layout.addWidget(self.executor_edit, 0, 1)

        self.workstation_label = QtWidgets.QLabel("工位：")
        self.layout.addWidget(self.workstation_label, 1, 0, alignment=h_align|v_align)

        self.workstation_edit = QtWidgets.QLineEdit()
        self.layout.addWidget(self.workstation_edit, 1, 1)

        self.time_label = QtWidgets.QLabel("时间：")
        self.layout.addWidget(self.time_label, 2, 0, alignment=h_align|v_align)

        date_initial = datetime.date.today()
        dt_initial = datetime.datetime(
            date_initial.year,
            date_initial.month,
            date_initial.day,
            hour=8,
            minute=30,
            second=30
        )

        self.datetime_edit = QtWidgets.QDateTimeEdit(dt_initial)
        self.datetime_edit.setDisplayFormat("yyyy/MM/dd hh:mm:ss")
        self.layout.addWidget(self.datetime_edit, 2, 1)

        self.memo_label = QtWidgets.QLabel("备注：")
        self.layout.addWidget(self.memo_label, 3, 0, alignment=h_align|v_align)

        self.memo_edit = QtWidgets.QTextEdit()
        self.layout.addWidget(self.memo_edit, 3, 1)

        self.executor_edit.editingFinished.connect(self.on_info_changed)
        self.workstation_edit.editingFinished.connect(self.on_info_changed)
        self.datetime_edit.editingFinished.connect(self.on_info_changed)
        self.memo_edit.textChanged.connect(self.on_info_changed)

        # lineEditStyle = '''
        #     QLineEdit {
        #         border-style: solid;
        #         border-top-width: 0px;
        #         border-right-width: 0px;
        #         border-left-width: 0px;
        #         border-bottom-width: 1px;
        #         border-color: #FFFFFF;
        #     },
        #     QLineEdit:!enabled {
        #         border-color: #FFFFFF;
        #     }
        # '''
        # self.executor_edit.setStyleSheet(lineEditStyle)
        # self.workstation_edit.setStyleSheet(lineEditStyle)

        # datetimeEditStyle = '''
        #     QDateTimeEdit {
        #         border-style: solid;
        #         border-top-width: 0px;
        #         border-right-width: 0px;
        #         border-left-width: 0px;
        #         border-bottom-width: 1px;
        #     }
        # '''
        # self.datetime_edit.setStyleSheet(datetimeEditStyle)
        

    @QtCore.pyqtSlot()
    def on_info_changed(self) -> None:
        self.info_changed.emit(self.details())

    def update_details(self, details) -> None:
        if details is not None:
            executor, workstation, date_time, memo = details
            self.executor_edit.setText(executor)
            self.workstation_edit.setText(workstation)
            self.datetime_edit.setDateTime(date_time)
            self.memo_edit.setText(memo)
        else:
            self.workstation_edit.clear()

            date_initial = datetime.date.today()
            dt_initial = datetime.datetime(
                date_initial.year,
                date_initial.month,
                date_initial.day,
                hour=8,
                minute=30,
                second=30
            )

            self.datetime_edit.setDateTime(dt_initial)
            self.memo_edit.clear()

    def details(self):
        executor = self.executor_edit.text()
        workstation = self.workstation_edit.text()
        date_time = self.datetime_edit.dateTime().toPyDateTime()
        memo = self.memo_edit.toPlainText()

        return executor, workstation, date_time, memo
