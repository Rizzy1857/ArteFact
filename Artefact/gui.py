"""Optional Qt desktop interface for case-oriented ArteFact workflows."""

import json
from pathlib import Path
from typing import Optional


def launch_gui(case_file: Optional[Path] = None) -> int:
    """Launch the dark Qt case, analysis, report, and timeline workspace."""
    try:
        from PySide6.QtCore import QThread, Signal
        from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
            QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton, QTabWidget,
            QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)
    except ImportError as exc:
        raise RuntimeError("The desktop interface requires PySide6: pip install PySide6") from exc

    from Artefact.case import Case
    from Artefact.modules.network import analyze_pcap
    from Artefact.reporting import ReportBuilder

    class AnalysisWorker(QThread):
        completed = Signal(dict)
        failed = Signal(str)

        def __init__(self, capture: Path):
            super().__init__()
            self.capture = capture

        def run(self) -> None:
            try:
                self.completed.emit(analyze_pcap(self.capture))
            except Exception as exc:
                self.failed.emit(str(exc))

    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    window.setWindowTitle("ArteFact Forensics 1.0")
    window.resize(1100, 720)
    window.setStyleSheet(
        "QWidget{background:#111827;color:#e5e7eb} QPushButton{padding:8px;background:#1f2937}"
        "QLineEdit,QTextEdit,QTableWidget{background:#0f172a;border:1px solid #374151}"
    )
    tabs = QTabWidget()
    current = {"case": Case.load(case_file) if case_file else None,
               "path": Path(case_file) if case_file else None, "workers": []}

    case_page = QWidget()
    case_layout = QVBoxLayout(case_page)
    case_label = QLabel()
    case_buttons = QHBoxLayout()
    evidence_view = QTextEdit()
    evidence_view.setReadOnly(True)

    timeline_table = QTableWidget(0, 4)
    timeline_table.setHorizontalHeaderLabels(["Timestamp", "Type", "Source", "Details"])
    timeline_filter = QLineEdit()
    timeline_filter.setPlaceholderText("Filter timeline")

    report_page = QTextEdit()
    report_page.setReadOnly(True)

    def save_case() -> None:
        if current["case"] is None:
            return
        if current["path"] is None:
            filename, _ = QFileDialog.getSaveFileName(window, "Save Case", filter="Cases (*.json)")
            if not filename:
                return
            current["path"] = Path(filename)
        current["case"].save(current["path"])

    def timeline_events():
        case = current["case"]
        if case is None:
            return []
        events = []
        for finding in case.findings:
            details = finding.get("details", {})
            if isinstance(details, dict) and isinstance(details.get("timeline"), list):
                events.extend(details["timeline"])
        return events

    def refresh_timeline(query: str = "") -> None:
        events = timeline_events()
        query = query.lower().strip()
        if query:
            events = [event for event in events if query in json.dumps(event, default=str).lower()]
        timeline_table.setRowCount(len(events))
        for row, event in enumerate(events):
            values = [event.get("timestamp", ""), event.get("event_type", event.get("protocol", "")),
                      event.get("source", ""), event]
            for column, value in enumerate(values):
                timeline_table.setItem(row, column, QTableWidgetItem(
                    json.dumps(value, default=str) if isinstance(value, dict) else str(value)))

    def refresh() -> None:
        case = current["case"]
        case_label.setText("No case loaded" if case is None else f"{case.title} ({case.id})")
        evidence_view.setPlainText("" if case is None else "\n".join(
            f"{item.path}\n  SHA-256: {item.sha256}" for item in case.evidence))
        report_page.setMarkdown("" if case is None else ReportBuilder(case).markdown())
        refresh_timeline(timeline_filter.text())

    def open_case() -> None:
        filename, _ = QFileDialog.getOpenFileName(window, "Open Case", filter="Cases (*.json)")
        if filename:
            try:
                current["case"] = Case.load(Path(filename))
                current["path"] = Path(filename)
                refresh()
            except Exception as exc:
                QMessageBox.critical(window, "Open Case", str(exc))

    def new_case() -> None:
        filename, _ = QFileDialog.getSaveFileName(window, "New Case", filter="Cases (*.json)")
        if filename:
            current["case"] = Case.create(Path(filename).stem)
            current["path"] = Path(filename)
            save_case()
            refresh()

    def add_evidence() -> None:
        if current["case"] is None:
            QMessageBox.warning(window, "ArteFact", "Create or open a case first")
            return
        filename, _ = QFileDialog.getOpenFileName(window, "Add Evidence")
        if filename:
            current["case"].add_evidence(Path(filename), actor="desktop analyst")
            save_case()
            refresh()

    for label, callback in (("New Case", new_case), ("Open Case", open_case),
                            ("Add Evidence", add_evidence), ("Save", save_case)):
        button = QPushButton(label)
        button.clicked.connect(callback)
        case_buttons.addWidget(button)
    case_layout.addWidget(case_label)
    case_layout.addLayout(case_buttons)
    case_layout.addWidget(evidence_view)
    tabs.addTab(case_page, "Case & Evidence")

    analysis_page = QWidget()
    analysis_layout = QVBoxLayout(analysis_page)
    analysis_button = QPushButton("Analyze PCAP")
    analysis_progress = QProgressBar()
    analysis_progress.setVisible(False)
    analysis_output = QTextEdit()
    analysis_output.setReadOnly(True)

    def analyze_capture() -> None:
        filename, _ = QFileDialog.getOpenFileName(window, "Analyze PCAP", filter="Captures (*.pcap)")
        if not filename:
            return
        analysis_progress.setRange(0, 0)
        analysis_progress.setVisible(True)
        worker = AnalysisWorker(Path(filename))
        current["workers"].append(worker)

        def complete(result):
            analysis_progress.setVisible(False)
            analysis_output.setPlainText(json.dumps(result, indent=2, default=str))
            if current["case"] is not None:
                current["case"].add_finding("Network analysis", result)
                save_case()
                refresh()
            current["workers"].remove(worker)

        def failed(message):
            analysis_progress.setVisible(False)
            QMessageBox.critical(window, "Analysis failed", message)
            current["workers"].remove(worker)

        worker.completed.connect(complete)
        worker.failed.connect(failed)
        worker.start()

    analysis_button.clicked.connect(analyze_capture)
    analysis_layout.addWidget(analysis_button)
    analysis_layout.addWidget(analysis_progress)
    analysis_layout.addWidget(analysis_output)
    tabs.addTab(analysis_page, "Live Analysis")

    tabs.addTab(report_page, "Report Preview")
    timeline_page = QWidget()
    timeline_layout = QVBoxLayout(timeline_page)
    timeline_filter.textChanged.connect(refresh_timeline)
    timeline_layout.addWidget(timeline_filter)
    timeline_layout.addWidget(timeline_table)
    tabs.addTab(timeline_page, "Interactive Timeline")

    window.setCentralWidget(tabs)
    refresh()
    window.show()
    return app.exec()


__all__ = ["launch_gui"]
